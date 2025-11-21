# alpha zero の学習サイクル

from sandbox._3moku.models.alpha_zero.dual_network import make_dual_network
from sandbox._3moku.models.alpha_zero.self_play import self_play
from sandbox._3moku.models.alpha_zero.train_network import train_network
from sandbox._3moku.models.alpha_zero.evaluate_network import evaluate_network
from sandbox._3moku.models.alpha_zero.evaluate_best_player import evaluate_best_player

from dotenv import load_dotenv
import os

load_dotenv()

MODEL_DIR_PATH = os.getenv("MODEL_DIR_PATH")


# best.keras が存在しない場合、dual network の作成
if not os.path.exists(f"{os.getenv(MODEL_DIR_PATH)}/best.keras"):
    # dual network の作成
    make_dual_network()

# 学習サイクル回数
TRAIN_CYCLE_NUM = 100

# 学習サイクルの実行
for cycle in range(TRAIN_CYCLE_NUM):
    print(f"===== TRAIN CYCLE {cycle + 1} / {TRAIN_CYCLE_NUM} =====")
    # 自己対戦データの生成
    self_play()
    # ネットワークの学習
    train_network()
    # ネットワークの評価
    update_best_player = evaluate_network()
    # 最良プレイヤーの評価
    if update_best_player:
        print("モデルを更新しました。")

# python -m sandbox._3moku.models.alpha_zero.train_cycle
