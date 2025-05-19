#====== بسم الله الرحمن الرخيم ======
import math
import random
import copy

# ======== Game Settings ========
BOARD_SIZE = 15
WIN_COUNT = 5
EMPTY = "."
HUMAN = "X"
AI_MINIMAX = "O"
AI_ALPHABETA = "A"
MAX_DEPTH = 2  # Adjustable search depth, increased for better AI

# Heuristic scores
SCORE_WIN = 100000
SCORE_OPEN_FOUR = 10000
SCORE_SEMI_FOUR = 1000
SCORE_OPEN_THREE = 500
SCORE_SEMI_THREE = 100
SCORE_OPEN_TWO = 50
SCORE_SEMI_TWO = 10
SCORE_OPEN_ONE = 1  # Slight preference for own pieces


# ======== Board Creation & Display ========
def create_board():
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def print_board(board):
    title = "GOMOKU - FIVE IN A ROW"
    board_width_chars = 3 + (4 * BOARD_SIZE)
    print("\n" + "╔" + "═" * (board_width_chars - 2) + "╗")
    print("║" + f"{title:^{board_width_chars - 2}}" + "║")
    print("╚" + "═" * (board_width_chars - 2) + "╝")
    print("\n===== CURRENT BOARD STATE =====")
    header_str = "   "
    for i in range(BOARD_SIZE):
        header_str += f"{i:^3} "
    print(header_str.rstrip())
    grid_line = "  +" + "---+" * BOARD_SIZE
    print(grid_line)
    for r_idx, row_values in enumerate(board):
        row_str = f"{r_idx:<2}|"
        for cell in row_values:
            row_str += f" {cell} |"
        print(row_str)
        print(grid_line)
    print(f"Players: Human='{HUMAN}', Minimax AI='{AI_MINIMAX}', AlphaBeta AI='{AI_ALPHABETA}', Empty='{EMPTY}'\n")


# ======== Move Handling ========
def is_valid_move(board, r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY


# ======== Win & Terminal Checking ========
def check_win(board, player):
    if player == EMPTY: return False  # Empty player cannot win
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # Vertical, Horizontal, Diagonal /, Diagonal \
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                for dr, dc in directions:
                    count = 0
                    for i in range(WIN_COUNT):
                        rr, cc = r + dr * i, c + dc * i
                        if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == player:
                            count += 1
                        else:
                            break
                    if count == WIN_COUNT:
                        return True
    return False


def is_board_full(board):
    return all(cell != EMPTY for row in board for cell in row)


def terminal_test(board, depth, player_ai, opponent_in_game):
    return depth == 0 or \
           check_win(board, player_ai) or \
           check_win(board, opponent_in_game) or \
           is_board_full(board)


# ======== Evaluation Function (Heuristic) ========
def evaluate_line(line, player_ai, opponent_in_game):
    score = 0
    # Evaluate for player_ai
    score += count_patterns_in_line(line, player_ai, opponent_in_game, True)
    # Evaluate for opponent_in_game (subtract from player_ai's score)
    score -= count_patterns_in_line(line, opponent_in_game, player_ai, False)
    return score


def count_patterns_in_line(line_segment, player, opponent, is_ai_perspective):
    line_str = "".join(line_segment)
    player_char = player
    opponent_char = opponent
    empty_char = EMPTY
    n = len(line_segment)
    line_score = 0

    # Winning five is handled by check_win directly in evaluate_board

    # Open Fours: .XXXX.
    pattern = empty_char + player_char * 4 + empty_char
    line_score += line_str.count(pattern) * SCORE_OPEN_FOUR

    # Semi-Open Fours: OXXXX. or .XXXXO (opponent blocking one side)
    pattern1 = opponent_char + player_char * 4 + empty_char
    pattern2 = empty_char + player_char * 4 + opponent_char
    line_score += (line_str.count(pattern1) + line_str.count(pattern2)) * SCORE_SEMI_FOUR
    # Also consider board edge as a block for semi-open
    # if line_str.startswith(player_char*4 + empty_char): line_score += SCORE_SEMI_FOUR
    # if line_str.endswith(empty_char + player_char*4): line_score += SCORE_SEMI_FOUR

    # Open Threes: .XXX.
    pattern = empty_char + player_char * 3 + empty_char
    line_score += line_str.count(pattern) * SCORE_OPEN_THREE

    # Semi-Open Threes: OXXX. or .XXXO or .X.XX. or .XX.X.
    pattern1 = opponent_char + player_char * 3 + empty_char
    pattern2 = empty_char + player_char * 3 + opponent_char
    line_score += (line_str.count(pattern1) + line_str.count(pattern2)) * SCORE_SEMI_THREE
    # if line_str.startswith(player_char*3 + empty_char): line_score += SCORE_SEMI_THREE
    # if line_str.endswith(empty_char + player_char*3): line_score += SCORE_SEMI_THREE
    # More complex semi-open threes like X.XX or XX.X with open ends
    # .X.XX. (already covered by .XXX. if X's are together)
    # For simplicity, we are using simpler string counts. A more robust way involves iterating and checking segments.

    # Open Twos: .XX.
    pattern = empty_char + player_char * 2 + empty_char
    line_score += line_str.count(pattern) * SCORE_OPEN_TWO

    # Semi-Open Twos: OXX. or .XXO
    pattern1 = opponent_char + player_char * 2 + empty_char
    pattern2 = empty_char + player_char * 2 + opponent_char
    line_score += (line_str.count(pattern1) + line_str.count(pattern2)) * SCORE_SEMI_TWO
    # if line_str.startswith(player_char*2 + empty_char): line_score += SCORE_SEMI_TWO
    # if line_str.endswith(empty_char + player_char*2): line_score += SCORE_SEMI_TWO

    # Single pieces in open space (less important, but can break ties)
    pattern = empty_char + player_char + empty_char
    line_score += line_str.count(pattern) * SCORE_OPEN_ONE

    return line_score


def evaluate_board(board, player_ai, opponent_in_game):
    if check_win(board, player_ai):
        return SCORE_WIN
    if check_win(board, opponent_in_game):
        return -SCORE_WIN
    if is_board_full(board):
        return 0  # Draw

    total_score = 0
    lines = []
    # Rows
    for r in range(BOARD_SIZE):
        lines.append([board[r][c] for c in range(BOARD_SIZE)])
    # Columns
    for c in range(BOARD_SIZE):
        lines.append([board[r][c] for r in range(BOARD_SIZE)])
    # Diagonals (top-left to bottom-right)
    for k in range(-(BOARD_SIZE - WIN_COUNT), BOARD_SIZE - WIN_COUNT + 1):
        lines.append([board[r][r + k] for r in range(BOARD_SIZE) if 0 <= r + k < BOARD_SIZE])
    # Diagonals (top-right to bottom-left)
    for k in range(WIN_COUNT - 1, 2 * BOARD_SIZE - WIN_COUNT):
        lines.append([board[r][k - r] for r in range(BOARD_SIZE) if 0 <= k - r < BOARD_SIZE])

    for line in lines:
        if len(line) >= WIN_COUNT:  # Only evaluate lines long enough for a win
            total_score += evaluate_line(line, player_ai, opponent_in_game)

    # Add a small random factor to break ties if scores are identical, makes AI less predictable
    # total_score += random.randint(-3, 3)
    return total_score


# ======== Successor Generation ========
def get_all_moves(board):
    # Consider only moves near existing pieces for efficiency (optional optimization)
    # For now, return all empty cells
    return [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == EMPTY]


# ======== Minimax Implementation ========
def minimax_decision(board, player_ai, opponent_in_game):
    best_score = -math.inf
    best_action = None
    possible_moves = get_all_moves(board)
    if not possible_moves: return None  # No moves left

    for (r, c) in possible_moves:
        board[r][c] = player_ai
        score = min_value(board, MAX_DEPTH - 1, player_ai, opponent_in_game)
        board[r][c] = EMPTY  # Backtrack
        if score > best_score:
            best_score = score
            best_action = (r, c)
    return best_action if best_action is not None else random.choice(possible_moves)  # Fallback if all scores are -inf


def max_value(board, depth, player_ai, opponent_in_game):
    if terminal_test(board, depth, player_ai, opponent_in_game):
        return evaluate_board(board, player_ai, opponent_in_game)
    v = -math.inf
    for (r, c) in get_all_moves(board):
        board[r][c] = player_ai  # AI's turn
        v = max(v, min_value(board, depth - 1, player_ai, opponent_in_game))
        board[r][c] = EMPTY  # Backtrack
    return v


def min_value(board, depth, player_ai, opponent_in_game):
    if terminal_test(board, depth, player_ai, opponent_in_game):
        return evaluate_board(board, player_ai, opponent_in_game)
    v = math.inf
    for (r, c) in get_all_moves(board):
        board[r][c] = opponent_in_game  # Opponent's turn
        v = min(v, max_value(board, depth - 1, player_ai, opponent_in_game))
        board[r][c] = EMPTY  # Backtrack
    return v


# ======== Alpha-Beta Implementation ========
def alpha_beta_search(board, player_ai, opponent_in_game):
    alpha = -math.inf
    beta = math.inf
    best_score = -math.inf
    best_action = None
    possible_moves = get_all_moves(board)
    if not possible_moves: return None

    for (r, c) in possible_moves:
        board[r][c] = player_ai
        score = min_value_ab(board, MAX_DEPTH - 1, alpha, beta, player_ai, opponent_in_game)
        board[r][c] = EMPTY  # Backtrack
        if score > best_score:
            best_score = score
            best_action = (r, c)
        alpha = max(alpha, best_score)  # Update alpha for the root
    return best_action if best_action is not None else random.choice(possible_moves)


def max_value_ab(board, depth, alpha, beta, player_ai, opponent_in_game):
    if terminal_test(board, depth, player_ai, opponent_in_game):
        return evaluate_board(board, player_ai, opponent_in_game)
    v = -math.inf
    for (r, c) in get_all_moves(board):
        board[r][c] = player_ai  # AI's turn
        v = max(v, min_value_ab(board, depth - 1, alpha, beta, player_ai, opponent_in_game))
        board[r][c] = EMPTY  # Backtrack
        if v >= beta:
            return v  # Beta cutoff
        alpha = max(alpha, v)
    return v


def min_value_ab(board, depth, alpha, beta, player_ai, opponent_in_game):
    if terminal_test(board, depth, player_ai, opponent_in_game):
        return evaluate_board(board, player_ai, opponent_in_game)
    v = math.inf
    for (r, c) in get_all_moves(board):
        board[r][c] = opponent_in_game  # Opponent's turn
        v = min(v, max_value_ab(board, depth - 1, alpha, beta, player_ai, opponent_in_game))
        board[r][c] = EMPTY  # Backtrack
        if v <= alpha:
            return v  # Alpha cutoff
        beta = min(beta, v)
    return v


# ======== Custom Board Input Function ========
def get_initial_board():
    while True:
        choice = input(
            f"Do you want to enter an initial board state? (yes/no, default: no, board size: {BOARD_SIZE}x{BOARD_SIZE}): ").strip().lower()
        if choice == "yes":
            print(
                f"Enter the board row by row. Use '{EMPTY}' for empty, '{HUMAN}' for human, '{AI_MINIMAX}' or '{AI_ALPHABETA}' for AI.")
            print(f"Each row should have {BOARD_SIZE} characters.")
            custom_board = []
            for r_idx in range(BOARD_SIZE):
                while True:
                    row_str = input(f"Enter row {r_idx}: ").strip()
                    if len(row_str) == BOARD_SIZE and all(
                            c in [EMPTY, HUMAN, AI_MINIMAX, AI_ALPHABETA] for c in row_str):
                        custom_board.append(list(row_str))
                        break
                    else:
                        print(f"Invalid row input. Ensure it has {BOARD_SIZE} characters and valid symbols.")
            print("Custom board accepted.")
            return custom_board
        elif choice == "no" or choice == "":
            return create_board()
        else:
            print("Invalid choice. Please enter 'yes' or 'no'.")


# ======== Game Modes ========
def play_human_vs_ai():
    board = get_initial_board()
    human_player_symbol = HUMAN
    ai_player_symbol = AI_MINIMAX  # Default AI for Human vs AI
    current_player_symbol = human_player_symbol  # Human starts by default

    while True:
        print_board(board)
        if current_player_symbol == human_player_symbol:
            try:
                r_in = input(f"Human ({human_player_symbol}), enter row: ").strip()
                c_in = input(f"Human ({human_player_symbol}), enter col: ").strip()
                if not r_in or not c_in:
                    print("Empty input. Please enter row and column.")
                    continue
                r, c = int(r_in), int(c_in)
            except ValueError:
                print("Invalid input. Please enter numbers for row and column.")
                continue
            move = (r, c)
        else:  # AI's turn
            print(f"AI ({ai_player_symbol}) is thinking...")
            # For Human vs AI, AI is Minimax, opponent is Human
            move = minimax_decision(board, ai_player_symbol, human_player_symbol)

            if move is None:
                print_board(board)
                if is_board_full(board):
                    print("Draw!")
                else:
                    print(f"AI ({ai_player_symbol}) cannot make a move. Game Over or Error.")
                break
            print(f"AI ({ai_player_symbol}) plays at {move}")

        if not is_valid_move(board, *move):
            print("Invalid move. Try again.")
            continue

        board[move[0]][move[1]] = current_player_symbol

        if check_win(board, current_player_symbol):
            print_board(board)
            print(f"Player {current_player_symbol} wins!")
            break
        if is_board_full(board):
            print_board(board)
            print("Draw!")
            break

        current_player_symbol = ai_player_symbol if current_player_symbol == human_player_symbol else human_player_symbol


def play_ai_vs_ai():
    board = get_initial_board()
    player1_ai_symbol = AI_MINIMAX
    player2_ai_symbol = AI_ALPHABETA
    current_player_symbol = player1_ai_symbol  # Minimax starts

    while True:
        print_board(board)
        print(f"Turn for AI: {current_player_symbol}")
        if current_player_symbol == player1_ai_symbol:  # Minimax's turn
            print(f"{player1_ai_symbol} (Minimax) is thinking...")
            move = minimax_decision(board, player1_ai_symbol, player2_ai_symbol)
        else:  # player2_ai_symbol (AlphaBeta)'s turn
            print(f"{player2_ai_symbol} (AlphaBeta) is thinking...")
            move = alpha_beta_search(board, player2_ai_symbol, player1_ai_symbol)

        if move is None:
            print_board(board)
            if is_board_full(board):
                print("Draw!")
            else:
                print(f"AI ({current_player_symbol}) cannot make a move. Game Over or Error.")
            break

        print(f"AI ({current_player_symbol}) plays at {move}")
        board[move[0]][move[1]] = current_player_symbol

        if check_win(board, current_player_symbol):
            print_board(board)
            print(f"Player {current_player_symbol} wins!")
            break
        if is_board_full(board):
            print_board(board)
            print("Draw!")
            break

        current_player_symbol = player2_ai_symbol if current_player_symbol == player1_ai_symbol else player1_ai_symbol


# ======== Entry Point ========
if __name__ == "__main__":
    print("Welcome to Gomoku!")
    MAX_DEPTH = 2  # Default depth, can be adjusted
    try:
        depth_input = input(f"Enter search depth for AI (e.g., 1, 2, 3 - default is {MAX_DEPTH}): ").strip()
        if depth_input:
            MAX_DEPTH = int(depth_input)
            if MAX_DEPTH <= 0:
                print("Depth must be positive. Using default.")
                MAX_DEPTH = 2
    except ValueError:
        print("Invalid depth input. Using default.")
        MAX_DEPTH = 2
    print(f"Using search depth: {MAX_DEPTH}")

    while True:
        mode = input("Select Mode: 1) Human vs AI (Minimax)  2) AI (Minimax) vs AI (Alpha-Beta) : ").strip()
        if mode == "1":
            play_human_vs_ai()
            break
        elif mode == "2":
            play_ai_vs_ai()
            break
        else:
            print("Invalid mode selected. Please enter 1 or 2.")
