# TensorFlow GPU対応イメージを使用
FROM tensorflow/tensorflow:2.17.0-gpu

# 作業ディレクトリ
WORKDIR /app

# Pythonパッケージのインストール
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

ENV PORT=8080
EXPOSE 8080

# デフォルトコマンド
CMD ["uvicorn", "src.infrastructure.fastapi.app:app", "--host", "0.0.0.0", "--port", "8080"]
