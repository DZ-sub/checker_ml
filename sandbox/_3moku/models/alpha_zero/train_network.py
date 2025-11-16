# 学習データによるニューラルネットワークの訓練・更新

from sandbox._3moku.models.alpha_zero.dual_network import DN_INPUT_SHAPE

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

# 学習データの読み込み
def load_data():
    pickle_path = sorted(Path(DATA_DIR_PATH).glob("*.pkl"))[-1]
    with open(pickle_path, "rb") as f:
        return pickle.load(f)

# デュアルネットワークの学習
def train_network():
    # 学習データの読み込み
    history = load_data()
    xs, y_policies, y_values = zip(*history)

    h, w, c = DN_INPUT_SHAPE  # 入力形状（縦, 横, チャンネル）
    xs = np.array(xs)
    xs = xs.reshape(len(xs), c, h, w).transpose(0, 2, 3, 1)  # 形状変換（バッチサイズ, 縦, 横, チャンネル）
    y_policies = np.array(y_policies)
    y_values = np.array(y_values)

    # モデルの読み込み
    model = load_model(f"{MODEL_DIR_PATH}/best.keras")

    # モデルのコンパイル
    model.compile(
        loss=["categorical_crossentropy", "mse"],
        optimizer="adam"
    )

    # 学習率
    def step_decay(epoch):
        x = 0.001
        if epoch >= 50: x = 0.0005
        if epoch >= 80: x = 0.00025
        return x
    lr_scheduler = LearningRateScheduler(step_decay)

    # 出力
    print_callback = LambdaCallback(
        on_epoch_end=lambda epoch, logs: print(
            f"\rTrain {epoch+1}/{RN_EPOCHS}", end="",
        )
    )

    # モデルの学習
    model.fit(
        x=xs,
        y=[y_policies, y_values],
        batch_size=128,
        epochs=RN_EPOCHS,
        callbacks=[lr_scheduler, print_callback],
        verbose=0,
    )
    print("")

    # モデルの保存
    model.save(f"{MODEL_DIR_PATH}/latest.keras")

    # モデルの破棄
    K.clear_session()
    del model

if __name__ == "__main__":
    # デュアルネットワークの訓練・更新
    train_network()

# python -m sandbox._3moku.models.alpha_zero.train_network