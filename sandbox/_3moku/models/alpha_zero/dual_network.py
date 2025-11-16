from keras.layers import (
    Activation,
    Add,
    BatchNormalization,
    Conv2D,
    Dense,
    GlobalAveragePooling2D,
    Input,
)
from keras.models import Model
from keras.regularizers import l2
from keras import backend as K
import os

# パラメータ準備
DN_FILTERS = 128  # 畳み込み層のカーネル数
DN_RESIDUAL_NUM = 16  # 残差ブロック数
DN_INPUT_SHAPE = (
    3,
    3,
    2,
)  # 入力の形状 (縦, 横, チャンネル) チャンネル数は2(先手と後手)
DN_OUTPUT_SIZE = 9  # 行動の数(3x3マス)


# 畳み込み層の作成
def conv(filters):
    # 共通設定の 2次元畳み込み層（Conv2D）を作るヘルパー関数
    return Conv2D(
        filters=filters,  # 出力チャンネル数（フィルタの枚数）　torchのLinearのout_featuresに相当
        kernel_size=[3, 3],  # カーネル（フィルタ）の縦横サイズを 3×3 にする
        padding="same",  # 出力のサイズを入力と同じにする
        use_bias=False,  # バイアス項を使わない（BatchNormと一緒に使う想定など）
        kernel_initializer="he_normal",  # He正規分布で重みを初期化（ReLU系に向いた初期化）
        kernel_regularizer=l2(
            5e-4
        ),  # L2正則化（重みに 5e-4 のペナルティをかけて過学習を抑制）
    )


# 残差ブロックの作成
def residual_block():
    def f(x):
        sc = x
        x = conv(DN_FILTERS)(x)  # 畳み込み層（1層目）
        x = BatchNormalization()(x)  # バッチ正則化
        x = Activation("relu")(x)  # 活性化関数
        x = conv(DN_FILTERS)(x)  # 畳み込み層（2層目）
        x = BatchNormalization()(x)  # バッチ正則化
        x = Add()([sc, x])  # スキップ接続
        x = Activation("relu")(x)  # 活性化関数
        return x

    return f


# デュアルネットワークの作成
def make_dual_network(save_dir_path: str = "./saved_models"):
    # モデル作成済みの場合は無処理
    if os.path.exists(f"{save_dir_path}/best.h5"):
        return
    # 入力層
    input = Input(shape=DN_INPUT_SHAPE)
    # 畳み込み層
    x = conv(DN_FILTERS)(input)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    # 残差ブロックをDN_RESIDUAL_NUM回繰り返す
    for i in range(DN_RESIDUAL_NUM):
        x = residual_block()(x)

    # プーリング層
    x = GlobalAveragePooling2D()(x)

    # ポリシー出力
    p = Dense(
        DN_OUTPUT_SIZE, kernel_regularizer=l2(5e-4), activation="softmax", name="pi"
    )(x)

    # バリュー出力
    v = Dense(1, kernel_regularizer=l2(5e-4))(x)
    v = Activation("tanh", name="v")(v)

    # モデル作成
    model = Model(inputs=input, outputs=[p, v])

    # モデル保存
    os.makedirs(save_dir_path, exist_ok=True)
    model.save(f"{save_dir_path}/best.h5")

    K.clear_session()
    del model


if __name__ == "__main__":
    # デュアルネットワークの作成
    make_dual_network(save_dir_path="sandbox/_3moku/saved_models")

# python -m sandbox._3moku.models.alpha_zero.dual_network
