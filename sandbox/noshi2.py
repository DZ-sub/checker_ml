import pygame
import sys

# 定数定義
BOARD_SIZE = 6
SQUARE_SIZE = 100
WIDTH, HEIGHT = BOARD_SIZE * SQUARE_SIZE, BOARD_SIZE * SQUARE_SIZE
FPS = 30

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GOLD = (255, 215, 0) # キング駒の色

class Piece:
    """駒クラス"""
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.king = False

    def make_king(self):
        self.king = True

    def draw(self, win):
        radius = SQUARE_SIZE // 2 - 10
        pygame.draw.circle(win, self.color, (self.col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                             self.row * SQUARE_SIZE + SQUARE_SIZE // 2), radius)
        if self.king:
            pygame.draw.circle(win, GOLD, (self.col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                           self.row * SQUARE_SIZE + SQUARE_SIZE // 2), radius // 2)

class Board:
    """盤面クラス"""
    def __init__(self):
        self.board = []
        self.create_board()
        self.red_pieces = 6
        self.blue_pieces = 6

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
                pygame.draw.rect(win, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        # 駒の描画
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def move_piece(self, piece, row, col):
        # 駒の移動
        self.board[piece.row][piece.col] = 0
        piece.row = row
        piece.col = col
        self.board[row][col] = piece
        
        # キングへの昇格判定
        if (piece.color == RED and row == BOARD_SIZE - 1) or \
           (piece.color == BLUE and row == 0):
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

    def get_valid_moves(self, piece):
        """有効な移動先を取得。ジャンプ可能な場合はジャンプのみを返す。"""
        moves = {}
        
        # 1. ジャンプ移動の探索 (多段ジャンプを含む)
        # piece.row, piece.col: 現在の駒の位置
        # []: これまで取った駒のリスト
        # False: 最初の移動であるため、キングへの昇格チェックをスキップしない
        all_jumps = self._find_jumps(piece, piece.row, piece.col, [], False)
        
        # ジャンプ可能な移動が見つかった場合、通常移動は不可
        if all_jumps:
            return all_jumps
            
        # 2. 通常移動の探索 (ジャンプがない場合のみ)
        
        # RED駒（通常前進）またはキング駒（前進・後退）
        if piece.color == RED or piece.king:
            moves.update(self._get_normal_moves(piece, 1)) # 前進
            
        if piece.color == BLUE or piece.king:
            moves.update(self._get_normal_moves(piece, -1)) # 後退

        return moves

    def _get_normal_moves(self, piece, step):
        """通常移動（1マス移動）を取得"""
        moves = {}
        r = piece.row + step
        
        # 盤面の境界チェック
        if not (0 <= r < BOARD_SIZE):
            return moves

        # 左移動
        c_left = piece.col - 1
        if c_left >= 0 and self.board[r][c_left] == 0:
            moves[(r, c_left)] = []
            
        # 右移動
        c_right = piece.col + 1
        if c_right < BOARD_SIZE and self.board[r][c_right] == 0:
            moves[(r, c_right)] = []
            
        return moves

    def _find_jumps(self, piece, r, c, skipped, forced_king):
        """再帰的に多段ジャンプのパスを探索する"""
        jumps = {}
        # キングの昇格を一時的にシミュレート
        temp_king = piece.king or forced_king or \
            (piece.color == RED and r == BOARD_SIZE - 1) or \
            (piece.color == BLUE and r == 0)

        # RED駒（前進）またはキング駒
        if piece.color == RED or temp_king:
            self._check_jump_direction(piece, r, c, 1, skipped, jumps, temp_king)

        # BLUE駒（後退）またはキング駒
        if piece.color == BLUE or temp_king:
            self._check_jump_direction(piece, r, c, -1, skipped, jumps, temp_king)

        return jumps

    def _check_jump_direction(self, piece, r, c, step, skipped, jumps, temp_king):
        """特定の方向（step）へのジャンプをチェックし、再帰的に多段ジャンプを探索"""
        next_r = r + step * 2
        
        # 盤面の境界チェック
        if not (0 <= next_r < BOARD_SIZE):
            return

        # 左ジャンプ
        skipped_r_left = r + step
        skipped_c_left = c - 1
        next_c_left = c - 2
        
        if next_c_left >= 0 and self.board[next_r][next_c_left] == 0:
            skipped_piece = self.board[skipped_r_left][skipped_c_left]
            # 相手の駒があり、まだ取っていない場合
            if skipped_piece != 0 and skipped_piece.color != piece.color and skipped_piece not in skipped:
                new_skipped = skipped + [skipped_piece]
                # ジャンプを記録
                jumps[(next_r, next_c_left)] = new_skipped
                
                # 多段ジャンプの継続探索 (強制キングは次の再帰で昇格状態を維持するためTrueを渡す)
                # 注: 厳密には、多段ジャンプ中はキングになってもすぐに後退移動はできないルールもあるが、ここではシンプルに許可する。
                recursive_jumps = self._find_jumps(piece, next_r, next_c_left, new_skipped, temp_king)
                jumps.update(recursive_jumps)

        # 右ジャンプ
        skipped_r_right = r + step
        skipped_c_right = c + 1
        next_c_right = c + 2

        if next_c_right < BOARD_SIZE and self.board[next_r][next_c_right] == 0:
            skipped_piece = self.board[skipped_r_right][skipped_c_right]
            # 相手の駒があり、まだ取っていない場合
            if skipped_piece != 0 and skipped_piece.color != piece.color and skipped_piece not in skipped:
                new_skipped = skipped + [skipped_piece]
                # ジャンプを記録
                jumps[(next_r, next_c_right)] = new_skipped
                
                # 多段ジャンプの継続探索
                recursive_jumps = self._find_jumps(piece, next_r, next_c_right, new_skipped, temp_king)
                jumps.update(recursive_jumps)

class Game:
    """ゲーム管理クラス"""
    def __init__(self, win):
        self.win = win
        self.board = Board()
        self.turn = RED
        self.selected_piece = None
        self.valid_moves = {}

    def update(self):
        self.board.draw(self.win)
        self.draw_valid_moves(self.valid_moves)
        pygame.display.flip()

    def draw_valid_moves(self, moves):
        # 有効な移動先マスを緑でハイライト
        GREEN = (0, 255, 0)
        for move in moves:
            row, col = move
            center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
            pygame.draw.circle(self.win, GREEN, (center_x, center_y), 15)


    def select(self, row, col):
        if self.selected_piece:
            result = self._move(row, col)
            if not result:
                # 移動失敗時は、選択を解除し、新しくクリックしたマスを選択し直す
                self.selected_piece = None
                self.valid_moves = {}
                return self.select(row, col)
            
        else:
            piece = self.board.get_piece(row, col)
            if piece != 0 and piece.color == self.turn:
                self.selected_piece = piece
                self.valid_moves = self.board.get_valid_moves(piece)
                return True
        
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
            return True
        return False

    def change_turn(self):
        self.selected_piece = None
        self.valid_moves = {}
        self.turn = BLUE if self.turn == RED else RED

    def winner(self):
        # Boardクラスでカウントするように変更
        if self.board.red_pieces == 0:
            return "BLUEの勝利"
        elif self.board.blue_pieces == 0:
            return "REDの勝利"
        return None

# Pygame初期化
pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("6x6 チェッカー 多段ジャンプ対応版")
clock = pygame.time.Clock()

game = Game(win)

# メインループ
running = True
while running:
    clock.tick(FPS)

    winner = game.winner()
    if winner:
        print(winner)
        pygame.time.wait(3000) 
        running = False
        break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            row = y // SQUARE_SIZE
            col = x // SQUARE_SIZE
            game.select(row, col)

    game.update()

pygame.quit()
sys.exit()