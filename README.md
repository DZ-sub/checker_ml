# checker_ml

チェッカー（6×6）ゲームのAlphaZero実装による機械学習プロジェクト

ハッカソンの制作物。

## 📋 目次

- [概要](#概要)
- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [セットアップ](#セットアップ)
- [使い方](#使い方)
- [API仕様](#api仕様)
- [プロジェクト構成](#プロジェクト構成)
- [開発](#開発)

## 概要

このプロジェクトは、6×6のチェッカーゲームをAlphaZeroアルゴリズムを用いて学習させる機械学習プロジェクトです。TensorFlow/Kerasを使用して実装されており、FastAPIを通じてAIの行動を提供するAPIサーバーとしても動作します。

### AlphaZeroとは

AlphaZeroは、DeepMindによって開発された強化学習アルゴリズムで、自己対戦（セルフプレイ）を通じてゲームの戦略を学習します。このプロジェクトでは、チェッカーゲームに適用しています。

## 主な機能

- **チェッカーゲームの実装**: Pygameを使用した6×6チェッカーゲーム
- **AlphaZero学習パイプライン**:
  - セルフプレイによるデータ生成
  - ニューラルネットワークの学習
  - モデルの評価と更新
- **FastAPI APIサーバー**: AWS SageMakerにデプロイ可能なRESTful API
- **GPU対応**: NVIDIA GPUを使用した高速学習
- **Docker対応**: 環境構築が簡単で再現性の高い実行環境

## 技術スタック

- **機械学習**: TensorFlow 2.17.0, Keras 3.5.0
- **ゲームエンジン**: Pygame
- **Webフレームワーク**: FastAPI 0.118.0
- **コンテナ**: Docker, Docker Compose
- **クラウド**: AWS (S3, SageMaker)
- **言語**: Python 3.x

## セットアップ

### 前提条件

- Docker Desktop（GPUを使用する場合はWSL2とnvidia-container-toolkit）
- または Python 3.x環境

### Dockerを使用する場合（推奨）

詳細な手順は [DOCKER_SETUP.md](./DOCKER_SETUP.md) を参照してください。

```bash
# イメージのビルド
docker-compose build

# GPU動作確認
docker run --rm --gpus all checker_ml:latest python -c "import tensorflow as tf; print('GPUs:', tf.config.list_physical_devices('GPU'))"
```

### ローカル環境でのセットアップ

```bash
# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使い方

### セルフプレイでデータを生成

```bash
docker-compose run --rm selfplay
```

または

```bash
python -m src.gpt_ml.alpha_zero.selfplay
```

### モデルの学習

```bash
docker-compose run --rm train
```

または

```bash
python -m src.gpt_ml.alpha_zero.train_network
```

### モデルの評価

```bash
docker-compose run --rm evaluate
```

または

```bash
python -m src.gpt_ml.alpha_zero.evaluate_network
```

### 学習サイクル全体の実行

```bash
docker-compose run --rm cycle
```

または

```bash
python -m src.gpt_ml.alpha_zero.train_cycle
```

### チェッカーゲームのプレイ

```bash
python -m src.game.checker
```

### APIサーバーの起動

```bash
# Dockerの場合
docker run -p 8080:8080 checker_ml:latest

# ローカルの場合
python -m src.infrastructure.fastapi.serve
```

## API仕様

### エンドポイント

#### `GET /`
ルートエンドポイント

**レスポンス:**
```json
{
  "Hello": "World"
}
```

#### `GET /ping`
ヘルスチェック用エンドポイント

**レスポンス:**
```json
{
  "status": "ok"
}
```

#### `POST /invocations`
AIの次の手を取得

**リクエスト:**
```json
{
  "board": [
    [0, 1, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1],
    [0, -1, 0, 0, -1, 0],
    [0, 0, 0, 0, 0, 0]
  ],
  "turn": 1,
  "turn_count": 10
}
```

**盤面の表記:**
- `0`: 空マス
- `1`: RED（赤）の通常駒
- `2`: REDのキング
- `-1`: BLUE（青）の通常駒
- `-2`: BLUEのキング

**手番:**
- `1`: RED
- `-1`: BLUE

**レスポンス:**
```json
{
  "version": "1.0.0",
  "action": {
    "selected_piece": [4, 1],
    "move_to": [3, 0],
    "captured_pieces": []
  }
}
```

## プロジェクト構成

```
checker_ml/
├── src/
│   ├── game/              # Pygameによるチェッカーゲーム
│   │   └── checker.py
│   ├── gpt_ml/            # AlphaZero実装（GPTバージョン）
│   │   ├── checker_state.py
│   │   ├── gameplay.py
│   │   └── alpha_zero/
│   │       ├── dual_network.py    # ニューラルネットワークモデル
│   │       ├── pv_mcts.py         # モンテカルロ木探索
│   │       ├── selfplay.py        # セルフプレイ
│   │       ├── train_network.py   # ネットワーク学習
│   │       ├── evaluate_network.py # モデル評価
│   │       └── train_cycle.py     # 学習サイクル
│   ├── ml/                # AlphaZero実装（別バージョン）
│   │   └── alpha_zero/
│   └── infrastructure/    # インフラストラクチャ
│       ├── aws/           # AWS連携（S3）
│       └── fastapi/       # APIサーバー
├── sandbox/               # 実験・検証用
├── requirements.txt       # Python依存パッケージ
├── Dockerfile            # Dockerイメージ定義
├── docker-compose.yml    # Docker Compose設定
├── DOCKER_SETUP.md       # Docker環境構築ガイド
└── AWS_SETUP.md          # AWS環境構築ガイド
```

### ディレクトリの説明

- **src/game/**: Pygameを使用したチェッカーゲームの実装
- **src/gpt_ml/**: AlphaZeroアルゴリズムを使用した機械学習パイプライン
- **src/ml/**: 別バージョンのML実装
- **src/infrastructure/**: APIサーバーとAWS連携
- **sandbox/**: 実験や検証用のコード

## 開発

### 詳細ドキュメント

- [Docker環境のセットアップ](./DOCKER_SETUP.md) - GPU対応のDocker環境構築ガイド
- [AWSセットアップ](./AWS_SETUP.md) - AWS SageMakerへのデプロイ方法

### コンテナ内での作業

```bash
docker run --rm -it --gpus all -v ${PWD}:/app checker_ml:latest bash
```

### モデルの保存場所

学習済みモデルは以下に保存されます：
- ローカル: `src/gpt_ml/alpha_zero/model/`
- AWS S3: `saved_models/best.keras`

## トラブルシューティング

### GPUが認識されない

[DOCKER_SETUP.md](./DOCKER_SETUP.md) のトラブルシューティングセクションを参照してください。

### メモリ不足エラー

Docker Desktopの設定でメモリを8GB以上に増やしてください。

## ライセンス

このプロジェクトはハッカソンの制作物です。
