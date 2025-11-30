(このファイルは再作成されました)

## Docker セットアップと運用ガイド

このドキュメントはリポジトリ内の `Dockerfile.serve` と `Dockerfile.train` を使ったイメージのビルド、ローカル実行（GPU 対応含む）、および ECR へ push して SageMaker で使うまでの手順をまとめたものです。

前提

- Docker がインストールされていること（Windows の場合は Docker Desktop + WSL2 推奨）
- GPU を使う場合は NVIDIA Container Toolkit（nvidia-docker2 相当）がセットアップ済みであること
- AWS CLI が設定済み（`aws configure` で認証情報とデフォルトリージョンを設定）
- （ECR に push する場合）ECR にリポジトリが存在するか、作成できる権限があること

主要ファイル

- `Dockerfile.serve` — 推論（serve）イメージ。ENTRYPOINT が `python -m src.infrastructure.fastapi.serve` になっており SageMaker の `serve` コマンド想定。
- `Dockerfile.train` — 学習用イメージ。デフォルトコマンドで学習ループを起動する想定。
- `requirements.txt` — 依存パッケージ

ローカルでのビルド（PowerShell 例）

```powershell
# docker に環境変数を渡す場合は -e オプションを使う
# 例: S3 バケット名や AWS リージョンを環境変数で渡す場合
docker build -f Dockerfile.serve -t checker-serve .
docker run --rm -e S3_BUCKET_NAME=my-bucket -e AWS_REGION=ap-northeast-1 -e AWS_ACCESS_KEY_ID=<> -e AWS_SECRET_ACCESS_KEY=<>
```

```powershell
# serve イメージをビルド
docker build -f Dockerfile.serve -t checker-serve:latest .

# train イメージをビルド
docker build -f Dockerfile.train -t checker-train:latest .
```

コンテナを GPU で実行する（確認用）

```powershell
# GPU を使って serve を起動してポート 8080 を公開する
docker run --rm --gpus all -p 8080:8080 checker-serve:latest

# コンテナ内で Python のバージョンや TensorFlow を確認する
docker run --rm checker-serve:latest python -c "import sys, tensorflow as tf; print(sys.version); print(tf.__version__)"
```

注意（Windows）: Docker Desktop + WSL2 の組み合わせで GPU を使うには追加設定が必要です。Docker Desktop の GPU サポート（Windows の WSL2 GPU paravirtualization）や NVIDIA ドライバが正しく入っているか確認してください。

ECR に push して SageMaker で使う

1) ECR リポジトリを作成（存在しない場合）

```powershell
# リポジトリ名例: checker-serve
aws ecr create-repository --repository-name checker-serve --region ap-northeast-1
```

2) ECR にログインしてタグ付け、push

```powershell
$account_id = (aws sts get-caller-identity --query Account --output text)
$region = 'ap-northeast-1'
$repo = "checker-serve"
$uri = "$account_id.dkr.ecr.$region.amazonaws.com/$repo"

# ログイン
aws ecr get-login-password --region $region | docker login --username AWS --password-stdin $uri

# タグ付け
docker tag checker-serve:latest $uri:latest

# push
docker push $uri:latest
```

3) Terraform の `ecr_image_uri` 変数にこの URI を設定して `terraform apply` することで、SageMaker のモデル定義でこのイメージを参照できます。

Python バージョン固定について（選択肢）

1. ベースイメージのタグを変える（推奨）
- 公式 TensorFlow イメージは特定の Python バージョンとビルドされています。互換性を保つため、`FROM tensorflow/tensorflow:<version>-gpu` のタグを公式ドキュメントで確認して、対応する Python バージョンのイメージを選んでください。

2. Dockerfile 内で Python をインストールして切り替える（上級）
- Debian ベースのイメージであれば apt で別の Python を追加インストールし、`update-alternatives` で `/usr/bin/python` を切り替える方法があります。ただし TensorFlow や CUDA ランタイムとの互換性に注意が必要です。

実践的な推奨

- 基本はベースイメージのタグを変えて Python/TensorFlow の互換性を維持する。
- もしどうしても Python を入れ替える場合は、イメージをビルドしてテスト（`python -c "import tensorflow as tf; print(tf.__version__)"`）を必ず行う。
- requirements.txt に GPU/CPU 固有のパッケージが含まれる場合はビルドとテストを徹底する。

トラブルシューティング

- ビルドが失敗する: Docker のキャッシュをクリアして再ビルド（`docker build --no-cache ...`）。
- GPU が認識されない: `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi` などで GPU が見えるか確認。Docker Desktop と NVIDIA ドライバ / WSL2 のバージョン整合性が必要。
- Push 時の認証エラー: `aws ecr get-login-password` の結果を使用してログインし、正しいアカウント / リージョンを使っていることを確認。

補足: docker-compose

このリポジトリには `docker-compose-sandbox.yml` があり、ローカルの学習/評価ワークフローを複数コンテナで起動する設定が含まれています。GPU を使うために `runtime: nvidia` が設定されていますが、Docker Compose のバージョンや Docker Desktop の設定によっては `--gpus` オプションを明示的に使う必要があります。

---
作成者: リポジトリ自動生成ドキュメント

