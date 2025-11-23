import pygame
import sys
import random
import json
import asyncio # ① asyncio をインポート
import aiohttp # ② aiohttp をインポート

# 定数定義
BOARD_SIZE = 6
SQUARE_SIZE = 100
WIDTH, HEIGHT = BOARD_SIZE * SQUARE_SIZE, BOARD_SIZE * SQUARE_SIZE
FPS = 30

url = "https://4djo1pd0h8.execute-api.ap-northeast-1.amazonaws.com/action"

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GOLD = (255, 215, 0)
GREEN = (0, 255, 0)


class Piece:
    """駒クラス"""
    # ... (変更なし)
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.king = False

    def make_king(self):
        self.king = True

    def draw(self, win):
        radius = SQUARE_SIZE // 2 - 10
        pygame.draw.circle(
            win,
            self.color,
            (
                self.col * SQUARE_SIZE + SQUARE_SIZE // 2,
                self.row * SQUARE_SIZE + SQUARE_SIZE // 2,
            ),
            radius,
        )
        if self.king:
            pygame.draw.circle(
                win,
                GOLD,
                (
                    self.col * SQUARE_SIZE + SQUARE_SIZE // 2,
                    self.row * SQUARE_SIZE + SQUARE_SIZE // 2,
                ),
                radius // 2,
            )


class Board:
    """盤面クラス"""
    def __init__(self):
        self.board = []
        self.create_board()
        self.red_pieces = 6
        self.blue_pieces = 6
        self.turn_count = 0

    def create_board(self):
        # 盤面の初期化と駒の配置
        for row in range(BOARD_SIZE):
            self.board.append([])
            for col in range(BOARD_SIZE):
                if row < 2 and (row + col) % 2 != 0:
                    self.board[row].append(Piece(row, col, RED))
                elif row > BOARD_SIZE - 3 and (row + col) % 2 != 0:
                    self.board[row].append(Piece(row, col, BLUE))
                else:
                    self.board[row].append(0)

    def draw(self, win):
        # 盤面の描画
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = WHITE if (row + col) % 2 == 0 else BLACK
                pygame.draw.rect(
                    win,
                    color,
                    (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                )
        # 駒の描画
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)
    
    def state(self, current_turn):
        # 盤面の状態を数値化して返す
        board_state = []
        if self.turn_count != 0:
            for i in range(BOARD_SIZE):
                row_state = []
                for j in range(BOARD_SIZE):
                    piece = self.board[i][j]
                    if piece != 0:
                        if piece.color == RED:
                            value = 2 if piece.king else 1
                        else:
                            value = -2 if piece.king else -1
                    else:
                        value = 0
                    row_state.append(value)
                board_state.append(row_state)
        else:
            # 初期盤面（turn_count が 0 のとき）
            board_state = [
                [0, 1, 0, 1, 0, 1],
                [1, 0, 1, 0, 1, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, -1, 0, -1, 0, -1],
                [-1, 0, -1, 0, -1, 0],
            ]

        state = {
            "board": board_state,
            "turn": 1 if current_turn == RED else -1,
            "turn_count": self.turn_count,
        }
        return state


    def move_piece(self, piece, row, col):
        # 駒の移動
        self.board[piece.row][piece.col] = 0
        piece.row = row
        piece.col = col
        self.board[row][col] = piece

        self.turn_count += 1

        # キングへの昇格判定
        if (piece.color == RED and row == BOARD_SIZE - 1) or (
            piece.color == BLUE and row == 0
        ):
            piece.make_king()

    def remove_piece(self, pieces):
        # 駒の除去（取られた駒）
        for piece in pieces:
            if piece.color == RED:
                self.red_pieces -= 1
            else:
                self.blue_pieces -= 1
            self.board[piece.row][piece.col] = 0

    def get_piece(self, row, col):
        # 特定の座標の駒を取得
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return self.board[row][col]
        return 0

    # 指定された色のすべての有効な移動を取得
    def get_all_valid_moves(self, color):
        all_moves = {}
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != 0 and piece.color == color:
                    moves = self.get_valid_moves(piece)
                    if moves:
                        all_moves[piece] = moves
        return all_moves

    def get_valid_moves(self, piece):
        """有効な移動先を取得。ジャンプ可能な場合はジャンプのみを返す。"""
        moves = {}
        all_jumps = self._find_jumps(piece, piece.row, piece.col, [], False)

        if all_jumps:
            return all_jumps

        if piece.color == RED or piece.king:
            moves.update(self._get_normal_moves(piece, 1))
        if piece.color == BLUE or piece.king:
            moves.update(self._get_normal_moves(piece, -1))

        return moves

    def _get_normal_moves(self, piece, step):
        """通常移動（1マス移動）を取得"""
        moves = {}
        r = piece.row + step

        if not (0 <= r < BOARD_SIZE):
            return moves

        c_left = piece.col - 1
        if c_left >= 0 and self.board[r][c_left] == 0:
            moves[(r, c_left)] = []

        c_right = piece.col + 1
        if c_right < BOARD_SIZE and self.board[r][c_right] == 0:
            moves[(r, c_right)] = []

        return moves

    def _find_jumps(self, piece, r, c, skipped, forced_king):
        """再帰的に多段ジャンプのパスを探索する"""
        jumps = {}
        temp_king = (
            piece.king
            or forced_king
            or (piece.color == RED and r == BOARD_SIZE - 1)
            or (piece.color == BLUE and r == 0)
        )

        if piece.color == RED or temp_king:
            self._check_jump_direction(piece, r, c, 1, skipped, jumps, temp_king)

        if piece.color == BLUE or temp_king:
            self._check_jump_direction(piece, r, c, -1, skipped, jumps, temp_king)

        return jumps

    def _check_jump_direction(self, piece, r, c, step, skipped, jumps, temp_king):
        """特定の方向（step）へのジャンプをチェックし、再帰的に多段ジャンプを探索"""
        next_r = r + step * 2

        if not (0 <= next_r < BOARD_SIZE):
            return

        # 左ジャンプ
        skipped_r_left = r + step
        skipped_c_left = c - 1
        next_c_left = c - 2

        if next_c_left >= 0 and self.board[next_r][next_c_left] == 0:
            skipped_piece = self.board[skipped_r_left][skipped_c_left]
            if (
                skipped_piece != 0
                and skipped_piece.color != piece.color
                and skipped_piece not in skipped
            ):
                new_skipped = skipped + [skipped_piece]
                jumps[(next_r, next_c_left)] = new_skipped

                recursive_jumps = self._find_jumps(
                    piece, next_r, next_c_left, new_skipped, temp_king
                )
                jumps.update(recursive_jumps)

        # 右ジャンプ
        skipped_r_right = r + step
        skipped_c_right = c + 1
        next_c_right = c + 2

        if next_c_right < BOARD_SIZE and self.board[next_r][next_c_right] == 0:
            skipped_piece = self.board[skipped_r_right][skipped_c_right]
            if (
                skipped_piece != 0
                and skipped_piece.color != piece.color
                and skipped_piece not in skipped
            ):
                new_skipped = skipped + [skipped_piece]
                jumps[(next_r, next_c_right)] = new_skipped

                recursive_jumps = self._find_jumps(
                    piece, next_r, next_c_right, new_skipped, temp_king
                )
                jumps.update(recursive_jumps)


class Game:
    """ゲーム管理クラス"""

    def __init__(self, win):
        self.win = win
        self.board = Board()
        self.turn = random.choice([RED, BLUE])
        self.selected_piece = None
        self.valid_moves = {}
        pygame.font.init()
        self.font_small = pygame.font.SysFont("meiryo", 30)
        self.font_large = pygame.font.SysFont("meiryo", 40, bold=True)
        self.game_over = False
        self.game_over_time = None
        self.AI_data = None
        # ③ API 実行中フラグを追加
        self.api_in_progress = False 

    def update(self):
        self.board.draw(self.win)
        self.draw_valid_moves(self.valid_moves)

        if not self.game_over:
            self.display_turn()
        else:
            self.display_winner()

        pygame.display.flip()

    def display_turn(self):
        """現在の手番を画面に表示する"""
        turn_color_name = "赤 (RED)" if self.turn == RED else "青 (BLUE)"
        # API 通信中は表示を変更
        if self.turn == RED and self.api_in_progress:
             turn_color_name += " (AI思考中...)"
        
        text_surface = self.font_small.render(
            f"現在の手番: {turn_color_name}", True, self.turn
        )
        self.win.blit(text_surface, (10, 10))

    def display_winner(self):
        """勝者を画面中央に表示する"""
        # ... (変更なし、描画ロジックは省略)
        winner_name = self.winner()
        if winner_name:
            lines = winner_name.split("\n")
            color = BLUE if "青" in winner_name else RED

            text_surfaces = [
                self.font_large.render(line, True, color) for line in lines
            ]

            total_height = sum(surface.get_height() for surface in text_surfaces)
            max_width = max(surface.get_width() for surface in text_surfaces)

            padding = 40
            rect_width = max_width + padding
            rect_height = total_height + (len(lines) - 1) * 10 + padding

            center_x = WIDTH // 2
            center_y = HEIGHT // 2

            s = pygame.Surface((rect_width, rect_height))
            s.set_alpha(200)
            s.fill(BLACK)
            self.win.blit(s, (center_x - rect_width // 2, center_y - rect_height // 2))

            current_y = center_y - total_height // 2 - (len(lines) - 1) * 5

            for surface in text_surfaces:
                text_rect = surface.get_rect(
                    center=(center_x, current_y + surface.get_height() // 2)
                )
                self.win.blit(surface, text_rect)
                current_y += surface.get_height() + 10

    def draw_valid_moves(self, moves):
        # 有効な移動先マスを緑でハイライト
        for move in moves:
            row, col = move
            center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
            pygame.draw.circle(self.win, GREEN, (center_x, center_y), 15)

    def select(self, row, col):
        if self.game_over:
            return False

        # 既に駒が選択されている場合 (→ 移動を試みる)
        if self.selected_piece:
            result = self._move(row, col)
            if not result:
                self.selected_piece = None
                self.valid_moves = {}
                return self.select(row, col)

        # 駒が選択されていない場合 (→ 駒の選択を試みる)
        else:
            piece = self.board.get_piece(row, col)
            if piece != 0 and piece.color == self.turn:
                self.selected_piece = piece
                self.valid_moves = self.board.get_valid_moves(piece)
                return True

        return False
    
    def play_AI(self):
        # AIのターンではない、ゲーム終了、データがない、または API 実行中の場合は終了
        if self.turn == BLUE or self.game_over or not self.AI_data or self.api_in_progress:
            return False
        
        try:
            action = self.AI_data['action']
            
            selected_row, selected_col = action["selected_piece"]
            move_row, move_col = action["move_to"]
            
            # 1. 選択処理
            # select は、そのマスに駒があり、有効な移動先がある場合に self.selected_piece と self.valid_moves を設定
            if self.select(selected_row, selected_col):
                
                # 2. 移動処理
                if self._move(move_row, move_col):
                    # 動作成功後、AI_data をクリア
                    self.AI_data = None 
                    return True
                
        except KeyError as e:
            print(f"AIアクション実行エラー: JSONキー {e} が見つかりません。")
        except Exception as e:
            print(f"AIアクション実行中に予期せぬエラーが発生しました: {e}")

        return False

    def _move(self, row, col):
        if (row, col) in self.valid_moves:
            piece_to_move = self.selected_piece

            # 駒の移動を実行
            self.board.move_piece(piece_to_move, row, col)

            # 取る駒がある場合は除去
            skipped = self.valid_moves[(row, col)]
            if skipped:
                self.board.remove_piece(skipped) 

            self.change_turn()

            if self.winner():
                self.game_over = True
                self.game_over_time = pygame.time.get_ticks()

            # ④ ターンが変わり、次のプレイヤーが赤（AI）の場合は API 呼び出しタスクをスケジュール
            if self.turn == RED and not self.game_over and not self.api_in_progress:
                # asyncio.get_event_loop() はグローバルループを取得
                # create_task は非同期関数をすぐに実行せずにタスクとしてスケジュールする
                loop = asyncio.get_event_loop()
                loop.create_task(self._async_fetch_ai_data())

            return True
        return False

    def change_turn(self):
        self.selected_piece = None
        self.valid_moves = {}
        self.turn = BLUE if self.turn == RED else RED

        if not self.game_over and self.winner():
            self.game_over = True
            self.game_over_time = pygame.time.get_ticks()

    def winner(self):
        # ... (変更なし)
        if self.board.red_pieces == 0:
            return "青 (BLUE) の勝利！"
        elif self.board.blue_pieces == 0:
            return "赤 (RED) の勝利！"

        current_player_moves = self.board.get_all_valid_moves(self.turn)

        if not current_player_moves:
            if self.turn == RED:
                return "青 (BLUE) の勝利！\n(赤は動けません) "
            else:
                return "赤 (RED) の勝利！\n(青は動けません) "

        return None
    
    # ⑤ 非同期 API 呼び出し関数
    async def _async_fetch_ai_data(self):
        """非同期で AI の次の手を API から取得し、self.AI_data に保存する"""
        
        if self.game_over or self.turn != RED or self.api_in_progress:
            return

        self.api_in_progress = True # API 実行開始
        print("AI思考開始: 盤面状態を送信中...")
        
        # aiohttp のクライアントセッションを使用
        async with aiohttp.ClientSession() as session:
            try:
                # post メソッドは非同期なので await が必要
                async with session.post(url, json=self.board.state(self.turn)) as res:
                    
                    # status が 200 でない場合はエラー
                    if res.status != 200:
                        print(f"APIエラー: Status Code {res.status}")
                        return
                        
                    # json() メソッドも非同期なので await が必要
                    AI_data = await res.json()
                    
                    self.AI_data = AI_data
                    
                    AI_selected_piece = self.AI_data['action']['selected_piece']
                    AI_move_to = self.AI_data['action']['move_to']
                    print(f"AIレスポンス取得完了。次の一手: {AI_selected_piece} -> {AI_move_to}")

            except aiohttp.ClientError as e:
                print(f"API通信エラー: {e}")
            except KeyError as e:
                print(f"AIレスポンスのJSON解析エラー: キー {e} がありません。")
            except Exception as e:
                print(f"予期せぬエラー: {e}")
            finally:
                self.api_in_progress = False # API 実行終了

# ⑥ Pygame と asyncio を統合するためのメイン関数
async def main():
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("6x6 チェッカー (Async)")
    clock = pygame.time.Clock()

    game = Game(win)
    running = True

    # 最初のターンが赤（AI）の場合、API 呼び出しを開始
    if game.turn == RED:
        await game._async_fetch_ai_data() # await で非同期関数を待機 (初期ターンのみ)
    else:
        print(f"最初のターンは青（人間）です。")


    while running:
        # 非同期タスクの実行を許可するため、一定時間 sleep する
        await asyncio.sleep(0) 

        # Pygame イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
                if game.turn == BLUE and not game.api_in_progress: # API 実行中は人間の操作を無視
                    x, y = pygame.mouse.get_pos()
                    row = y // SQUARE_SIZE
                    col = x // SQUARE_SIZE
                    game.select(row, col)

        # AI 動作の実行
        # API 実行中でなく、AIデータがあり、AIのターンであれば実行
        if not game.game_over and game.turn == RED and game.AI_data and not game.api_in_progress:
            game.play_AI()

        # ゲームオーバー判定
        if game.game_over and game.game_over_time is not None:
            if pygame.time.get_ticks() - game.game_over_time >= 3000:
                running = False

        game.update()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    # ⑦ プログラムのエントリポイント
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass