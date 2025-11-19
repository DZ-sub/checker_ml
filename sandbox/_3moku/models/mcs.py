# 原始モンテカルロ探索

from sandbox._3moku.game import State, random_action
from sandbox._3moku.models.ab import alpha_beta_action
from sandbox._3moku.models.utils.evaluate import evaluate_algorithm_of


# プレイアウト
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


# 最大値のインデックスを返す
def argmax(collection: list, key=None):
    return collection.index(max(collection))


# 原始モンテカルロ探索による行動選択
def mcs_action(state: State, n_playout: int = 10):
    """
    各合法手についてn_playout回プレイアウトを行い、最も勝率の高い手を選択する
    """
    leagal_actions = state.legal_actions()
    # 合法手分のリストを用意
    values = [0] * len(leagal_actions)
    # 各合法手についてn_playout回プレイアウトを実行し状態価値をいれる
    for i, action in enumerate(leagal_actions):
        for _ in range(n_playout):
            values[i] += -playout(state.next(action))

    # 最良の手を選択
    return leagal_actions[argmax(values)]


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


# 原始モンテカルロ探索のアルゴリズム評価
if __name__ == "__main__":
    # # VS random
    # next_actions = (mcs_action, random_action)
    # evaluate_algorithm_of("random", next_actions)

    # vs alpha-beta
    next_actions = (mcs_action, alpha_beta_action)
    evaluate_algorithm_of("alpha-beta", next_actions)

# python -m sandbox._3moku.models.mcs
