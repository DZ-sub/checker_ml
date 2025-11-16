from sandbox._3moku.game import State, random_action
from sandbox._3moku.models.alpha_zero.dual_network import DN_INPUT_SHAPE
from sandbox._3moku.models.utils.gameplay import play

from math import sqrt
from keras.models import load_model
from pathlib import Path
import numpy as np

# 1推論あたりのシミュレーション回数
PV_EVALUATE_COUNT = 50


# 推論
def predict(model, state: State):
    h, w, c = DN_INPUT_SHAPE  # 入力形状（縦, 横, チャンネル）
    x = np.array([state.pieces, state.enemy_pieces])  # 自分の石と相手の石
    x = (
        x.reshape(c, h, w).transpose(1, 2, 0).reshape(1, h, w, c)
    )  # 形状変換（バッチサイズ, 縦, 横, チャンネル）

    # 推論
    y = model.predict(x, batch_size=1)

    # ポリシーとバリューに分割
    # ポリシー（各合法手のスコア）
    policies = y[0][0][list(state.legal_actions())]  # 合法手のみ
    policies /= sum(policies) if sum(policies) else 1  # 合計1の確率分布に正則化
    # バリュー（状態価値）
    value = y[1][0][0]

    return policies, value


# ノードのリストを試行回数のリストに変換
def nodes_to_scores(nodes):
    scores = []
    for c in nodes:
        scores.append(c.n)
    return scores


# 最大値のインデックスを返す
def argmax(collection: list, key=None):
    return collection.index(max(collection))


# ボルツマン分布によるスコア
def boltzman(xs, temperature):
    xs = [x ** (1 / temperature) for x in xs]
    return [x / sum(xs) for x in xs]


# ポリシー・バリュー付きモンテカルロ木探索のスコアの取得
def pv_mcts_scores(state: State, model, temperature):
    # ノードの定義
    class Node:
        def __init__(self, state: State, p):
            self.state = state  # ゲームの状態
            self.p = p  # ポリシー（事前確率）
            self.w = 0  # 累計価値
            self.n = 0  # 試行回数
            self.child_nodes = None  # 子ノードのリスト

        # 局面の価値の計算
        def evaluate(self):
            # ゲーム終了時
            if self.state.is_done():
                # 勝敗結果の価値
                value = -1 if self.state.is_lose() else 0

                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1
                return value

            # 子ノードが存在しない時
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
            # 子ノードが存在する時
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

    # 合法手の確率分布
    scores = nodes_to_scores(root_node.child_nodes)
    if temperature == 0:  # 最大値のみ1
        action = np.argmax(scores)
        scores = [0] * len(scores)
        scores[action] = 1
    else:  # ボルツマン分布によるスコア付け
        scores = boltzman(scores, temperature)
    return scores


# モンテカルロ木探索で行動選択
def pv_mcts_action(model, temperature=0):
    def pv_mcts_action(state: State):
        scores = pv_mcts_scores(state, model, temperature)
        return np.random.choice(state.legal_actions(), p=scores)

    return pv_mcts_action


# 動作確認
if __name__ == "__main__":
    # モデルの読み込み
    model_path = Path("sandbox/_3moku/saved_models/best.h5")
    model = load_model(model_path, compile=False)

    # pv_mctsの行動選択関数を作成
    pv_mcts = pv_mcts_action(model, temperature=1.0)

    # アルゴリズム評価
    play([pv_mcts, pv_mcts])

# python -m sandbox._3moku.models.alpha_zero.pv_mcts
