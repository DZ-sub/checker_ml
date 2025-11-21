# from src.game.checker import

BOARD_SIZE = 6


class CheckerState:
    def __init__(self, pieces=None, enemy_pieces=None):
        # 自分の盤面: [[row][col]]
        self.pieces = [
            pieces if pieces is not None else [0] * BOARD_SIZE
            for _ in range(BOARD_SIZE)
        ]
        # 敵の盤面
        self.enemy_pieces = [
            enemy_pieces if enemy_pieces is not None else [0] * BOARD_SIZE
            for _ in range(BOARD_SIZE)
        ]

    # 駒の数の取得
    def piece_count(self, pieces):
        count = 0
        for row in pieces:
            for p in row:
                if p == 1:
                    count += 1
        return count

    # 負けかどうか
    def is_lose(self):
        """
        負け条件： 自分の駒が0になる or 合法手がなくなる
        """
        # 自分の駒が0の場合
        if self.piece_count(self.pieces) == 0:
            return True
        # 合法手がない場合
        if not self.legal_actions():
            return True
        return False


state = CheckerState()
print(state.pieces)
