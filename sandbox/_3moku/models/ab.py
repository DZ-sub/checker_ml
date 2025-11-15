# α-β法

from sandbox._3moku.game import State
from sandbox._3moku.models.minmax import mini_max_action
from sandbox._3moku.models.utils.gameplay import play


def alpha_beta(state: State, alpha, beta):
    # 負けは状態価値-1
    if state.is_lose():
        return -1

    # 引き分けは状態価値0
    if state.is_draw():
        return 0

    # 合法手の状態価値を計算
    for action in state.legal_actions():
        score = -alpha_beta(state.next(action), -beta, -alpha)  # スコアを再帰的に計算

        # α値を更新
        if score > alpha:
            alpha = score

        # 現ノードのベストスコアが親ノードを超えたら終了（これ以上の改善しない）
        ## 関数をマイナスで呼び出しているので、符号が逆になることに注意
        if alpha >= beta:
            return alpha

    # 最良の状態価値を返す
    return alpha


def alpha_beta_action(state: State):
    best_action = 0
    alpha = -float("inf")
    str = ["", ""]
    for action in state.legal_actions():
        score = -alpha_beta(state.next(action), -float("inf"), -alpha)
        if score > alpha:
            best_action = action
            alpha = score

        str[0] = f"{str[0]}{action:2d}"
        str[1] = f"{str[1]}{score:2d}"

    print("action:", str[0], "\nscore: ", str[1], "\n")

    return best_action


if __name__ == "__main__":
    play([alpha_beta_action, mini_max_action])

# python -m sandbox._3moku.models.ab
