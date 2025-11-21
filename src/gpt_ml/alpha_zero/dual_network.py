from src.infrastructure.aws.s3 import upload_model_to_s3, load_bytes_from_s3

import os
from dotenv import load_dotenv
from keras import backend as K
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


# 定数・環境変数
BOARD_SIZE = 6  # 6x6 チェッカー
load_dotenv()
MODEL_DIR_PATH = os.getenv("MODEL_DIR_PATH")

# 盤面のマス数
NUM_SQUARES = BOARD_SIZE * BOARD_SIZE

# 行動空間: (fromマス, toマス) の組み合わせ
ACTION_SIZE = NUM_SQUARES * NUM_SQUARES  # 36 * 36 = 1296

# NN パラメータ
DN_FILTERS = 128  # 畳み込み層のカーネル数
DN_RESIDUAL_NUM = 16  # 残差ブロック数

# 入力の形状 (縦, 横, チャンネル)
# チャンネル例:
#   0: 自分の通常駒
#   1: 自分のキング
#   2: 相手の通常駒
#   3: 相手のキング
DN_INPUT_SHAPE = (BOARD_SIZE, BOARD_SIZE, 4)

# 出力の数（行動の数）
DN_OUTPUT_SIZE = ACTION_SIZE


# Conv・ResBlock 定義
def conv(filters):
    """共通設定の 2次元畳み込み層（Conv2D）を作るヘルパー関数"""
    return Conv2D(
        filters=filters,  # 出力チャンネル数
        kernel_size=[3, 3],  # 3x3 カーネル（盤面の局所パターンを見る）
        padding="same",  # 出力サイズを入力と同じに保つ
        use_bias=False,  # バイアス項なし（BatchNorm 前提）
        kernel_initializer="he_normal",  # He 初期化（ReLU 系推奨）
        kernel_regularizer=l2(5e-4),  # L2 正則化
    )


def residual_block():
    """ResNet 型の残差ブロック"""

    def f(x):
        sc = x
        x = conv(DN_FILTERS)(x)
        x = BatchNormalization()(x)
        x = Activation("relu")(x)

        x = conv(DN_FILTERS)(x)
        x = BatchNormalization()(x)

        x = Add()([sc, x])
        x = Activation("relu")(x)
        return x

    return f


# デュアルネットワークの作成
def make_dual_network():
    """checker 用 AlphaZero デュアルネットワークを作成して保存"""

    # モデル作成済みなら何もしない
    # os.makedirs(MODEL_DIR_PATH, exist_ok=True)
    # model_path = os.path.join(MODEL_DIR_PATH, "best.keras")
    # if os.path.exists(model_path):
    #     return
    existing = load_bytes_from_s3("saved_models", "best.keras")
    if existing:
        print("S3 に best.keras が既に存在するため、モデル作成をスキップ。")
        return

    # 入力層
    input = Input(shape=DN_INPUT_SHAPE)

    # 畳み込み + 残差ブロック
    x = conv(DN_FILTERS)(input)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    for _ in range(DN_RESIDUAL_NUM):
        x = residual_block()(x)

    # グローバルプーリング
    x = GlobalAveragePooling2D()(x)

    # ポリシー出力（行動 0〜ACTION_SIZE-1 への確率分布）
    p = Dense(
        DN_OUTPUT_SIZE,
        kernel_regularizer=l2(5e-4),
        activation="softmax",
        name="pi",
    )(x)

    # バリュー出力（-1〜1）
    v = Dense(1, kernel_regularizer=l2(5e-4))(x)
    v = Activation("tanh", name="v")(v)

    # モデル作成
    model = Model(inputs=input, outputs=[p, v])

    # モデル保存（S3）
    upload_model_to_s3("saved_models", "best.keras", model)

    # メモリ解放
    K.clear_session()
    del model


# State.legal_actions() からの (fr, fc, tr, tc) <-> index 変換に使える


def action_to_index(fr, fc, tr, tc):
    """
    盤上の座標 (fr, fc) -> (tr, tc) を [0, ACTION_SIZE) の index に変換
    """
    from_id = fr * BOARD_SIZE + fc
    to_id = tr * BOARD_SIZE + tc
    return from_id * NUM_SQUARES + to_id


def index_to_action(index):
    """
    index (0 ~ ACTION_SIZE-1) から (fr, fc, tr, tc) を復元
    """
    from_id, to_id = divmod(index, NUM_SQUARES)
    fr, fc = divmod(from_id, BOARD_SIZE)
    tr, tc = divmod(to_id, BOARD_SIZE)
    return fr, fc, tr, tc


if __name__ == "__main__":
    # デュアルネットワークの作成
    make_dual_network()

# python -m src.gpt_ml.alpha_zero.dual_network
