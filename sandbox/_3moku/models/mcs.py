# 原始モンテカルロ探索

from sandbox._3moku.game import State, random_action

def playout(state: State):
    """
    今の局面からゲームを終了までランダムにプレイする
    """
    # 負けは状態価値-1
    if state.is_lose():
        return -1
    # 引き分けは状態価値0
    if state.is_draw():
        return 0
    
    # ランダムに行動を選択して次の局面へ（再帰）
    action = random_action(state)
    return -playout(state.next(action))
    