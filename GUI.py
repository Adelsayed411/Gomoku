#====== بسم الله الرحمن الرحيم ======
import tkinter as tk
from tkinter import messagebox, ttk
import math
import random
import copy
import threading
import queue
from PIL import Image, ImageTk
import os

# ======== Game Settings ========
BOARD_SIZE = 15
WIN_COUNT = 5
EMPTY = "."
HUMAN = "X"
AI_MINIMAX = "O"
AI_ALPHABETA = "A"
MAX_DEPTH = 2
LAST_MOVE_COLOR = "yellow"
SCORE_WIN = 1000000
SCORE_OPEN_FOUR = 100000
SCORE_SEMI_FOUR = 10000
SCORE_OPEN_THREE = 1000
SCORE_SEMI_THREE = 100
SCORE_OPEN_TWO = 50
SCORE_SEMI_TWO = 10
SCORE_OPEN_ONE = 1
MOVE_SEARCH_RADIUS = 2

# ======== Game Logic (Unchanged) ========
def create_board():
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def is_valid_move(board, r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY

def check_win(board, player):
    if player == EMPTY: return False, None
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                for dr, dc in directions:
                    count = 0
                    win_line = []
                    for i in range(WIN_COUNT):
                        rr, cc = r + dr * i, c + dc * i
                        if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == player:
                            count += 1
                            win_line.append((rr, cc))
                        else:
                            break
                    if count == WIN_COUNT:
                        return True, win_line
    return False, None

def is_board_full(board):
    return all(cell != EMPTY for row in board for cell in row)

def terminal_test(board, depth, player_ai, opponent_in_game):
    win_ai, _ = check_win(board, player_ai)
    win_opponent, _ = check_win(board, opponent_in_game)
    return depth == 0 or win_ai or win_opponent or is_board_full(board)

def evaluate_line(line, player_ai, opponent_in_game):
    score = 0
    line_str = "".join(line)
    player_char = player_ai
    opponent_char = opponent_in_game
    empty_char = EMPTY
    n = len(line)

    if player_char * WIN_COUNT in line_str:
        return SCORE_WIN
    if opponent_char * WIN_COUNT in line_str:
        return -SCORE_WIN

    def get_pattern_score(current_player, current_opponent):
        pat_score = 0
        for start in range(n - WIN_COUNT + 1):
            segment = line[start : start + WIN_COUNT]
            segment_str = "".join(segment)
            player_count = segment_str.count(current_player)
            opponent_count = segment_str.count(current_opponent)
            empty_count = segment_str.count(empty_char)

            if opponent_count > 0 or player_count + empty_count != WIN_COUNT:
                continue

            left_boundary = EMPTY if start == 0 else line[start - 1]
            right_boundary = EMPTY if start + WIN_COUNT == n else line[start + WIN_COUNT]
            is_open_left = (left_boundary == EMPTY)
            is_open_right = (right_boundary == EMPTY)
            is_blocked_left = (left_boundary == current_opponent) or (start == 0)
            is_blocked_right = (right_boundary == current_opponent) or (start + WIN_COUNT == n)

            if player_count == 5:
                pat_score += SCORE_WIN
            elif player_count == 4:
                if is_open_left and is_open_right:
                    pat_score += SCORE_OPEN_FOUR
                elif (is_open_left and is_blocked_right) or (is_blocked_left and is_open_right):
                    pat_score += SCORE_SEMI_FOUR
            elif player_count == 3 and empty_count == 2:
                if current_player * 3 in segment_str:
                    if is_open_left and is_open_right:
                        pat_score += SCORE_OPEN_THREE
                    elif (is_open_left and is_blocked_right) or (is_blocked_left and is_open_right):
                        pat_score += SCORE_SEMI_THREE
                elif (current_player*2 + empty_char + current_player in segment_str or
                      current_player + empty_char + current_player*2 in segment_str):
                    if is_open_left or is_open_right:
                        pat_score += SCORE_SEMI_THREE // 2
            elif player_count == 2 and empty_count == 3:
                if current_player * 2 in segment_str:
                    if n >= start + WIN_COUNT + 1:
                        longer_segment = line[start : start + WIN_COUNT + 1]
                        longer_str = "".join(longer_segment)
                        if empty_char + current_player*2 + empty_char in longer_str:
                            pat_score += SCORE_OPEN_TWO
                        elif (current_opponent + current_player*2 + empty_char in longer_str or
                              empty_char + current_player*2 + current_opponent in longer_str or
                              (current_player*2 + empty_char in segment_str and (start == 0 or line[start-1] == current_opponent)) or
                              (empty_char + current_player*2 in segment_str and (start + WIN_COUNT == n or line[start + WIN_COUNT] == current_opponent))):
                            pat_score += SCORE_SEMI_TWO
                    elif start == 0 and current_player*2 + empty_char in segment_str and is_open_right:
                        pat_score += SCORE_SEMI_TWO
                    elif start + WIN_COUNT == n and empty_char + current_player*2 in segment_str and is_open_left:
                        pat_score += SCORE_SEMI_TWO
                    elif current_player * 2 in segment_str and is_open_left and is_open_right and empty_count >= 2:
                        pat_score += SCORE_SEMI_TWO
            elif player_count == 1 and empty_count == 4:
                if is_open_left and is_open_right:
                    pat_score += SCORE_OPEN_ONE
        return pat_score

    score += get_pattern_score(player_ai, opponent_in_game)
    score -= get_pattern_score(opponent_in_game, player_ai) * 1.2
    return score

def evaluate_board(board, player_ai, opponent_in_game):
    win_ai, _ = check_win(board, player_ai)
    if win_ai:
        return SCORE_WIN
    win_opponent, _ = check_win(board, opponent_in_game)
    if win_opponent:
        return -SCORE_WIN
    total_score = 0
    lines = []
    for r in range(BOARD_SIZE):
        lines.append([board[r][c] for c in range(BOARD_SIZE)])
    for c in range(BOARD_SIZE):
        lines.append([board[r][c] for r in range(BOARD_SIZE)])
    for k in range(-(BOARD_SIZE - WIN_COUNT), BOARD_SIZE - WIN_COUNT + 1):
        lines.append([board[r][r + k] for r in range(BOARD_SIZE) if 0 <= r + k < BOARD_SIZE])
    for k in range(WIN_COUNT - 1, 2 * BOARD_SIZE - WIN_COUNT):
        lines.append([board[r][k - r] for r in range(BOARD_SIZE) if 0 <= k - r < BOARD_SIZE])
    for line in lines:
        if len(line) >= WIN_COUNT:
            total_score += evaluate_line(line, player_ai, opponent_in_game)
    return total_score

def get_all_moves(board):
    moves = set()
    is_empty = True
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                is_empty = False
                for dr in range(-MOVE_SEARCH_RADIUS, MOVE_SEARCH_RADIUS + 1):
                    for dc in range(-MOVE_SEARCH_RADIUS, MOVE_SEARCH_RADIUS + 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                            moves.add((nr, nc))
    if is_empty:
        center = BOARD_SIZE // 2
        for r in range(max(0, center-1), min(BOARD_SIZE, center+2)):
            for c in range(max(0, center-1), min(BOARD_SIZE, center+2)):
                if board[r][c] == EMPTY:
                    moves.add((r,c))
        if not moves:
            moves.add((center, center))
    return list(moves) if moves else [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == EMPTY]

def minimax_decision(board, player_ai, opponent_in_game, depth):
    best_score = -math.inf
    best_action = None
    possible_moves = get_all_moves(board)
    if not possible_moves:
        return None
    if len(possible_moves) == 1:
        return possible_moves[0]
    for (r, c) in possible_moves:
        board[r][c] = player_ai
        score = min_value(board, depth - 1, player_ai, opponent_in_game)
        board[r][c] = EMPTY
        if score > best_score:
            best_score = score
            best_action = (r, c)
    return best_action if best_action is not None else random.choice(possible_moves)

def max_value(board, depth, player_ai, opponent_in_game):
    if terminal_test(board, depth, player_ai, opponent_in_game):
        return evaluate_board(board, player_ai, opponent_in_game)
    v = -math.inf
    for (r, c) in get_all_moves(board):
        board[r][c] = player_ai
        v = max(v, min_value(board, depth - 1, player_ai, opponent_in_game))
        board[r][c] = EMPTY
    return v

def min_value(board, depth, player_ai, opponent_in_game):
    if terminal_test(board, depth, player_ai, opponent_in_game):
        return evaluate_board(board, player_ai, opponent_in_game)
    v = math.inf
    for (r, c) in get_all_moves(board):
        board[r][c] = opponent_in_game
        v = min(v, max_value(board, depth - 1, player_ai, opponent_in_game))
        board[r][c] = EMPTY
    return v

def alpha_beta_search(board, player_ai, opponent_in_game, depth):
    alpha = -math.inf
    beta = math.inf
    best_score = -math.inf
    best_action = None
    possible_moves = get_all_moves(board)
    if not possible_moves:
        return None
    if len(possible_moves) == 1:
        return possible_moves[0]
    for (r, c) in possible_moves:
        board[r][c] = player_ai
        score = min_value_ab(board, depth - 1, alpha, beta, player_ai, opponent_in_game)
        board[r][c] = EMPTY
        if score > best_score:
            best_score = score
            best_action = (r, c)
        alpha = max(alpha, score)
    return best_action if best_action is not None else random.choice(possible_moves)

def max_value_ab(board, depth, alpha, beta, player_ai, opponent_in_game):
    if terminal_test(board, depth, player_ai, opponent_in_game):
        return evaluate_board(board, player_ai, opponent_in_game)
    v = -math.inf
    for (r, c) in get_all_moves(board):
        board[r][c] = player_ai
        v = max(v, min_value_ab(board, depth - 1, alpha, beta, player_ai, opponent_in_game))
        board[r][c] = EMPTY
        if v >= beta:
            return v
        alpha = max(alpha, v)
    return v

def min_value_ab(board, depth, alpha, beta, player_ai, opponent_in_game):
    if terminal_test(board, depth, player_ai, opponent_in_game):
        return evaluate_board(board, player_ai, opponent_in_game)
    v = math.inf
    for (r, c) in get_all_moves(board):
        board[r][c] = opponent_in_game
        v = min(v, max_value_ab(board, depth - 1, alpha, beta, player_ai, opponent_in_game))
        board[r][c] = EMPTY
        if v <= alpha:
            return v
        beta = min(beta, v)
    return v

# ======== GUI Implementation ========
class GomokuGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Gomoku - Five in a Row")
        self.master.geometry("900x700")
        self.master.configure(bg="#1e1e1e")

        self.board = create_board()
        self.player_symbols = {HUMAN: "Human (X)", AI_MINIMAX: "Minimax AI (O)", AI_ALPHABETA: "Alpha-Beta AI (A)"}
        self.current_player = None
        self.human_player_symbol = HUMAN
        self.ai_player_symbol = AI_MINIMAX
        self.ai_player_symbol_1 = None  # For AI vs. AI mode
        self.ai_player_symbol_2 = None  # For AI vs. AI mode
        self.opponent_player_symbol = None
        self.game_mode = None
        self.game_over = False
        self.last_move = None
        self.winning_line = None
        self.ai_thread = None
        self.ai_move_queue = queue.Queue()
        self.cell_size = 40
        self.board_offset = 50
        self.animations = {}

        # Apply custom styling
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 14), padding=10)
        self.style.map("TButton", background=[("active", "#357abd")])

        # Show main menu
        self.current_screen = None
        self.show_main_menu()

    def clear_screen(self):
        if self.current_screen:
            self.current_screen.destroy()
        self.current_screen = None

    def show_main_menu(self):
        self.clear_screen()
        self.current_screen = tk.Frame(self.master, bg="#1e1e1e")
        self.current_screen.pack(fill="both", expand=True)

        # Gradient background
        canvas = tk.Canvas(self.current_screen, bg="#1e1e1e", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        for i in range(700):
            color = f"#{(int(30 + (i/700)*20)):02x}{(int(30 + (i/700)*20)):02x}{(int(50 + (i/700)*50)):02x}"
            canvas.create_line(0, i, 900, i, fill=color)

        # Title
        title = tk.Label(self.current_screen, text="Gomoku - Five in a Row", font=("Arial", 36, "bold"), fg="white", bg="#1e1e1e")
        title.place(relx=0.5, rely=0.1, anchor="center")

        # Game mode selection
        mode_frame = tk.Frame(self.current_screen, bg="#2d2d2d", bd=2, relief="ridge")
        mode_frame.place(relx=0.5, rely=0.4, anchor="center", width=400, height=300)

        tk.Label(mode_frame, text="Choose Game Mode:", font=("Arial", 18, "bold"), fg="white", bg="#2d2d2d").pack(pady=10)
        self.mode_var = tk.StringVar(value="human_vs_minimax")
        modes = [
            ("Human vs. Minimax AI", "human_vs_minimax"),
            ("Human vs. Alpha-Beta AI", "human_vs_alphabeta"),
            ("Minimax AI vs. Alpha-Beta AI", "ai_vs_ai")
        ]
        for text, value in modes:
            tk.Radiobutton(mode_frame, text=text, value=value, variable=self.mode_var, font=("Arial", 14), fg="white", bg="#2d2d2d", selectcolor="#2d2d2d").pack(anchor="w", padx=20)

        # AI depth
        depth_frame = tk.Frame(mode_frame, bg="#2d2d2d")
        depth_frame.pack(pady=10)
        tk.Label(depth_frame, text="AI Search Depth:", font=("Arial", 14), fg="white", bg="#2d2d2d").pack(side="left")
        self.depth_entry = tk.Entry(depth_frame, width=5, font=("Arial", 14), bg="#3c3c3c", fg="white", insertbackground="white")
        self.depth_entry.insert(0, str(MAX_DEPTH))
        self.depth_entry.pack(side="left", padx=5)

        # Buttons
        ttk.Button(self.current_screen, text="Start Game", command=self.start_game_from_menu).place(relx=0.5, rely=0.7, anchor="center")
        ttk.Button(self.current_screen, text="Custom Board", command=self.show_custom_board_input).place(relx=0.5, rely=0.8, anchor="center")

    def start_game_from_menu(self):
        global MAX_DEPTH
        try:
            depth = int(self.depth_entry.get())
            if depth > 0:
                MAX_DEPTH = depth
            else:
                messagebox.showwarning("Invalid Depth", "Depth must be a positive integer.")
                return
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number for depth.")
            return

        mode = self.mode_var.get()
        if mode == "human_vs_minimax":
            self.start_game("human_vs_ai", ai_player_symbol=AI_MINIMAX)
        elif mode == "human_vs_alphabeta":
            self.start_game("human_vs_ai", ai_player_symbol=AI_ALPHABETA)
        else:
            self.start_game("ai_vs_ai", ai1_symbol=AI_MINIMAX, ai2_symbol=AI_ALPHABETA)

    def show_custom_board_input(self):
        self.clear_screen()
        self.current_screen = tk.Frame(self.master, bg="#1e1e1e")
        self.current_screen.pack(fill="both", expand=True)

        tk.Label(self.current_screen, text="Enter Custom Board", font=("Arial", 24, "bold"), fg="white", bg="#1e1e1e").pack(pady=10)
        entry_frame = tk.Frame(self.current_screen, bg="#1e1e1e")
        entry_frame.pack(pady=10)

        self.custom_entries = []
        for r in range(BOARD_SIZE):
            row_frame = tk.Frame(entry_frame, bg="#1e1e1e")
            row_frame.pack(fill="x")
            tk.Label(row_frame, text=f"Row {r:02d}:", font=("Arial", 12), fg="white", bg="#1e1e1e").pack(side="left")
            entry = tk.Entry(row_frame, width=BOARD_SIZE + 5, font=("Consolas", 12), bg="#3c3c3c", fg="white", insertbackground="white")
            entry.pack(side="left", expand=True, fill="x")
            self.custom_entries.append(entry)

        button_frame = tk.Frame(self.current_screen, bg="#1e1e1e")
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Load Board", command=self.load_custom_board).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.show_main_menu).pack(side="left", padx=5)

    def load_custom_board(self):
        new_board = []
        valid_chars = [EMPTY, HUMAN, AI_MINIMAX, AI_ALPHABETA]
        for i, entry in enumerate(self.custom_entries):
            row_str = entry.get().strip()
            if len(row_str) != BOARD_SIZE or not all(c in valid_chars for c in row_str):
                messagebox.showwarning("Invalid Input", f"Row {i} is invalid. Use {BOARD_SIZE} chars: {valid_chars}.")
                return
            new_board.append(list(row_str))
        self.board = new_board
        self.show_main_menu()

    def show_game_screen(self):
        self.clear_screen()
        self.current_screen = tk.Frame(self.master, bg="#1e1e1e")
        self.current_screen.pack(fill="both", expand=True)

        # Status
        self.status_label = tk.Label(self.current_screen, text="Game started.", font=("Arial", 16), fg="white", bg="#1e1e1e")
        self.status_label.pack(pady=10)

        # Board canvas
        self.canvas = tk.Canvas(self.current_screen, width=(BOARD_SIZE + 1) * self.cell_size, height=(BOARD_SIZE + 1) * self.cell_size, bg="#3c3c3c", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.handle_click)

        # Draw board
        self.draw_board()

        # Controls
        control_frame = tk.Frame(self.current_screen, bg="#1e1e1e")
        control_frame.pack(pady=10)
        ttk.Button(control_frame, text="Back to Menu", command=self.show_main_menu).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Reset Game", command=self.reset_game).pack(side="left", padx=5)
        tk.Label(control_frame, text=f"Human={HUMAN} (Blue), Minimax={AI_MINIMAX} (Red), AlphaBeta={AI_ALPHABETA} (Purple)", font=("Arial", 12), fg="white", bg="#1e1e1e").pack(side="left", padx=5)

    def draw_board(self):
        self.canvas.delete("all")
        # Draw wooden background
        for i in range(0, (BOARD_SIZE + 1) * self.cell_size, 10):
            color = f"#{(int(139 - (i/((BOARD_SIZE+1)*self.cell_size))*20)):02x}{(int(69 + (i/((BOARD_SIZE+1)*self.cell_size))*20)):02x}19"
            self.canvas.create_rectangle(0, i, (BOARD_SIZE + 1) * self.cell_size, i + 10, fill=color, outline="")

        # Draw grid
        for i in range(BOARD_SIZE + 1):
            x = self.board_offset + i * self.cell_size
            y = self.board_offset + i * self.cell_size
            self.canvas.create_line(x, self.board_offset, x, self.board_offset + BOARD_SIZE * self.cell_size, fill="black")
            self.canvas.create_line(self.board_offset, y, self.board_offset + BOARD_SIZE * self.cell_size, y, fill="black")

        # Draw labels
        for i in range(BOARD_SIZE):
            self.canvas.create_text(self.board_offset + i * self.cell_size + self.cell_size // 2, self.board_offset // 2, text=str(i), font=("Arial", 12), fill="white")
            self.canvas.create_text(self.board_offset // 2, self.board_offset + i * self.cell_size + self.cell_size // 2, text=str(i), font=("Arial", 12), fill="white")

        # Draw pieces
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] != EMPTY:
                    x = self.board_offset + c * self.cell_size + self.cell_size // 2
                    y = self.board_offset + r * self.cell_size + self.cell_size // 2
                    radius = self.cell_size // 2 - 5
                    color = "blue" if self.board[r][c] == HUMAN else "red" if self.board[r][c] == AI_MINIMAX else "purple"
                    self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline="black")
                    if self.last_move and (r, c) == self.last_move:
                        self.canvas.create_oval(x - radius - 3, y - radius - 3, x + radius + 3, y + radius + 3, outline=LAST_MOVE_COLOR, width=2)
                    if self.winning_line and (r, c) in self.winning_line:
                        self.canvas.create_oval(x - radius - 5, y - radius - 5, x + radius + 5, y + radius + 5, outline="lightgreen", width=3)

    def handle_click(self, event):
        if self.game_over or self.game_mode != "human_vs_ai" or self.current_player != self.human_player_symbol:
            return
        r = (event.y - self.board_offset) // self.cell_size
        c = (event.x - self.board_offset) // self.cell_size
        if is_valid_move(self.board, r, c):
            self.make_move(r, c)
        else:
            self.update_status("Invalid move. Choose an empty cell.")

    def start_game(self, mode, ai_player_symbol=AI_MINIMAX, ai1_symbol=AI_MINIMAX, ai2_symbol=AI_ALPHABETA, initial_player=None, custom_board=False):
        self.game_mode = mode
        self.game_over = False
        self.last_move = None
        self.winning_line = None
        if not custom_board:
            self.board = create_board()
        if mode == "human_vs_ai":
            self.human_player_symbol = HUMAN
            self.ai_player_symbol = ai_player_symbol
            self.opponent_player_symbol = self.human_player_symbol
            self.ai_player_symbol_1 = None
            self.ai_player_symbol_2 = None
            self.current_player = self.human_player_symbol if initial_player is None else initial_player
        else:  # ai_vs_ai
            self.ai_player_symbol_1 = ai1_symbol
            self.ai_player_symbol_2 = ai2_symbol
            self.ai_player_symbol = None
            self.opponent_player_symbol = None
            self.current_player = self.ai_player_symbol_1 if initial_player is None else initial_player
        self.show_game_screen()
        self.update_status(f"{self.player_symbols.get(self.current_player, self.current_player)}'s turn.")
        if mode == "ai_vs_ai" or (mode == "human_vs_ai" and self.current_player == self.ai_player_symbol):
            self.master.after(500, self.trigger_ai_move)

    def make_move(self, r, c):
        if self.game_over:
            return
        player = self.current_player
        self.board[r][c] = player
        self.last_move = (r, c)
        self.draw_board()
        win, win_line = check_win(self.board, player)
        if win:
            self.game_over = True
            self.winning_line = win_line
            self.draw_board()
            self.update_status(f"{self.player_symbols.get(player, player)} wins!")
            messagebox.showinfo("Game Over", f"{self.player_symbols.get(player, player)} wins!")
            return
        if is_board_full(self.board):
            self.game_over = True
            self.update_status("Draw!")
            messagebox.showinfo("Game Over", "It's a Draw!")
            return
        if self.game_mode == "human_vs_ai":
            self.current_player = self.ai_player_symbol if player == self.human_player_symbol else self.human_player_symbol
        else:  # ai_vs_ai
            self.current_player = self.ai_player_symbol_2 if player == self.ai_player_symbol_1 else self.ai_player_symbol_1
        self.update_status(f"{self.player_symbols.get(self.current_player, self.current_player)}'s turn.")
        if (self.game_mode == "human_vs_ai" and self.current_player == self.ai_player_symbol) or self.game_mode == "ai_vs_ai":
            self.master.after(500, self.trigger_ai_move)

    def trigger_ai_move(self):
        if self.game_over:
            return
        ai_player = self.current_player
        if self.game_mode == "human_vs_ai":
            opponent_player = self.human_player_symbol
        else:  # ai_vs_ai
            opponent_player = self.ai_player_symbol_2 if ai_player == self.ai_player_symbol_1 else self.ai_player_symbol_1
        self.update_status(f"{self.player_symbols.get(ai_player, ai_player)} is thinking...")
        board_copy = [row[:] for row in self.board]
        ai_algorithm = (lambda b, p, o, d: minimax_decision(b, p, o, d)) if ai_player == AI_MINIMAX else (lambda b, p, o, d: alpha_beta_search(b, p, o, d))
        self.ai_thread = threading.Thread(target=self.run_ai_in_thread, args=(board_copy, ai_player, opponent_player, MAX_DEPTH, ai_algorithm))
        self.ai_thread.start()
        self.master.after(100, self.check_ai_thread)

    def run_ai_in_thread(self, board_copy, ai_player, opponent_player, depth, ai_algorithm):
        try:
            move = ai_algorithm(board_copy, ai_player, opponent_player, depth)
            self.ai_move_queue.put(move)
        except Exception as e:
            print(f"AI thread error: {e}")
            self.ai_move_queue.put(None)

    def check_ai_thread(self):
        try:
            move = self.ai_move_queue.get_nowait()
            if move is not None:
                self.make_move(*move)
            else:
                self.update_status("AI failed to make a move.")
                self.game_over = True
                messagebox.showwarning("AI Error", "AI could not make a valid move.")
            self.ai_thread = None
        except queue.Empty:
            if self.ai_thread and self.ai_thread.is_alive():
                self.master.after(100, self.check_ai_thread)
            else:
                self.update_status("AI encountered an issue.")
                self.ai_thread = None

    def update_status(self, message):
        self.status_label.config(text=message)

    def reset_game(self):
        self.board = create_board()
        self.game_over = False
        self.last_move = None
        self.winning_line = None
        self.current_player = self.human_player_symbol if self.game_mode == "human_vs_ai" else self.ai_player_symbol_1
        self.draw_board()
        self.update_status(f"{self.player_symbols.get(self.current_player, self.current_player)}'s turn.")
        if self.game_mode == "ai_vs_ai" or (self.game_mode == "human_vs_ai" and self.current_player == self.ai_player_symbol):
            self.master.after(500, self.trigger_ai_move)

# ======== Main Application Entry Point ========
if __name__ == "__main__":
    root = tk.Tk()
    app = GomokuGUI(root)
    root.mainloop()
