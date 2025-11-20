# ポリシー・バリュー付きモンテカルロ木探索（PV-MCTS）
# ★ パスはあなたのchecker用モジュールに合わせて修正すること

from math import sqrt
from pathlib import Path
import os

import numpy as np
from keras.models import load_model
from dotenv import load_dotenv

from src.gpt_ml.checker_state import State
from src.gpt_ml.alpha_zero.dual_network import DN_INPUT_SHAPE, action_to_index
from src.gpt_ml.gameplay import play

# 定数・環境変数
load_dotenv()
MODEL_DIR_PATH = os.getenv("MODEL_DIR_PATH")

# 1推論あたりのシミュレーション回数
PV_EVALUATE_COUNT = 100

# 盤面サイズは DN_INPUT_SHAPE から取得
H, W, C = DN_INPUT_SHAPE
assert H == W, "入力が正方盤面である前提です"
BOARD_SIZE = H


# State -> NN入力テンソル 変換
def state_to_tensor(state: State):
    """
    State(盤面オブジェクト)を、モデルに入力できる (1, 6, 6, 4) テンソルに変換する。
    チャンネル定義:
      0: 手番側の通常駒
      1: 手番側のキング
      2: 相手側の通常駒
      3: 相手側のキング
    """
    planes = np.zeros(DN_INPUT_SHAPE, dtype=np.float32)

    # state.turn を「自分」として正規化（RED=1, BLUE=-1を想定）
    my_color = 1 if state.turn == 1 else -1

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            v = state.board[r][c]
            if v == 0:
                continue
            color = 1 if v > 0 else -1
            is_king = abs(v) == 2

            if color == my_color:
                if not is_king:
                    planes[r, c, 0] = 1  # 自分ノーマル
                else:
                    planes[r, c, 1] = 1  # 自分キング
            else:
                if not is_king:
                    planes[r, c, 2] = 1  # 相手ノーマル
                else:
                    planes[r, c, 3] = 1  # 相手キング

    # バッチ次元を足して (1, H, W, 4)
    return planes[np.newaxis, ...]


# NN 推論
def predict(model, state: State):
    """
    モデルから (policies, value) を取得する。
    policies: 合法手に対応する確率の np.ndarray
    value   : 現局面の状態価値（手番側から見た -1〜1）
    """
    # 入力テンソルに変換
    x = state_to_tensor(state)

    # 推論
    pi_full, v = model.predict(x, batch_size=1, verbose=0)  # pi_full.shape=(1, ACTION_SIZE)

    # 合法手を取得
    legal_actions = state.legal_actions()  # [(fr,fc,tr,tc, captured_list), ...]

    # 各合法手をポリシーベクトル上の index に変換
    indices = [
        action_to_index(fr, fc, tr, tc)
        for (fr, fc, tr, tc, captured) in legal_actions
    ]

    # 合法手に対応するポリシーのみ抽出
    policies = pi_full[0][indices]  # shape=(len(legal_actions),)

    # 合計1に正規化（全部0なら一様分布）
    s = policies.sum()
    if s > 0:
        policies = policies / s
    else:
        policies = np.ones_like(policies) / len(policies)

    # バリュー（手番側から見た価値）
    value = v[0][0]

    return policies, value


def nodes_to_scores(nodes):
    """ノードのリストを試行回数 n のリストに変換"""
    return [c.n for c in nodes]


def argmax(collection: list, key=None):
    """最大値のインデックスを返す（keyは未使用で3目並べに合わせた形だけ残す）"""
    return collection.index(max(collection))


def boltzman(xs, temperature):
    """ボルツマン分布によるスコア変換"""
    xs = [x ** (1 / temperature) for x in xs]
    s = sum(xs)
    return [x / s for x in xs]


# PV-MCTS 本体
def pv_mcts_scores(state: State, model, temperature):
    # ノードの定義
    class Node:
        def __init__(self, state: State, p):
            self.state = state  # ゲームの状態
            self.p = p          # ポリシー（事前確率）
            self.w = 0          # 累計価値
            self.n = 0          # 試行回数
            self.child_nodes = None  # 子ノードのリスト

        # 局面の価値の計算
        def evaluate(self):
            # ゲーム終了時
            if self.state.is_done():
                # 勝敗結果の価値（手番側から見て）
                value = -1 if self.state.is_lose() else 0

                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1
                return value

            # 子ノードが存在しない時（展開）
            if not self.child_nodes:
                # ニューラルネットワークでポリシーとバリューを取得
                policies, value = predict(model, self.state)

                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1

                # ノードの展開
                self.child_nodes = []
                for action, policy in zip(self.state.legal_actions(), policies):
                    next_state = self.state.next(action)
                    self.child_nodes.append(Node(next_state, policy))
                return value

            # 子ノードが存在する時（UCBで次に進む）
            else:
                # アーク評価値が最大の子ノードの評価で価値を取得
                value = -self.next_child_node().evaluate()
                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1
                return value

        # アーク評価値が最大の子ノードの取得
        def next_child_node(self):
            # アーク評価値の計算
            C_PUCT = 1.0
            t = sum(nodes_to_scores(self.child_nodes))
            pucb_values = []
            for child_node in self.child_nodes:
                q = child_node.w / child_node.n if child_node.n else 0
                u = C_PUCT * child_node.p * sqrt(t) / (1 + child_node.n)
                pucb_values.append(q + u)
            # アーク評価値が最大の子ノードを返す
            return self.child_nodes[argmax(pucb_values)]

    # 現在の局面のノード作成
    root_node = Node(state, 0)

    # 複数回の評価を実行
    for _ in range(PV_EVALUATE_COUNT):
        root_node.evaluate()

    # 合法手の確率分布（rootの子ノードの訪問回数に基づく）
    scores = nodes_to_scores(root_node.child_nodes)
    if temperature == 0:  # 最大値のみ1
        action_idx = int(np.argmax(scores))
        scores = [0] * len(scores)
        scores[action_idx] = 1
    else:  # ボルツマン分布によるスコア付け
        scores = boltzman(scores, temperature)

    return scores


# モンテカルロ木探索で行動選択
def pv_mcts_action(model, temperature=0.0):
    def _pv_mcts_action(state: State):
        # 合法手と、そのスコアを取得
        legal_actions = state.legal_actions()
        scores = pv_mcts_scores(state, model, temperature)

        # インデックスを確率付きでサンプリング
        idx = np.random.choice(len(legal_actions), p=scores)

        # 対応する行動（(fr,fc,tr,tc,captured_list)）を返す
        return legal_actions[idx]

    return _pv_mcts_action


# 動作確認
if __name__ == "__main__":
    # モデルの読み込み
    model_path = Path(f"{MODEL_DIR_PATH}/best.keras")
    model = load_model(model_path, compile=False)

    # pv_mctsの行動選択関数を作成
    pv_mcts = pv_mcts_action(model, temperature=1.0)

    # アルゴリズム評価（play は [方策1, 方策2] を受け取る前提）
    play([pv_mcts, pv_mcts])

    # モデルの破棄
    from keras import backend as K
    K.clear_session()
    del model

# python -m src.gpt_ml.alpha_zero.pv_mcts
