from src.ml.checker_state import State


# 先手プレイヤーのポイント
def first_player_point(ended_state: State):
    # 1: 先手勝利, 0.5: 引き分け, 0: 先手敗北
    if ended_state.is_lose():
        if ended_state.is_first_player():
            return 0
        else:
            return 1
    else:
        return 0.5


# 1ゲームの実行
def play(next_actions):
    # 状態の生成
    state = State()
    # ゲームループ
    while True:
        # ゲーム終了判定
        if state.is_done():
            break

        # 行動の取得
        if state.is_first_player():
            action = next_actions[0](state)
        else:
            action = next_actions[1](state)

        # 状態更新
        state = state.next(action)
        # 表示
        print(state)

    # 先手プレイヤーのポイントを返す
    return first_player_point(state)
