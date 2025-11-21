# sagemaker_model/code/inference.py

import json

from src.ml.checker_state import State
from src.ml.alpha_zero.pv_mcts import pv_mcts_action
from src.infrastructure.s3 import load_model_from_s3



# ---------- 必須: モデルロード ----------
def model_fn():
    """
    モデルのロード。s3//<バケット名>/saved_models/best.keras から取得。
    返り値: Keras モデルオブジェクト 
    """
    return load_model_from_s3("saved_models", "best.keras")
     


# ---------- 必須: 入力のパース ----------
def input_fn(request_body, content_type="application/json"):
    """
    API リクエストの JSON → (board, turn) に変換。
    期待するJSONフォーマット:
      {
        "board": [[...6要素...], ... x6],
        "turn": 1 or -1
      }
    """
    if content_type != "application/json":
        raise ValueError(f"Unsupported content type: {content_type}")

    data = json.loads(request_body)
    board = data["board"]
    turn = data["turn"]
    return board, turn


# ---------- 必須: 推論本体 ----------
def predict_fn(input_data, model):
    """
    (board, turn) から、AlphaZero+MCTS で次の一手を選ぶ。
    """
    board, turn = input_data

    # State を復元
    state = State(board=board, turn=turn)

    # MCTS付きの行動選択関数
    # temperature=0 で「一番強そうな手」を決め打ち
    pv = pv_mcts_action(model, temperature=0.0)

    # 1手取得: (fr, fc, tr, tc, captured_list)
    fr, fc, tr, tc, captured = pv(state)

    # SageMaker → Lambda → クライアント に返しやすい形に整形
    result = {
        "from": [fr, fc],
        "to": [tr, tc],
        "captured": captured,  # [[r,c], ...]
    }
    return result


# ---------- 必須: 出力のシリアライズ ----------
def output_fn(prediction, accept="application/json"):
    if accept != "application/json":
        raise ValueError(f"Unsupported accept: {accept}")

    body = json.dumps(prediction)
    return body, accept
