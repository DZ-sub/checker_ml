# TensorFlow GPU対応イメージを使用
FROM tensorflow/tensorflow:2.17.0-gpu

# 作業ディレクトリ
WORKDIR /app

# Pythonパッケージのインストール
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# デフォルトコマンド
CMD ["python", "-m", "sandbox._3moku.models.alpha_zero.self_play"]
