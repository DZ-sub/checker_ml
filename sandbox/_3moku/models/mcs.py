# 原始モンテカルロ探索

from sandbox._3moku.game import State, random_action
from sandbox._3moku.models.ab import alpha_beta_action


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
        next_action = next_actions[0] if state.is_first_player() else next_actions[1]
        action = next_action(state)

        # 状態更新
        state = state.next(action)

    # 先手プレイヤーのポイントを返す
    return first_player_point(state)


# アルゴリズム評価
def evaluate_algorithm_of(label, next_actions, EP_GAME_COUNT = 100):
    """
    next_actions回ゲームを繰り返してその平均成績を見る

    label: アルゴリズム名
    next_actions: (先手の行動選択関数, 後手の行動選択関数)
    EP_GAME_COUNT: 対戦回数
    """
    # 複数回の対戦を繰り返す
    total_point = 0
    for i in range(EP_GAME_COUNT):
        # 1ゲームの実行
        if i % 2 == 0:
            total_point += play(next_actions)
        else:
            # 先手後手を入れ替えて実行
            total_point += 1 - play(list(reversed(next_actions)))

            # 出力
        print(f"\rEvaluate {i + 1}/{EP_GAME_COUNT}", end="")
    print("")
    # 平均ポイントを計算
    average_point = total_point / EP_GAME_COUNT
    print(f"VS_{label} {average_point:.3f}")


# # VS random
# next_actions = (mcs_action, random_action)
# evaluate_algorithm_of("random", next_actions)

# vs alpha-beta
next_actions = (mcs_action, alpha_beta_action)
evaluate_algorithm_of("alpha-beta", next_actions)

# python -m sandbox._3moku.models.mcs
