import random


# ゲーム状態
class State:
    def __init__(self, pieces=None, enemy_pieces=None):
        # 石の配置
        self.pieces = pieces if pieces != None else [0] * 9
        self.enemy_pieces = enemy_pieces if enemy_pieces != None else [0] * 9

    # 石の数の取得
    def piece_count(self, pieces):
        count = 0
        for p in pieces:
            if p == 1:
                count += 1
        return count

    # 負けかどうか
    def is_lose(self):
        # 敵が3並びかどうか
        def is_comp(x, y, dx, dy):
            """
            x: 開始位置のx座標
            y: 開始位置のy座標
            dx: x方向の増分
            dy: y方向の増分
            """
            for k in range(3):  # 3マス分見る
                # y座標の範囲外チェック
                if y < 0 or 2 < y:
                    return False
                # x座標の範囲外チェック
                if x < 0 or 2 < x:
                    return False
                # 敵の意思があるかチェック
                if self.enemy_pieces[x + y * 3] == 0:  # (3*3の1次元配列なのでx + y * 3)
                    return False
                x, y = x + dx, y + dy
            return True

        # 負けの判定
        # 斜め
        if is_comp(0, 0, 1, 1) or is_comp(0, 2, 1, -1):
            return True
        # 横 と 縦
        for i in range(3):
            if is_comp(0, i, 1, 0) or is_comp(i, 0, 0, 1):
                return True
        return False

    # 引き分けかどうか
    def is_draw(self):
        """
        石が合計で9個置かれているか判定する
        """
        return self.piece_count(self.pieces) + self.piece_count(self.enemy_pieces) == 9

    # ゲーム終了かどうか
    def is_done(self):
        return self.is_lose() or self.is_draw()

    # 次の状態を取得
    def next(self, action):
        """
        action: 置く位置 (0~8)
        置いた後の状態のStateを新たに生成して返す
        """
        pieces = self.pieces.copy()
        pieces[action] = 1
        # 状態を再帰的に更新する
        return State(self.enemy_pieces, pieces)

    # 合法手のリストの取得
    def legal_actions(self):
        actions = []
        for i in range(9):
            # まだ置かれていない場所を追加
            if self.pieces[i] == 0 and self.enemy_pieces[i] == 0:
                actions.append(i)
        return actions

    # 先手かどうか
    def is_first_player(self):
        # 置かれている石の数が同じなら先手
        return self.piece_count(self.pieces) == self.piece_count(self.enemy_pieces)

    # 文字列表記
    def __str__(self):
        ox = ("o", "x") if self.is_first_player() else ("x", "o")
        str = ""
        for i in range(9):
            if self.pieces[i] == 1:
                str += ox[0]
            elif self.enemy_pieces[i] == 1:
                str += ox[1]
            else:
                str += "-"
            if i % 3 == 2:
                str += "\n"
        return str


# プレイヤー入力
def input_action(state: State):
    legal_actions = state.legal_actions()
    while True:
        a = int(input(f"{legal_actions}の数字を入力: "))
        if a not in legal_actions:
            print("置けない場所")
            continue
        return a


# ランダム入力
def random_action(state: State):
    legal_actions = state.legal_actions()
    return legal_actions[random.randint(0, len(legal_actions) - 1)]


# テスト用のメイン関数
def main():

    # 初期盤面
    state = State()
    while True:
        # ゲーム終了時
        if state.is_done():
            break
        # 行動の取得
        action = random_action(state)
        # 状態の更新
        state = state.next(action)
        # 表示
        print(state)


if __name__ == "__main__":
    main()
