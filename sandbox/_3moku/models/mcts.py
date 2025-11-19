# モンテカルロ木探索

import math

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


# MCTSの行動選択
def mcts_action(state: State):
    # MCTSのノード定義
    class Node:
        def __init__(self, state: State):
            self.state = state  # ゲームの状態
            self.w = 0  # 累計価値
            self.n = 0  # 試行回数
            self.child_nodes = None  # 子ノードのリスト

        # 局面の価値の計算
        def evaluate(self):
            # ゲーム終了時
            if self.state.is_done():
                # 勝敗結果の価値
                value = -1 if self.state.is_lose() else 0

                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1
                return value

            # 子ノードが存在しない時
            if not self.child_nodes:
                # プレイアウトで価値を取得
                value = playout(self.state)
                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1
                # ノードの展開
                if self.n == 10:
                    self.expand()
                return value
            # 子ノードが存在する時
            else:
                # UCB1が最大の子ノードの評価で価値を取得
                value = -self.next_child_node().evaluate()
                # 累計価値と試行回数の更新
                self.w += value
                self.n += 1
                return value

        # 子ノードの展開
        def expand(self):
            legal_actions = self.state.legal_actions()
            self.child_nodes = []
            for action in legal_actions:
                next_state = self.state.next(action)
                self.child_nodes.append(Node(next_state))

        # UCB1が最大の子ノードの取得
        def next_child_node(self):
            # 試行回数が0の子ノードを返す
            for child_node in self.child_nodes:
                if child_node.n == 0:
                    return child_node
            # UCB1の計算
            t = 0
            for c in self.child_nodes:
                t += c.n
            ucb1_values = []
            for child_node in self.child_nodes:
                ucb1 = (
                    -child_node.w / child_node.n
                    + (2 * math.log(t) / child_node.n) ** 0.5
                )
                ucb1_values.append(ucb1)
            # UCB1が最大の子ノードを返す
            return self.child_nodes[argmax(ucb1_values)]

    # 現在の局面のノード作成
    root_node = Node(state)
    root_node.expand()

    # MCTSの試行回数
    N_SIMULATION = 100
    for _ in range(N_SIMULATION):
        root_node.evaluate()

    # 試行回数の最大値を持つ行動を返す
    legal_actions = state.legal_actions()
    n_list = []
    for c in root_node.child_nodes:
        n_list.append(c.n)
    return legal_actions[argmax(n_list)]


# モンテカルロ木探索のアルゴリズム評価
if __name__ == "__main__":
    # # vs random
    # next_actions = (mcts_action, random_action)
    # evaluate_algorithm_of("random", next_actions)

    # vs alpha-beta
    next_actions = (mcts_action, alpha_beta_action)
    evaluate_algorithm_of("alpha-beta", next_actions)

# python -m sandbox._3moku.models.mcts
