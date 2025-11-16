import pygame
import sys
import random # ランダム機能を追加

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
GOLD = (255, 215, 0) 
GREEN = (0, 255, 0)
YELLOW=(255, 255, 0)

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
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = WHITE if (row + col) % 2 == 0 else BLACK
                pygame.draw.rect(win, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def move_piece(self, piece, row, col):
        self.board[piece.row][piece.col] = 0
        piece.row = row
        piece.col = col
        self.board[row][col] = piece
        
        if (piece.color == RED and row == BOARD_SIZE - 1) or \
           (piece.color == BLUE and row == 0):
            piece.make_king()

    def remove_piece(self, pieces):
        for piece in pieces:
            if piece.color == RED:
                self.red_pieces -= 1
            else:
                self.blue_pieces -= 1
            self.board[piece.row][piece.col] = 0

    def get_piece(self, row, col):
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
             return self.board[row][col]
        return 0

    def get_valid_moves(self, piece):
        moves = {}
        
        # 1. ジャンプ移動の探索 (多段ジャンプを含む)
        all_jumps = self._find_jumps(piece, piece.row, piece.col, [], False)
        
        if all_jumps:
            return all_jumps
            
        # 2. 通常移動の探索 (ジャンプがない場合のみ)
        if piece.color == RED or piece.king:
            moves.update(self._get_normal_moves(piece, 1)) # 前進
            
        if piece.color == BLUE or piece.king:
            moves.update(self._get_normal_moves(piece, -1)) # 後退

        return moves

    def _get_normal_moves(self, piece, step):
        moves = {}
        r = piece.row + step
        
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
        jumps = {}
        temp_king = piece.king or forced_king or \
            (piece.color == RED and r == BOARD_SIZE - 1) or \
            (piece.color == BLUE and r == 0)

        if piece.color == RED or temp_king:
            self._check_jump_direction(piece, r, c, 1, skipped, jumps, temp_king)

        if piece.color == BLUE or temp_king:
            self._check_jump_direction(piece, r, c, -1, skipped, jumps, temp_king)

        return jumps

    def _check_jump_direction(self, piece, r, c, step, skipped, jumps, temp_king):
        next_r = r + step * 2
        
        if not (0 <= next_r < BOARD_SIZE):
            return

        # 左ジャンプ
        skipped_r_left = r + step
        skipped_c_left = c - 1
        next_c_left = c - 2
        
        if next_c_left >= 0 and self.board[next_r][next_c_left] == 0:
            skipped_piece = self.board[skipped_r_left][skipped_c_left]
            if skipped_piece != 0 and skipped_piece.color != piece.color and skipped_piece not in skipped:
                new_skipped = skipped + [skipped_piece]
                jumps[(next_r, next_c_left)] = new_skipped
                
                recursive_jumps = self._find_jumps(piece, next_r, next_c_left, new_skipped, temp_king)
                jumps.update(recursive_jumps)

        # 右ジャンプ
        skipped_r_right = r + step
        skipped_c_right = c + 1
        next_c_right = c + 2

        if next_c_right < BOARD_SIZE and self.board[next_r][next_c_right] == 0:
            skipped_piece = self.board[skipped_r_right][skipped_c_right]
            if skipped_piece != 0 and skipped_piece.color != piece.color and skipped_piece not in skipped:
                new_skipped = skipped + [skipped_piece]
                jumps[(next_r, next_c_right)] = new_skipped
                
                recursive_jumps = self._find_jumps(piece, next_r, next_c_right, new_skipped, temp_king)
                jumps.update(recursive_jumps)

class Game:
    """ゲーム管理クラス"""
    def __init__(self, win):
        self.win = win
        self.board = Board()
        # 先手後手をランダムに決定
        self.turn = random.choice([RED, BLUE]) 
        self.selected_piece = None
        self.valid_moves = {}
        # フォントの初期化
        pygame.font.init()
        self.font_small = pygame.font.SysFont('meiryo', 30) # 手番表示用
        self.font_large = pygame.font.SysFont('meiryo', 60, bold=True) # 勝利メッセージ用
        self.game_over = False

    def update(self):
        self.board.draw(self.win)
        self.draw_valid_moves(self.valid_moves)
        
        if not self.game_over:
            self.display_turn() # 手番を表示
        else:
            self.display_winner() # 勝利メッセージを表示

        pygame.display.flip()

    def display_turn(self):
        """現在の手番を画面に表示する"""
        turn_color_name = "赤 (RED)" if self.turn == RED else "青 (BLUE)"
        text_surface = self.font_small.render(f'現在の手番: {turn_color_name}', True, self.turn)
        self.win.blit(text_surface, (10, 10)) # 左上隅に表示

    def display_winner(self):
        """勝者を画面中央に表示する"""
        winner_name = self.winner()
        if winner_name:
            # 勝利メッセージ
            text = winner_name
            color = BLUE if "BLUE" in winner_name else RED
            
            text_surface = self.font_large.render(text, True, color)
            
            # 画面中央に配置
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            
            # メッセージの背景として半透明の矩形を描画 (オプション)
            s = pygame.Surface((text_rect.width + 40, text_rect.height + 40))
            s.set_alpha(200) # 透明度 (0-255)
            s.fill(BLACK)
            self.win.blit(s, (text_rect.x - 20, text_rect.y - 20))
            
            # メッセージ本体を描画
            self.win.blit(text_surface, text_rect)


    def draw_valid_moves(self, moves):
        for move in moves:
            row, col = move
            center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
            pygame.draw.circle(self.win, GREEN, (center_x, center_y), 15)

    def select(self, row, col):
        if self.game_over:
            return False
            
        if self.selected_piece:
            result = self._move(row, col)
            if not result:
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
            self.board.move_piece(piece_to_move, row, col) 
            
            skipped = self.valid_moves[(row, col)]
            if skipped:
                self.board.remove_piece(skipped)
                
            self.change_turn()
            
            if self.winner():
                self.game_over = True
            
            return True
        return False

    def change_turn(self):
        self.selected_piece = None
        self.valid_moves = {}
        self.turn = BLUE if self.turn == RED else RED

    def winner(self):
        if self.board.red_pieces == 0:
            return "青 (BLUE) の勝利！"
        elif self.board.blue_pieces == 0:
            return "赤 (RED) の勝利！"
        return None

# Pygame初期化
pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("6x6 チェッカー")
clock = pygame.time.Clock()

game = Game(win)

# メインループ
running = True
while running:
    clock.tick(FPS)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
            x, y = pygame.mouse.get_pos()
            row = y // SQUARE_SIZE
            col = x // SQUARE_SIZE
            game.select(row, col)
            
        # ゲーム終了後にキーを押すと終了
        if game.game_over and event.type == pygame.KEYDOWN:
             running = False

    game.update()

pygame.quit()
sys.exit()