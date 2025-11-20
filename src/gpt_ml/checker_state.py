import random

BOARD_SIZE = 6
RED = 1  # 上側
BLUE = -1  # 下側


class State:
    def __init__(self, board=None, turn=RED, turn_count=0):
        """
        board: 6x6 の2次元リスト[int]
        turn: RED(1) or BLUE(-1)
        turn_count: 手数（引き分け判定用に利用）
        """
        if board is None:
            # 初期配置を Pygame版と同じにする
            board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    # 上2段に RED、下2段に BLUE を黒マス((r+c)%2==1)に配置
                    if r < 2 and (r + c) % 2 == 1:
                        board[r][c] = RED  # RED の通常駒
                    elif r > BOARD_SIZE - 3 and (r + c) % 2 == 1:
                        board[r][c] = BLUE  # BLUE の通常駒
        self.board = board
        self.turn = turn
        self.turn_count = turn_count

    # ある色の駒数を数える（通常駒＋キング）
    def piece_count(self, color: int) -> int:
        cnt = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                v = self.board[r][c]
                if v != 0 and (1 if v > 0 else -1) == color:
                    cnt += 1
        return cnt

    # 負け判定：自分の駒がない or 合法手がない
    def is_lose(self) -> bool:
        if self.piece_count(self.turn) == 0:
            return True
        if not self.legal_actions():
            return True
        return False

    # 超単純な引き分け判定（手数が多すぎたら引き分け扱い）
    def is_draw(self) -> bool:
        return self.turn_count >= 50

    # 終局かどうか
    def is_done(self) -> bool:
        return self.is_lose() or self.is_draw()

    # そのマスの駒の移動方向（通常／キング、ジャンプ時の昇格も考慮）
    def _dirs_for_piece(self, piece: int, r: int, jumps: bool = False):
        color = RED if piece > 0 else BLUE
        is_king = abs(piece) == 2

        # ジャンプ探索のときは、最終段に到達していたらキング扱いにする（Pygame版と同じ思想）
        if jumps and not is_king:
            if color == RED and r == BOARD_SIZE - 1:
                is_king = True
            if color == BLUE and r == 0:
                is_king = True

        if is_king:
            # キングは前後左右の斜めに進める
            return [(1, -1), (1, 1), (-1, -1), (-1, 1)]
        if color == RED:
            # RED 通常駒は下方向に1マス
            return [(1, -1), (1, 1)]
        else:
            # BLUE 通常駒は上方向に1マス
            return [(-1, -1), (-1, 1)]

    def _in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    # 多段ジャンプを再帰的に探索
    def _search_jumps(self, start_r, start_c, r, c, piece, captured):
        """
        start_r, start_c: 最初に動かした駒の位置
        r, c: 現在位置
        piece: 駒の種類 (1,2,-1,-2)
        captured: これまでに取った駒の座標リスト
        """
        moves = []
        dirs = self._dirs_for_piece(piece, r, jumps=True)
        extended = False

        for dr, dc in dirs:
            mid_r, mid_c = r + dr, c + dc
            land_r, land_c = r + 2 * dr, c + 2 * dc
            if not (self._in_bounds(mid_r, mid_c) and self._in_bounds(land_r, land_c)):
                continue

            mid_v = self.board[mid_r][mid_c]
            land_v = self.board[land_r][land_c]

            # 間に敵駒がいて、着地マスが空いていて、まだその駒を取っていない
            if (
                land_v == 0
                and mid_v != 0
                and (1 if mid_v > 0 else -1) != (RED if piece > 0 else BLUE)
                and (mid_r, mid_c) not in captured
            ):
                extended = True
                new_captured = captured + [(mid_r, mid_c)]
                # さらに多段ジャンプができるか探索
                moves.extend(
                    self._search_jumps(
                        start_r, start_c, land_r, land_c, piece, new_captured
                    )
                )

        # これ以上ジャンプできない & 何かは既に取っている → ここを終点とするジャンプ手
        if not extended and captured:
            moves.append((start_r, start_c, r, c, captured))

        return moves

    # 1つの駒についての合法手（通常＋ジャンプ）
    def _moves_for_piece(self, r, c):
        piece = self.board[r][c]
        if piece == 0:
            return [], []
        color = RED if piece > 0 else BLUE
        if color != self.turn:
            return [], []

        # 1. ジャンプ手を探索（あれば通常手は無視）
        jumps = self._search_jumps(r, c, r, c, piece, [])
        normals = []

        # 2. ジャンプ手が無いときだけ通常手を生成
        if not jumps:
            for dr, dc in self._dirs_for_piece(piece, r, jumps=False):
                nr, nc = r + dr, c + dc
                if self._in_bounds(nr, nc) and self.board[nr][nc] == 0:
                    normals.append((r, c, nr, nc, []))

        return normals, jumps

    # 現在手番プレイヤーの合法手一覧
    def legal_actions(self):
        all_normals = []
        all_jumps = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                normals, jumps = self._moves_for_piece(r, c)
                all_normals.extend(normals)
                all_jumps.extend(jumps)
        # 取れる手があるときはジャンプ手のみ許可
        return all_jumps if all_jumps else all_normals

    # 次の状態を返す
    def next(self, action):
        """
        action = (from_r, from_c, to_r, to_c, captured_list)
        """
        fr, fc, tr, tc, captured = action

        # 盤面コピー
        new_board = [row[:] for row in self.board]

        # 駒を動かし、取った駒を消す
        piece = new_board[fr][fc]
        new_board[fr][fc] = 0
        for cr, cc in captured:
            new_board[cr][cc] = 0
        new_board[tr][tc] = piece

        # 昇格判定
        color = RED if piece > 0 else BLUE
        if abs(piece) == 1:
            if (color == RED and tr == BOARD_SIZE - 1) or (color == BLUE and tr == 0):
                new_board[tr][tc] = 2 if color == RED else -2

        # 手番交代
        return State(new_board, turn=-self.turn, turn_count=self.turn_count + 1)

    # 先手かどうか（AlphaZero側で使う想定）
    def is_first_player(self):
        return self.turn == RED

    # 文字列表現（デバッグ・確認用）
    def __str__(self):
        symbols = {
            0: ".",
            RED: "r",  # RED 通常
            2: "R",  # RED キング
            BLUE: "b",  # BLUE 通常
            -2: "B",  # BLUE キング
        }
        s = ""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                s += symbols[self.board[r][c]]
            s += "\n"
        s += f"Turn: {'RED' if self.turn == RED else 'BLUE'}\n"
        return s


# プレイヤー入力（番号で手を選ぶ）
def input_action(state: State):
    legal_actions = state.legal_actions()
    if not legal_actions:
        return None

    print("合法手一覧:")
    for i, (fr, fc, tr, tc, captured) in enumerate(legal_actions):
        cap_str = ",".join(f"({r},{c})" for r, c in captured) if captured else "-"
        print(f"{i}: ({fr},{fc}) -> ({tr},{tc}), capture: {cap_str}")

    while True:
        try:
            a = int(input("指したい手の番号を入力してください: "))
        except ValueError:
            print("数字を入力してください。")
            continue

        if 0 <= a < len(legal_actions):
            return legal_actions[a]

        print("その番号の手はありません。")


# ランダム入力
def random_action(state: State):
    legal = state.legal_actions()
    if not legal:
        return None
    return random.choice(legal)


# テスト用のメイン関数
def main():
    # 初期盤面
    state = State()

    while True:
        # 盤面表示
        print(state)

        # ゲーム終了時
        if state.is_done():
            if state.is_lose():
                loser = "RED" if state.turn == RED else "BLUE"
                winner = "BLUE" if loser == "RED" else "RED"
                print(f"{loser} の番で合法手がないので {winner} の勝ちです")
            else:
                print("引き分けです")
            break

        # 行動の取得（ここを input_action(state) に変えれば手入力で遊べます）
        action = random_action(state)
        if action is None:
            print("合法手がありません")
            break

        # 状態の更新
        state = state.next(action)


if __name__ == "__main__":
    main()
