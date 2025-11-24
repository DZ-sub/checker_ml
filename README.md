## checker_ml

### チェッカー（6×6）ゲーム + AlphaZeroを参考にした機械学習プロジェクト（ハッカソンの制作物。）

**チェッカー**: https://ja.wikipedia.org/wiki/%E3%83%81%E3%82%A7%E3%83%83%E3%82%AB%E3%83%BC

**AlphaZero**: https://deepmind.google/blog/alphazero-shedding-new-light-on-chess-shogi-and-go/?utm_source=chatgpt.com


## 📋 目次

- [ディレクトリ構成](#ディレクトリ構成)
- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [モデル開発](#モデル開発)
- [セットアップ](#セットアップ)
- [API仕様](#api仕様)
- [開発過程](#開発過程)
- [C4モデル](#c4モデル)
- [参考資料・文献](#参考資料・文献)


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
├── outputs/               # 学習データ・モデル保存先（.gitignore）
├── docs/                  # ドキュメント
├── requirements.txt      # Python依存パッケージ
├── Dockerfile.serve      # Dockerイメージ定義（推論用）
├── Dockerfile.train      # Dockerイメージ定義（学習用）
├── docker-compose.yml    # Docker Compose設定
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

### 全体像
[docs/images/container.png](docs/images/container.png)

### src/game/（ゲーム層・フロントエンド）
- ゲーム画面・操作: Pygame（Python）

### src/ml/（AIバックエンド層）
- 機械学習: TensorFlow 2.17.0, Keras 3.5.0
- Web API: FastAPI 0.118.0（AI予測API）
- 言語: Python 3.x

### インフラ（デプロイ基盤）
- コンテナ: Docker, Docker Compose
- クラウド: AWS（S3, EC2, Lambda, SageMaker, API Gateway）
- IaC: Terraform


### AIバックエンド層（AlphaZero）について
- **src/ml/alpha_zero/dual_network.py**: ニューラルネットワークモデルの定義
- **src/ml/alpha_zero/pv_mcts.py**: PVモンテカルロ木探索の実装
- **src/ml/alpha_zero/selfplay.py**: セルフプレイによるデータ生成
- **src/ml/alpha_zero/train_network.py**: ニューラルネットワークの学習
- **src/ml/alpha_zero/evaluate_network.py**: モデルの評価と更新
- **src/ml/alpha_zero/train_cycle.py**: 学習サイクルの管理

## モデル開発（超ざっくり）※びっくりするぐらいざっくりです。
### 行動選択のためのモデル作成

```python
# src/ml/alpha_zero/dual_network.py

def conv(filters):
    return Conv2D(
        filters=filters,
        kernel_size=[3, 3],
        padding="same",
        use_bias=False,
        kernel_initializer="he_normal",  # ★ ランダム初期化
        kernel_regularizer=l2(5e-4),
    )

# 畳み込み + 残差ブロック
x = conv(DN_FILTERS)(input)
x = BatchNormalization()(x)
x = Activation("relu")(x)

# ポリシー出力（行動 0〜ACTION_SIZE-1 への確率分布）
p = Dense(
    DN_OUTPUT_SIZE,
    kernel_regularizer=l2(5e-4),
    activation="softmax",  # ★ policy head
    name="pi",
)(x)

# バリュー出力（-1〜1）
v = Dense(1, kernel_regularizer=l2(5e-4))(x)
v = Activation("tanh", name="v")(v)  # ★ value head

# モデル作成
model = Model(inputs=input, outputs=[p, v])

```
conv だけでなく、最後の Dense 層（p, v の部分）もランダム初期化なので、
モデル全体の重みがランダム → その結果として p, v も最初は意味のない予測になる。

p: 全行動の行動確率分布（Policy）

v: 盤面の状態価値（Value）今の盤面はどれくらい強いか

convがランダムなため、p,vも最初はランダムな値を出力する。

### 自己対戦：自分で対戦データを作る。
```python
## src/ml/alpha_zero/pv_mcts.py
# 推論
pi_full, v = model.predict(
    x, batch_size=1, verbose=0
)  # pi_full.shape=(1, ACTION_SIZE)
```
x: (1, 盤面高さ, 盤面幅, チャンネル数)のテンソル src/ml/alpha_zero/DN_INPUT_SHAPEに対応

pi_full, v をもとに Policy と Value を作成

```python
## src/ml/alpha_zero/selfplay.py

# 学習データに [state_info, policies, value(None)] を追加
history.append([[board_copy, turn_copy], policies, None])
```
自己探索により、盤面状態と行動確率分布を保存

### モデルの学習
```python
## src/ml/alpha_zero/train_network.py

# モデルの学習
model.fit(
    x=xs, # 入力テンソル（N, H, W, 4）
    y=[y_policies, y_values], # 出力ポリシーと価値
    batch_size=128,
    epochs=RN_EPOCHS,
    callbacks=[lr_scheduler, print_callback],
    verbose=0,
)
```
xs: (N, 盤面高さ, 盤面幅, チャンネル数)のテンソル
y: Policy, Value

### 強化学習の全体像
```
自己対戦を繰り返しながら、モデルを学習していく。

1. **行動選択モデル（dual_network）を作る**
   - `conv`（畳み込み + 残差ブロック）で盤面の特徴を抽出する。
   - `p`（Policy Head）は「全行動の確率分布」を出力する。
   - `v`（Value Head）は「今の盤面がどれくらい勝ちやすいか（-1〜1）」を出力する。
   - これらの重みは最初ランダムに初期化されるため、初期状態では p, v の予測にはまだ意味がなく、
     学習を通じて少しずつ賢くなっていく。

2. **自己対戦（selfplay）でデータを集める**
   - 局面 `x` をモデルに入力し、`pi_full, v = model.predict(x)` で Policy と Value を予測する。
   - 予測した Policy をもとに MCTS（木探索）でさらに探索し、その局面での「最終的な行動確率分布（policies）」を得る。
   - 各手について `[盤面(state_info), 行動確率分布(policies), 最終結果(None)]` を `history` に保存し、
     対局終了時に勝敗（+1 / 0 / -1）を埋めて学習用データとする。

3. **モデルの学習（train_network）**
   - `history` から入力テンソル `xs`（形状: (N, H, W, 4)）と、
     教師データ `y_policies`（MCTS で得た行動確率）・`y_values`（最終勝敗）を作る。
   - `model.fit(x=xs, y=[y_policies, y_values], ...)` を実行し、
     「モデルの出力する p, v が、自己対戦から得られた良い手・実際の勝敗に近づくように」
     ネットワークの重みを更新する。
   - 学習後のモデルを使って再び selfplay を行い、このループを繰り返すことで、
     自分で対戦しながら自分の Policy（手の選び方）と Value（盤面評価）を改善していく。
```
## セットアップ

### 前提条件

- **Docker Desktop**: GPUを使用する場合は以下も必要
  - Windows: WSL2（Docker Desktopが自動でGPU対応）
  - Linux: nvidia-container-toolkit
- **または** Python 3.x環境とTensorFlow 2.17.0

### AWSを使用する場合（⚠️1日20ドル以上かかります...）インスタンス調整してください

[AWS_SETUP.md](./AWS_SETUP.md) を参照してください。

### Dockerを使用する場合（推奨：モデル学習にはクソ時間かかります）

[DOCKER_SETUP.md](./DOCKER_SETUP.md) を参照してください。

## API仕様

### AWS環境のエンドポイント

https://4djo1pd0h8.execute-api.ap-northeast-1.amazonaws.com/（dev）

### `POST /actions`


**リクエスト:**
```
{
  "board": [
    [0, 1, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1],
    [0, -1, 0, 0, -1, 0],
    [0, 0, 0, 0, 0, 0]
  ], # 盤面の表記
  "turn": 1, # 手番
  "turn_count": 10 # 手数
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
```
{
  "version": "1.0.0",
  "action": {
    "selected_piece": [4, 1], # 選択した駒の位置
    "move_to": [3, 0], # 移動先の位置
    "captured_pieces": [] # 取った駒の位置リスト
  }
}
```


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

### C4モデルとは: https://c4model.com/

なんちゃってではありますが、C4モデルを作成しました。

container, componentレベルが難しく、かなり雑ではありますが、ご容赦ください。

### Context
[C4モデル - コンテキスト図](docs/pdfs/context.pdf)

### Container
[C4モデル - コンテナ図](docs/pdfs/container.pdf)

### Component
[C4モデル - コンポーネント図](docs/pdfs/component.pdf)

### Code
※ Codeレベルの図は今回は未実装

## 参考資料・文献

### AlphaZero関連

**AlphaZero 深層学習・強化学習・探索 人工知能プログラミング実践入門**: https://www.amazon.co.jp/AlphaZero-%E6%B7%B1%E5%B1%A4%E5%AD%A6%E7%BF%92%E3%83%BB%E5%BC%B7%E5%8C%96%E5%AD%A6%E7%BF%92%E3%83%BB%E6%8E%A2%E7%B4%A2-%E4%BA%BA%E5%B7%A5%E7%9F%A5%E8%83%BD%E3%83%97%E3%83%AD%E3%82%B0%E3%83%A9%E3%83%9F%E3%83%B3%E3%82%B0%E5%AE%9F%E8%B7%B5%E5%85%A5%E9%96%80-%E5%B8%83%E7%95%99%E5%B7%9D-%E8%8B%B1%E4%B8%80/dp/4862464505?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&ref_=fplfs&psc=1&smid=AN1VRQENFRJN5

**スッキリわかるAlphaZero**: https://horomary.hatenablog.com/entry/2021/06/21/000500

### AWS関連

**AWS 推論コンテナイメージ**: https://docs.aws.amazon.com/ja_jp/sagemaker/latest/dg/neo-deployment-hosting-services-container-images.html

**Deploying ML Models to AWS with Docker and SageMaker**: https://tuanatran.medium.com/deploying-ml-models-to-aws-with-docker-and-sagemaker-32ff8fe6cf29

**Amazon SageMaker AI がトレーニングイメージを実行する方法**: https://docs.aws.amazon.com/ja_jp/sagemaker/latest/dg/your-algorithms-training-algo-dockerfile.html

※ AWS SageMaker の推論と学習でコンテナのエントリーポイントを指定する必要があるという情報がマジで少なかったです。（学習用: train.py, 推論用: serve.py）