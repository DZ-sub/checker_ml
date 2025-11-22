# checker_ml

チェッカー（6×6）ゲーム + AlphaZero実装による機械学習プロジェクト

ハッカソンの制作物。

## 📋 目次

- [概要](#概要)
- [ディレクトリ構成](#ディレクトリ構成)
- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [AlphaZeroについての説明](#AlphaZeroについての説明)
- [セットアップ](#セットアップ)
- [API仕様](#api仕様)
- [開発過程](#開発過程)

## 概要

このプロジェクトは、6×6のチェッカーゲームをAlphaZeroアルゴリズムを用いて学習させる機械学習プロジェクトです。
**チェッカー**: https://ja.wikipedia.org/wiki/%E3%83%81%E3%82%A7%E3%83%83%E3%82%AB%E3%83%BC
**AlphaZero**


## ディレクトリ構成

```
checker_ml/
├── src/
│   ├── game/              # Pygameによるチェッカーゲーム
│   │   └── checker.py
│   ├── ml/            # AlphaZero実装
│   │   ├── checker_state.py
│   │   ├── gameplay.py
│   │   └── alpha_zero/
│   │       ├── dual_network.py    # ニューラルネットワークモデル
│   │       ├── pv_mcts.py         # モンテカルロ木探索
│   │       ├── selfplay.py        # セルフプレイ
│   │       ├── train_network.py   # ネットワーク学習
│   │       ├── evaluate_network.py # モデル評価
│   │       └── train_cycle.py     # 学習サイクル
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
- **src/ml/**: AlphaZeroアルゴリズムを使用した機械学習パイプライン
- **src/infrastructure/**: APIサーバーとAWS連携
- **sandbox/**: 実験や検証用のコード

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
### src/game/（フロント層）
- **ゲームエンジン**: Pygame
### src/ml/（）
- **機械学習**: TensorFlow 2.17.0 (Dockerベースイメージ), Keras 3.5.0
- **Webフレームワーク**: FastAPI 0.118.0
- **コンテナ**: Docker, Docker Compose
- **クラウド**: AWS (S3, EC2, Lambda, SageMaker, APIGateway)
- **言語**: Python 3.x

## 機械学習部分（AlphaZero）についての説明


## セットアップ

### 前提条件

- **Docker Desktop**: GPUを使用する場合は以下も必要
  - Windows: WSL2（Docker Desktopが自動でGPU対応）
  - Linux: nvidia-container-toolkit
- **または** Python 3.x環境とTensorFlow 2.17.0

### AWSを使用する場合（推奨）

### Dockerを使用する場合（推奨）

[DOCKER_SETUP.md](./DOCKER_SETUP.md) を参照してください。

## API仕様

### AWS環境のエンドポイント

### Docker環境のエンドポイント

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


## 開発過程

### スケジュール

- **5日～13日**: 設計・C4モデルの作成
- **13日～18日**: 練習・勉強（sandbox/）
- **18～23日**: 開発（src/）

## C4モデル

**C4モデル**: https://c4model.com/

### Context

### Container

### Component

## 参考資料・文献

**AlphaZero 深層学習・強化学習・探索 人工知能プログラミング実践入門**: https://www.amazon.co.jp/AlphaZero-%E6%B7%B1%E5%B1%A4%E5%AD%A6%E7%BF%92%E3%83%BB%E5%BC%B7%E5%8C%96%E5%AD%A6%E7%BF%92%E3%83%BB%E6%8E%A2%E7%B4%A2-%E4%BA%BA%E5%B7%A5%E7%9F%A5%E8%83%BD%E3%83%97%E3%83%AD%E3%82%B0%E3%83%A9%E3%83%9F%E3%83%B3%E3%82%B0%E5%AE%9F%E8%B7%B5%E5%85%A5%E9%96%80-%E5%B8%83%E7%95%99%E5%B7%9D-%E8%8B%B1%E4%B8%80/dp/4862464505?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&ref_=fplfs&psc=1&smid=AN1VRQENFRJN5

**スッキリわかるAlphaZero**: https://horomary.hatenablog.com/entry/2021/06/21/000500

