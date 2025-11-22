# 学習データによるニューラルネットワークの訓練・更新

from src.gpt_ml.alpha_zero.dual_network import DN_INPUT_SHAPE
from src.infrastructure.aws.s3 import (
    upload_model_to_s3,
    load_model_from_s3,
    load_some_pickles_from_s3,
)

from keras.callbacks import LearningRateScheduler, LambdaCallback
from keras.models import load_model
from keras import backend as K
from pathlib import Path
import pickle
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()
MODEL_DIR_PATH = os.getenv("MODEL_DIR_PATH")
DATA_DIR_PATH = os.getenv("DATA_DIR_PATH")

# 学習回数
RN_EPOCHS = 100


# # 学習データの読み込み
# def load_data(max_files: int = 10):
#     paths = sorted(Path(DATA_DIR_PATH).glob("selfplay_*.pkl"))
#     if not paths:
#         raise FileNotFoundError(f"No selfplay_*.pkl found in {DATA_DIR_PATH}")
#     pickle_path = paths[-1]  # 一番新しいファイル
#     with open(pickle_path, "rb") as f:
#         return pickle.load(f)


def encode_board_to_tensor(boards, turns):
    """
    self_play で保存した
      state_info = [board_copy, turn_copy]
    から、(N, H, W, 4) のテンソルを作る。

    チャンネル定義:
      0: 手番側の通常駒
      1: 手番側のキング
      2: 相手側の通常駒
      3: 相手側のキング
    """
    h, w, c = DN_INPUT_SHAPE
    assert c == 4, "DN_INPUT_SHAPE のチャンネル数は 4 を想定しています"

    N = len(boards)
    xs = np.zeros((N, h, w, c), dtype=np.float32)

    for i, (board, turn) in enumerate(zip(boards, turns)):
        # turn > 0 を「自分」、turn < 0 を「相手」とする
        my_color = 1 if turn > 0 else -1

        for r in range(h):
            for col in range(w):
                v = board[r][col]
                if v == 0:
                    continue
                color = 1 if v > 0 else -1
                is_king = abs(v) == 2

                if color == my_color:
                    if not is_king:
                        xs[i, r, col, 0] = 1.0  # 自分ノーマル
                    else:
                        xs[i, r, col, 1] = 1.0  # 自分キング
                else:
                    if not is_king:
                        xs[i, r, col, 2] = 1.0  # 相手ノーマル
                    else:
                        xs[i, r, col, 3] = 1.0  # 相手キング

    return xs


# デュアルネットワークの学習
def train_network():
    # 学習データの読み込み
    # history = load_data()
    history = load_some_pickles_from_s3(
        "data", "selfplay_", max_files=None
    )  # None=全部
    # history の各要素: [ [board, turn], policies, value ]
    state_infos, y_policies, y_values = zip(*history)
    boards, turns = zip(*state_infos)

    # 入力テンソルを作成 (N, H, W, 4)
    xs = encode_board_to_tensor(boards, turns)

    # 出力の整形
    y_policies = np.array(y_policies, dtype=np.float32)  # (N, ACTION_SIZE)
    y_values = np.array(y_values, dtype=np.float32)  # (N,)

    # モデルの読み込み
    # model_path = os.path.join(MODEL_DIR_PATH, "best.keras")
    # model = load_model(model_path, compile=False)
    model = load_model_from_s3("saved_models", "best.keras")

    # モデルのコンパイル
    model.compile(
        loss=["categorical_crossentropy", "mse"],
        optimizer="adam",
    )

    # 学習率スケジューラ
    def step_decay(epoch):
        x = 0.001
        if epoch >= 50:
            x = 0.0005
        if epoch >= 80:
            x = 0.00025
        return x

    lr_scheduler = LearningRateScheduler(step_decay)

    # エポックごとの進捗表示
    print_callback = LambdaCallback(
        on_epoch_end=lambda epoch, logs: print(
            f"\rTrain {epoch+1}/{RN_EPOCHS}",
            end="",
        )
    )

    # モデルの学習
    model.fit(
        x=xs, # 入力テンソル（N, H, W, 4）
        y=[y_policies, y_values], # 出力ポリシーと価値
        batch_size=128,
        epochs=RN_EPOCHS,
        callbacks=[lr_scheduler, print_callback],
        verbose=0,
    )
    print("")

    # モデルの保存（最新パラメータ）
    # latest_path = os.path.join(MODEL_DIR_PATH, "latest.keras")
    # model.save(latest_path)
    upload_model_to_s3("saved_models", "latest.keras", model)

    # モデルの破棄
    K.clear_session()
    del model


if __name__ == "__main__":
    # デュアルネットワークの訓練・更新
    train_network()
