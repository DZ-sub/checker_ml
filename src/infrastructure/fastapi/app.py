from src.gpt_ml.checker_state import State
from src.gpt_ml.alpha_zero.pv_mcts import pv_mcts_scores
from src.gpt_ml.alpha_zero.dual_network import (
    DN_OUTPUT_SIZE,
    action_to_index,
)
from src.infrastructure.aws.s3 import load_model_from_s3

from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np


app = FastAPI()

SP_TEMPERATURE = 1.0


class RequestState(BaseModel):
    """
    board : 6×6 の整数配列
        0 : 空
        1 : RED 通常
        2 : RED キング
        -1: BLUE 通常
        -2: BLUE キング
    turn : 手番
        1 = RED
        -1 = BLUE
    turn_count : 手番数（0から始まる）
    """

    board: list[list[int]]
    turn: int
    turn_count: int


def predict(model, state: State):
    # 合法手の確率分布の取得 (legal_actions と同じ順序)
    scores = pv_mcts_scores(state, model, SP_TEMPERATURE)
    legal_actions = state.legal_actions()  # [(fr,fc,tr,tc,captured_list), ...]
    # ポリシーベクトル（全行動空間分 = DN_OUTPUT_SIZE）を0で初期化
    policies = [0.0] * DN_OUTPUT_SIZE
    # 合法手それぞれに対応する index を立てる
    for (fr, fc, tr, tc, captured), policy in zip(legal_actions, scores):
        idx = action_to_index(fr, fc, tr, tc)
        policies[idx] = policy
    # # 盤面のコピーを保存（後で State を再構成してもいいし、そのまま平面にしてもいい）
    # board_copy = [row[:] for row in state.board]
    # turn_copy = state.turn
    # 行動の取得
    # np.random.choice(legal_actions, p=...) はエラーになるので、
    # インデックスをサンプリングしてから実際の行動を取る
    action_idx = np.random.choice(len(legal_actions), p=scores)
    action = legal_actions[action_idx]  # (fr, fc, tr, tc, captured)
    return action


# application layer
def get_action_by_pv_mcts(req: RequestState):
    # チェッカーの状態を State オブジェクトに変換
    state = State(req.board, req.turn, req.turn_count)
    # モデルの読み込み
    model = app.state.model
    # 行動の予測
    pred = predict(model, state)

    return {
        "selected_piece": [pred[0], pred[1]],
        "move_to": [pred[2], pred[3]],
        "captured_pieces": pred[4],
    }


# 最初にモデルをロードしておく
@app.on_event("startup")
def skd_startup():
    app.state.model = load_model_from_s3("saved_models", "best.keras")


@app.get("/")
async def read_root():
    # checker_mlの紹介文を返す
    return {"Hello": "World"}


@app.get("/ping")
def ping():
    # 単純に 200 が返れば OK
    return {"status": "ok"}


# AIの行動を取得するエンドポイント
@app.post("/invocations")
async def invocations(req: RequestState):
    action = get_action_by_pv_mcts(req)
    return {"version": "1.0.0", "action": action}
