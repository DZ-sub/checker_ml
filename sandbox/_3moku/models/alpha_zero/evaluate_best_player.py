from sandbox._3moku.game import State, random_action
from sandbox._3moku.models.ab import alpha_beta_action
from sandbox._3moku.models.mcts import mcts_action
from sandbox._3moku.models.alpha_zero.pv_mcts import pv_mcts_action
from sandbox._3moku.models.utils.evaluate import evaluate_algorithm_of

from keras.models import load_model
from keras import backend as K
from pathlib import Path
from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()

MODEL_DIR = os.getenv("MODEL_DIR")


# 最良プレイヤーの評価
def evaluate_best_player():
    # 最良モデルの読み込み
    model = load_model(f"{MODEL_DIR}/best_model.keras")

    # pv_mctsの行動選択
    next_pv_mcts_action = pv_mcts_action(model, temperature=0.0)

    # VS ランダム
    next_actions = (next_pv_mcts_action, random_action)
    evaluate_algorithm_of("RANDOM", next_actions)

    # VS アルファベータ法
    next_actions = (next_pv_mcts_action, alpha_beta_action)
    evaluate_algorithm_of("ALPHA_BETA", next_actions)

    # VS MCTS
    next_actions = (next_pv_mcts_action, mcts_action)
    evaluate_algorithm_of("MCTS", next_actions)

    # モデルの破棄
    K.clear_session()
    del model


if __name__ == "__main__":
    evaluate_best_player()

# python -m sandbox._3moku.models.alpha_zero.evaluate_best_player
