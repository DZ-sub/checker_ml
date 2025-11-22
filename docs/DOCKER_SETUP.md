# GPU対応機械学習環境セットアップガイド

## 前提条件

WindowsでDockerを使用してGPUを利用する場合、**WSL2**が必要です。

### WSL2のセットアップ（まだの場合）

PowerShellを管理者権限で開き、以下を実行:
```powershell
wsl --install
wsl --set-default-version 2
```

再起動後、Docker Desktopの設定で以下を確認:
1. Settings → General → "Use the WSL 2 based engine" にチェック
2. Settings → Resources → WSL Integration → Ubuntuを有効化

## 使い方

### 1. Dockerイメージのビルド
```bash
docker-compose build
```

### 2. GPU動作確認
```bash
docker run --rm --gpus all checker_ml:latest python -c "import tensorflow as tf; print('GPUs:', tf.config.list_physical_devices('GPU'))"
```

### 3. セルフプレイでデータ生成
```bash
docker-compose run --rm alphazero
```

### 4. モデルの学習
```bash
docker-compose run --rm train
```

### 5. 対話的にコンテナ内で作業
```bash
docker run --rm -it --gpus all -v ${PWD}:/app checker_ml:latest bash
```

## トラブルシューティング

### GPUが認識されない場合

1. **nvidia-container-toolkitのインストール（WSL2内で）**
   ```bash
   wsl
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

2. **Docker Desktopの再起動**

### メモリ不足エラーの場合

Docker Desktopの設定でメモリを増やす:
- Settings → Resources → Memory → 8GB以上に設定

## ローカル環境との比較

### Dockerを使う場合
- ✅ 環境構築が簡単（CUDAインストール不要）
- ✅ 再現性が高い
- ✅ 環境を汚さない
- ❌ 初回セットアップに時間がかかる

### ローカルで直接実行する場合
- ✅ セットアップ後は高速
- ✅ デバッグが簡単
- ❌ CUDA/cuDNNのインストールが必要
- ❌ 環境が壊れるリスク

## 推奨フロー

開発中はDockerを使い、本番やデバッグ時はローカル環境を使うのがおすすめです。
