from src.gpt_ml.checker_state import State
from src.gpt_ml.alpha_zero.pv_mcts import pv_mcts_action
from src.gpt_ml.evaluate import evaluate_algorithm_of

from keras.models import load_model
from keras import backend as K
from shutil import copy
from dotenv import load_dotenv
import os

load_dotenv()
MODEL_DIR_PATH = os.getenv("MODEL_DIR_PATH")

# 1評価あたりのゲーム数
EN_GAME_COUNT = 10
# ボルツマン分布の温度パラメータ（pv_mcts の探索で使う）
EN_TEMPERATURE = 1.0


# ベストプレイヤーの更新
def update_best_player():
    src = os.path.join(MODEL_DIR_PATH, "latest.keras")
    dst = os.path.join(MODEL_DIR_PATH, "best.keras")
    copy(src, dst)
    print("Best player updated.")


# ニューラルネットワークの評価
def evaluate_network():
    # モデルの読み込み
    latest_model_path = os.path.join(MODEL_DIR_PATH, "latest.keras")
    best_model_path = os.path.join(MODEL_DIR_PATH, "best.keras")

    latest_model = load_model(latest_model_path, compile=False)
    best_model = load_model(best_model_path, compile=False)

    # pv-mcts の行動選択関数を作成
    latest_player = pv_mcts_action(latest_model, EN_TEMPERATURE)
    best_player = pv_mcts_action(best_model, EN_TEMPERATURE)
    next_actions = [latest_player, best_player]

    # アルゴリズム評価（latest vs best）
    average_point = evaluate_algorithm_of(
        "BEST",
        next_actions,
        EP_GAME_COUNT=EN_GAME_COUNT,
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
        print("Best player NOT updated.")
        return False


if __name__ == "__main__":
    # ニューラルネットワークの評価
    evaluate_network()

# python -m src.gpt_ml.alpha_zero.evaluate_network
