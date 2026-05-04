import os
import time

# ─── Constants ───────────────────────────────────────────────────────────────

WINS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
    [0, 4, 8], [2, 4, 6],             # diagonals
]

# ─── Display ─────────────────────────────────────────────────────────────────

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_title():
    print("=" * 35)
    print("       ✦  TIC  TAC  TOE  ✦")
    print("=" * 35)


def print_scoreboard(names, scores, round_num):
    x_name = names["X"]
    o_name = names["O"]
    print(f"\n  Round {round_num}")
    print(f"  {x_name} (X): {scores['X']}   "
          f"Draws: {scores['D']}   "
          f"{o_name} (O): {scores['O']}")
    print()


def print_board(board, winning_combo=None):
    symbols = []
    for i, val in enumerate(board):
        if winning_combo and i in winning_combo:
            symbols.append(f"[{val}]")
        elif val == "X":
            symbols.append(" X ")
        elif val == "O":
            symbols.append(" O ")
        else:
            symbols.append(f" {i + 1} ")

    print("  +-----+-----+-----+")
    print(f"  |{symbols[0]}|{symbols[1]}|{symbols[2]}|")
    print("  +-----+-----+-----+")
    print(f"  |{symbols[3]}|{symbols[4]}|{symbols[5]}|")
    print("  +-----+-----+-----+")
    print(f"  |{symbols[6]}|{symbols[7]}|{symbols[8]}|")
    print("  +-----+-----+-----+")
    print()


# ─── Game Logic ───────────────────────────────────────────────────────────────

def check_win(board, player):
    for combo in WINS:
        if all(board[i] == player for i in combo):
            return combo
    return None


def check_draw(board):
    return all(cell in ("X", "O") for cell in board)


def get_move(board, player_name, mark):
    while True:
        try:
            move = input(f"  {player_name} ({mark}) → enter cell [1-9]: ").strip()
            if move.lower() == "q":
                return None
            idx = int(move) - 1
            if idx < 0 or idx > 8:
                print("  ⚠  Please enter a number between 1 and 9.\n")
            elif board[idx] in ("X", "O"):
                print("  ⚠  That cell is already taken. Try another.\n")
            else:
                return idx
        except ValueError:
            print("  ⚠  Invalid input. Enter a number from 1 to 9.\n")


# ─── Round ────────────────────────────────────────────────────────────────────

def play_round(names, scores, round_num):
    board = [None] * 9
    # Alternate who goes first each round
    first = "X" if round_num % 2 == 1 else "O"
    current = first
    log = []

    while True:
        clear()
        print_title()
        print_scoreboard(names, scores, round_num)
        print_board(board)

        if log:
            print(f"  Last move: {log[-1]}")
            print()

        idx = get_move(board, names[current], current)
        if idx is None:
            return "quit"

        board[idx] = current
        log.append(f"{names[current]} ({current}) → cell {idx + 1}")

        win_combo = check_win(board, current)
        if win_combo:
            scores[current] += 1
            clear()
            print_title()
            print_scoreboard(names, scores, round_num)
            print_board(board, winning_combo=win_combo)
            print(f"  🎉  {names[current]} ({current}) wins the round!\n")
            return "continue"

        if check_draw(board):
            scores["D"] += 1
            clear()
            print_title()
            print_scoreboard(names, scores, round_num)
            print_board(board)
            print("  🤝  It's a draw!\n")
            return "continue"

        current = "O" if current == "X" else "X"


# ─── Setup ────────────────────────────────────────────────────────────────────

def get_names():
    clear()
    print_title()
    print("\n  Enter player names (or press Enter for defaults)\n")
    x = input("  Player 1 (X) name: ").strip() or "Player 1"
    o = input("  Player 2 (O) name: ").strip() or "Player 2"
    return {"X": x, "O": o}


def play_again():
    while True:
        choice = input("  Play another round? [y / n]: ").strip().lower()
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no", "q"):
            return False
        print("  Please enter y or n.\n")


def reset_scores():
    while True:
        choice = input("  Reset scores and start over? [y / n]: ").strip().lower()
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    names = get_names()
    scores = {"X": 0, "O": 0, "D": 0}
    round_num = 0

    print(f"\n  {names['X']} (X) vs {names['O']} (O) — let's play!")
    time.sleep(1.2)

    while True:
        round_num += 1
        result = play_round(names, scores, round_num)

        if result == "quit":
            break

        if not play_again():
            break

    # Final summary
    clear()
    print_title()
    print("\n  ── Final Scores ──\n")
    print(f"  {names['X']} (X) : {scores['X']} wins")
    print(f"  {names['O']} (O) : {scores['O']} wins")
    print(f"  Draws           : {scores['D']}")
    print()

    if scores["X"] > scores["O"]:
        print(f"  🏆  {names['X']} wins overall!")
    elif scores["O"] > scores["X"]:
        print(f"  🏆  {names['O']} wins overall!")
    else:
        print("  🤝  Overall it's a tie!")

    print("\n  Thanks for playing!\n")


if __name__ == "__main__":
    main()