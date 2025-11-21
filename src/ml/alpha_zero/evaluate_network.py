from sandbox._3moku.game import State
from sandbox._3moku.models.alpha_zero.pv_mcts import pv_mcts_action
from sandbox._3moku.models.utils.evaluate import evaluate_algorithm_of

from keras.models import load_model
from keras import backend as K
from pathlib import Path
from shutil import copy
from dotenv import load_dotenv
import numpy as np
import os

load_dotenv()
MODEL_DIR_PATH = os.getenv("MODEL_DIR_PATH")


# 1評価あたりのゲーム数
EN_GAME_COUNT = 10
# ボルツマン分布の温度パラメータ
EN_TEMPERATURE = 1.0


# ベストプレイヤーの更新
def update_best_player():
    copy(f"{MODEL_DIR_PATH}/latest.keras", f"{MODEL_DIR_PATH}/best.keras")
    print("Best player updated.")


# ニューラルネットワークの評価
def evaluate_network():
    # モデルの読み込み
    latest_model = load_model(f"{MODEL_DIR_PATH}/latest.keras", compile=False)
    best_model = load_model(f"{MODEL_DIR_PATH}/best.keras", compile=False)

    # pv-mctsの行動選択関数を作成
    latest_player = pv_mcts_action(latest_model, EN_TEMPERATURE)
    best_player = pv_mcts_action(best_model, EN_TEMPERATURE)
    next_action = [latest_player, best_player]

    # アルゴリズム評価
    average_point = evaluate_algorithm_of(
        "BEST", next_action, EP_GAME_COUNT=EN_GAME_COUNT
    )

    # モデルの破棄
    K.clear_session()
    del latest_model
    del best_model

    # ベストプレイヤーの更新判定
    if average_point > 0.5:
        update_best_player()
        return True
    else:
        return False


if __name__ == "__main__":
    # ニューラルネットワークの評価
    evaluate_network()
