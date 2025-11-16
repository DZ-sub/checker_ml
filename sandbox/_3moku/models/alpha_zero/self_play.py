from sandbox._3moku.game import State
from sandbox._3moku.models.alpha_zero.dual_network import DN_OUTPUT_SIZE
from sandbox._3moku.models.alpha_zero.pv_mcts import pv_mcts_scores

from keras.models import load_model
from keras import backend as K
from datetime import datetime
from pathlib import Path
import numpy as np
import pickle
import os

# セルフプレイを行うゲーム数
SP_GAME_COUNT = 500
# 行動選択の温度パラメータ
SP_TEMPERATURE = 1.0

# 先手プレイヤーの価値
def first_player_value(ended_state: State):
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
    os.makedirs("./data/", exist_ok=True)
    path = f"./data/self_play_{now}.pkl"
    with open(path, "wb") as f:
        pickle.dump(history, f)

#　1ゲームの実行
def play(model):
    # 学習データ
    history = []
    # 状態の生成
    state = State()

    # ゲーム終了まで繰り返す
    while True:
        # ゲーム終了時
        if state.is_done():
            break
        # 合法手の確率分布の取得
        scores = pv_mcts_scores(state, model, SP_TEMPERATURE)
        # 学習データにvalueとpolicyを追加
        policies = [0] * DN_OUTPUT_SIZE
        for action, policy in zip(state.legal_actions(), scores):
            policies[action] = policy
        history.append([[state.pieces, state.enemy_pieces], policies, None])
        # 行動の取得
        action = np.random.choice(state.legal_actions(), p=scores)
        # 次の状態の取得
        state = state.next(action)

    # 学習データに価値を追加
    value = first_player_value(state)
    for i in range(len(history)):
        history[i][2] = value
        value = -value  # プレイヤー交代
    return history

# セルフプレイの実行
def self_play(model_path: str):
    # 学習データ
    history = []
    # モデルの読み込み
    model = load_model(model_path, compile=False)
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
    self_play("sandbox/_3moku/saved_models/best.h5")

# python -m sandbox._3moku.models.alpha_zero.self_play