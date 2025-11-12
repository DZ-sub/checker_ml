from sandbox._3moku.game import State, input_action, random_action

# ミニマックス法で状態価値計算
def mini_max(state: State):
    # 負けは状態価値-1
    if state.is_lose():
        return -1
    
    # 引き分けは状態価値0
    if state.is_draw():
        return 0
    
    # 合法手の状態価値を計算
    best_score = -float("inf") # 初期値（マイナス無限大）
    for action in state.legal_actions():
        score = -mini_max(state.next(action))
        if score > best_score:
            best_score = score

    # 最良の状態価値を返す
    return best_score

# ミニマックス法で行動選択
def mini_max_action(state: State):
    best_score = -float("inf") # 初期値（マイナス無限大）
    best_action = 0
    str = ["", ""]
    for action in state.legal_actions():

        score = -mini_max(state.next(action))
        if score > best_score:
            best_score = score
            best_action = action
    
        str[0] = f"{str[0]}{action:2d}"
        str[1] = f"{str[1]}{score:2d}"
    
    print("action:", str[0], "\nscore: ", str[1], "\n")

    # 合法手の状態価値が最も高い行動を返す
    return best_action

def main():
    # ゲーム状態の初期化
    state = State()

    while True:
        if state.is_done():
            break
        if state.is_first_player():
            action = mini_max_action(state)
        else:
            action = input_action(state)
        state = state.next(action)
        print(state)

if __name__ == "__main__":
    main()