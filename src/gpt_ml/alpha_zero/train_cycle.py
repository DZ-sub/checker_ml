# AlphaZero の学習サイクル（checker 用）

from src.gpt_ml.alpha_zero.dual_network import make_dual_network
from src.gpt_ml.alpha_zero.selfplay import selfplay
from src.gpt_ml.alpha_zero.train_network import train_network
from src.gpt_ml.alpha_zero.evaluate_network import evaluate_network

from dotenv import load_dotenv
import os

load_dotenv()

MODEL_DIR_PATH = os.getenv("MODEL_DIR_PATH")

if MODEL_DIR_PATH is None:
    raise RuntimeError("環境変数 MODEL_DIR_PATH が設定されていません。")


# best.keras が存在しない場合、dual network の作成
best_model_path = os.path.join(MODEL_DIR_PATH, "best.keras")
if not os.path.exists(best_model_path):
    print("best.keras が見つからないため、新しいデュアルネットワークを作成します。")
    make_dual_network()

# 学習サイクル回数
TRAIN_CYCLE_NUM = 100

# 学習サイクルの実行
for cycle in range(TRAIN_CYCLE_NUM):
    print(f"===== TRAIN CYCLE {cycle + 1} / {TRAIN_CYCLE_NUM} =====")

    # 1. 自己対戦データの生成
    selfplay()

    # 2. ネットワークの学習（latest.keras を更新）
    train_network()

    # 3. ネットワークの評価（latest vs best）
    updated = evaluate_network()

    # 4. 最良プレイヤー更新のログ
    if updated:
        print("モデルを更新しました。（latest -> best）")
    else:
        print("モデルは更新されませんでした。")

    # もし「人間 or ルールベースとの評価」を追加したくなったら、
    # evaluate_best_player(...) をここで呼ぶ形にすると良いです。

if __name__ == "__main__":
    # このファイルを直接実行したときのエントリポイント
    pass