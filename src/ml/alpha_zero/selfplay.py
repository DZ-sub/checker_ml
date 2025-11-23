# セルフプレイによる学習データ生成（強化学習）

from src.ml.checker_state import State
from src.ml.alpha_zero.dual_network import (
    DN_OUTPUT_SIZE,
    action_to_index,
)
from src.ml.alpha_zero.pv_mcts import pv_mcts_scores
from src.infrastructure.aws.s3 import upload_bytes_to_s3, load_model_from_s3

from keras.models import load_model
from keras import backend as K
from datetime import datetime
from dotenv import load_dotenv
import numpy as np
import pickle
import os

load_dotenv()
MODEL_DIR_PATH = os.getenv("MODEL_DIR_PATH")
DATA_DIR_PATH = os.getenv("DATA_DIR_PATH")

# セルフプレイを行うゲーム数
SP_GAME_COUNT = 1000
# 行動選択の温度パラメータ
SP_TEMPERATURE = 1.0


# 先手プレイヤーの価値
def first_player_value(ended_state: State):
    """
    3目並べ版と同じロジック:
      先手勝利  -> +1
      先手敗北  -> -1
      引き分け  -> 0
    """
    if ended_state.is_lose():
        if ended_state.is_first_player():
            return -1
        else:
            return 1
    else:
        return 0


# 学習データの保存
def write_data(history):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    # os.makedirs(DATA_DIR_PATH, exist_ok=True)
    # path = f"{DATA_DIR_PATH}/selfplay_{now}.pkl"
    # with open(path, "wb") as f:
    #     pickle.dump(history, f)
    body = pickle.dumps(history)
    upload_bytes_to_s3("data", f"selfplay_{now}.pkl", body)


# 1ゲームの実行
def play(model):
    """
    返す history の1要素は:
      [ state_info, policies, value ]
    とする。
      state_info: [board_copy, turn]
        - board_copy: 6x6 の 2次元配列 (整数: 0,1,2,-1,-2)
        - turn: 1=RED(先手), -1=BLUE(後手)
      policies: 長さ DN_OUTPUT_SIZE (= 1296) のリスト
      value   : 最終的に first_player_value で埋める
    """
    history = []

    # 状態の生成
    state = State()

    # ゲーム終了まで繰り返す
    while True:
        # ゲーム終了時
        if state.is_done():
            break

        # 合法手の確率分布の取得 (legal_actions と同じ順序)
        scores = pv_mcts_scores(state, model, SP_TEMPERATURE)
        legal_actions = state.legal_actions()  # [(fr,fc,tr,tc,captured_list), ...]

        # ポリシーベクトル（全行動空間分 = DN_OUTPUT_SIZE）を0で初期化
        policies = [0.0] * DN_OUTPUT_SIZE

        # 合法手それぞれに対応する index を立てる
        for (fr, fc, tr, tc, captured), policy in zip(legal_actions, scores):
            idx = action_to_index(fr, fc, tr, tc)
            policies[idx] = policy

        # 盤面のコピーを保存（後で State を再構成してもいいし、そのまま平面にしてもいい）
        board_copy = [row[:] for row in state.board]
        turn_copy = state.turn

        # 学習データに [state_info, policies, value(None)] を追加
        history.append([[board_copy, turn_copy], policies, None])

        # 行動の取得
        # np.random.choice(legal_actions, p=...) はエラーになるので、
        # インデックスをサンプリングしてから実際の行動を取る
        action_idx = np.random.choice(len(legal_actions), p=scores)
        action = legal_actions[action_idx]

        # 次の状態の取得
        state = state.next(action)

    # 学習データに価値を追加
    value = first_player_value(state)
    for i in range(len(history)):
        history[i][2] = value
        value = -value  # 手番が交代するごとに価値を反転（先手視点での価値）

    return history


# セルフプレイの実行
def selfplay():
    # 学習データ
    history = []

    # モデルの読み込み
    # model_path = os.path.join(MODEL_DIR_PATH, "best.keras")
    # model = load_model(model_path, compile=False)
    model = load_model_from_s3("saved_models", "best.keras")

    # 複数回のゲームの実行
    for i in range(SP_GAME_COUNT):
        # 1ゲームの実行
        h = play(model)
        history.extend(h)

        # ログ
        print(f"\rSelf Play {i+1}/{SP_GAME_COUNT}", end="")
    print("")

    # 学習データの保存
    write_data(history)

    # モデルの破棄
    K.clear_session()
    del model


if __name__ == "__main__":
    # セルフプレイの実行
    selfplay()

# python -m src.gpt_ml.alpha_zero.selfplay
