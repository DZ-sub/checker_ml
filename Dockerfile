# TensorFlow GPU対応イメージを使用
FROM tensorflow/tensorflow:2.17.0-gpu

# 作業ディレクトリ
WORKDIR /app

# Pythonパッケージのインストール
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードのコピー
COPY src ./src

# 環境変数とポート設定
ENV PORT=8080
EXPOSE 8080

# # デフォルトコマンド
# CMD ["uvicorn", "src.infrastructure.fastapi.app:app", "--host", "0.0.0.0", "--port", "8080"]

# SageMaker の `docker run <image> serve` を想定したENTRYPOINT
ENTRYPOINT ["python", "-m", "src.infrastructure.fastapi.serve"]
CMD ["serve"]