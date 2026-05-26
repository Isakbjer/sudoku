"""Minimal Sudoku engine and CLI handler.

Provides both module-level pure helpers (operate on a grid list-of-lists)
and a small `Board` class that wraps state and a move log. The CLI
handler accepts either a `Board` instance or the legacy `(grid, move_log)`
pair for backwards compatibility.
"""
from __future__ import annotations

import copy
from typing import Dict, List, Optional, Set, Tuple

import example_games


def print_grid(grid: List[List[Optional[int]]]) -> None:
    """Print the Sudoku grid with block separators."""
    n = len(grid)
    block = int(n**0.5)
    print("Current Sudoku Grid:")
    for i in range(n):
        if i % block == 0 and i != 0:
            print("-" * (n * 2 + block - 1))
        for j in range(n):
            if j % block == 0 and j != 0:
                print("| ", end="")
            val = grid[i][j]
            print("." if val is None else val, end=" ")
        print()


def get_row_view(grid: List[List[Optional[int]]], row: int) -> List[Optional[int]]:
    return list(grid[row])


def get_column_view(grid: List[List[Optional[int]]], column: int) -> List[Optional[int]]:
    n = len(grid)
    return [grid[r][column] for r in range(n)]


def get_box_view(grid: List[List[Optional[int]]], row: int, column: int) -> List[List[Optional[int]]]:
    n = len(grid)
    block = int(n**0.5)
    br = (row // block) * block
    bc = (column // block) * block
    return [[grid[r][c] for c in range(bc, bc + block)] for r in range(br, br + block)]


def find_notes(grid: List[List[Optional[int]]], row: int, column: int) -> Set[int]:
    n = len(grid)
    if grid[row][column] is not None:
        return set()
    candidates = set(range(1, n + 1))
    candidates -= {x for x in grid[row] if x is not None}
    candidates -= {grid[r][column] for r in range(n) if grid[r][column] is not None}
    block = int(n**0.5)
    br = (row // block) * block
    bc = (column // block) * block
    for r in range(br, br + block):
        for c in range(bc, bc + block):
            v = grid[r][c]
            if v is not None:
                candidates.discard(v)
    return candidates


def edit_notes(grid: List[List[Optional[int]]], row: int, column: int, value: int) -> Set[int]:
    """Return a modified notes set for one-off editing (doesn't persist)."""
    notes = find_notes(grid, row, column)
    if value in notes:
        notes.remove(value)
        print(f"Removed {value} from notes for cell ({row}, {column}).")
    else:
        notes.add(value)
        print(f"Added {value} to notes for cell ({row}, {column}).")
    return notes


def find_easy_move(grid: List[List[Optional[int]]]) -> Optional[Tuple[int, int, int]]:
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] is None:
                notes = find_notes(grid, i, j)
                if len(notes) == 1:
                    return (i, j, next(iter(notes)))
    return None


def is_valid_move(grid: List[List[Optional[int]]], row: int, column: int, value: int) -> bool:
    n = len(grid)
    if not (0 <= row < n and 0 <= column < n):
        return False
    if not (1 <= value <= n):
        return False
    if grid[row][column] is not None:
        return False
    if value in grid[row]:
        return False
    if any(grid[r][column] == value for r in range(n)):
        return False
    block = int(n**0.5)
    br = (row // block) * block
    bc = (column // block) * block
    for r in range(br, br + block):
        for c in range(bc, bc + block):
            if grid[r][c] == value:
                return False
    return True


def undo_move(grid: List[List[Optional[int]]], move_log: List[Tuple[int, int, Optional[int], Optional[int]]]) -> bool:
    if not move_log:
        return False
    row, column, old_value, new_value = move_log.pop()
    grid[row][column] = old_value
    print(f"Undid move {new_value} at ({row}, {column}).")
    return True


def make_move(grid: List[List[Optional[int]]], row: int, column: int, value: int,
              move_log: Optional[List[Tuple[int, int, Optional[int], Optional[int]]]] = None) -> bool:
    # Special-case: use 0 or None to clear a cell
    if value is None or value == 0:
        old_value = grid[row][column]
        grid[row][column] = None
        if move_log is not None:
            move_log.append((row, column, old_value, None))
        return True

    if not is_valid_move(grid, row, column, value):
        print("Invalid move. Try again.")
        return False
    old_value = grid[row][column]
    grid[row][column] = value
    if move_log is not None:
        move_log.append((row, column, old_value, value))
    return True


def empty_cell(grid: List[List[Optional[int]]], row: int, column: int,
               move_log: Optional[List[Tuple[int, int, Optional[int], Optional[int]]]] = None) -> None:
    if 0 <= row < len(grid) and 0 <= column < len(grid[0]):
        old_value = grid[row][column]
        grid[row][column] = None
        if move_log is not None:
            move_log.append((row, column, old_value, None))


class Board:
    """Simple OO wrapper around the grid and its move log."""

    def __init__(self, grid: List[List[Optional[int]]]):
        self.grid = copy.deepcopy(grid)
        # move_log entries: legacy tuples (r,c,old,new) or composite
        # ('composite', [ ('cell', r,c,old,new), ('notes_snapshot', {(r,c): set(...)}) ])
        self.move_log: List = []
        # givens: coordinates that should not be changed by the player
        self.givens: Set[Tuple[int, int]] = set()
        n = len(self.grid)
        for r in range(n):
            for c in range(len(self.grid[0])):
                if self.grid[r][c] is not None:
                    self.givens.add((r, c))
        # notes stores user/autonotes per cell
        self.notes: Dict[Tuple[int, int], Set[int]] = {}
        self.autonote: bool = True
        if self.autonote:
            self.recompute_notes()

    def get_grid_copy(self) -> List[List[Optional[int]]]:
        return copy.deepcopy(self.grid)

    def print_grid(self) -> None:
        print_grid(self.grid)

    def get_row_view(self, row: int) -> List[Optional[int]]:
        return get_row_view(self.grid, row)

    def get_column_view(self, column: int) -> List[Optional[int]]:
        return get_column_view(self.grid, column)

    def get_box_view(self, row: int, column: int) -> List[List[Optional[int]]]:
        return get_box_view(self.grid, row, column)

    def find_notes(self, row: int, column: int) -> Set[int]:
        # prefer persistent notes if present, otherwise compute
        key = (row, column)
        if key in self.notes:
            return set(self.notes[key])
        return find_notes(self.grid, row, column)

    def edit_notes(self, row: int, column: int, value: int) -> Set[int]:
        return edit_notes(self.grid, row, column, value)

    def find_easy_move(self):
        return find_easy_move(self.grid)

    def is_valid_move(self, row: int, column: int, value: int) -> bool:
        return is_valid_move(self.grid, row, column, value)

    def recompute_notes(self) -> None:
        self.notes = {}
        n = len(self.grid)
        for r in range(n):
            for c in range(n):
                if self.grid[r][c] is None:
                    self.notes[(r, c)] = find_notes(self.grid, r, c)

    def try_move(self, row: int, column: int, value: int) -> Tuple[bool, List[Tuple[int, int]]]:
        """Attempt a move and return (success, conflicts).

        Conflicts is a list of coordinates that caused the move to be invalid
        (e.g. existing same-value cells or a given that was attempted to change).
        """
        n = len(self.grid)
        if not (0 <= row < n and 0 <= column < n):
            return False, []
        if (row, column) in self.givens:
            return False, [(row, column)]
        # clearing cell
        if value is None or value == 0:
            old_value = self.grid[row][column]
            # snapshot notes for affected cells
            affected = self._affected_cells(row, column)
            snapshot = {k: set(self.notes.get(k, set())) for k in affected}
            # apply change
            self.grid[row][column] = None
            if self.autonote:
                self.recompute_notes()
            self.move_log.append(('composite', [('cell', row, column, old_value, None), ('notes_snapshot', snapshot)]))
            return True, []

        # check conflicts
        conflicts: List[Tuple[int, int]] = []
        # row
        for c in range(len(self.grid[0])):
            if self.grid[row][c] == value:
                conflicts.append((row, c))
        # column
        for r in range(len(self.grid)):
            if self.grid[r][column] == value:
                conflicts.append((r, column))
        # box
        block = int(len(self.grid) ** 0.5)
        br = (row // block) * block
        bc = (column // block) * block
        for r in range(br, br + block):
            for c in range(bc, bc + block):
                if self.grid[r][c] == value:
                    conflicts.append((r, c))
        # remove duplicates and ignore the target cell itself
        conflicts = [p for p in set(conflicts) if p != (row, column)]
        if conflicts:
            return False, conflicts

        # perform move and record note snapshots for undo
        old_value = self.grid[row][column]
        affected = self._affected_cells(row, column)
        snapshot = {k: set(self.notes.get(k, set())) for k in affected}
        self.grid[row][column] = value
        if self.autonote:
            # remove this value from notes in affected cells
            for k in affected:
                s = self.notes.get(k, set())
                if value in s:
                    s.discard(value)
                    self.notes[k] = s
        # push composite entry
        self.move_log.append(('composite', [('cell', row, column, old_value, value), ('notes_snapshot', snapshot)]))
        return True, []

    def _affected_cells(self, row: int, column: int) -> Set[Tuple[int, int]]:
        n = len(self.grid)
        res: Set[Tuple[int, int]] = set()
        # row and column
        for c in range(n):
            if (row, c) != (row, column) and self.grid[row][c] is None:
                res.add((row, c))
        for r in range(n):
            if (r, column) != (row, column) and self.grid[r][column] is None:
                res.add((r, column))
        # box
        block = int(n ** 0.5)
        br = (row // block) * block
        bc = (column // block) * block
        for r in range(br, br + block):
            for c in range(bc, bc + block):
                if (r, c) != (row, column) and self.grid[r][c] is None:
                    res.add((r, c))
        # include the target cell key too for snapshot
        res.add((row, column))
        return res

    def make_move(self, row: int, column: int, value: int) -> bool:
        ok, _ = self.try_move(row, column, value)
        return ok

    def undo(self) -> bool:
        if not self.move_log:
            return False
        entry = self.move_log.pop()
        if isinstance(entry, tuple) and entry and entry[0] == 'composite':
            ops = entry[1]
            # apply ops in reverse
            for op in reversed(ops):
                if op[0] == 'cell':
                    _, r, c, old, new = op
                    self.grid[r][c] = old
                elif op[0] == 'notes_snapshot':
                    _, snapshot = op
                    for k, s in snapshot.items():
                        if s:
                            self.notes[k] = set(s)
                        elif k in self.notes:
                            del self.notes[k]
            return True
        # legacy tuple handling
        if isinstance(entry, tuple) and len(entry) == 4:
            r, c, old, new = entry
            self.grid[r][c] = old
            return True
        return False

    def empty_cell(self, row: int, column: int) -> None:
        return empty_cell(self.grid, row, column, self.move_log)


def show_help(output_func=print) -> None:
    output_func("Move format: 'row column value' (e.g. '0 0 5' to place a 5 in the top-left cell)")
    output_func("Notes format: 'notes row column' (e.g. 'notes 0 0' to find notes for the top-left cell)")
    output_func("Edit notes format: 'edit notes row column value' (e.g. 'edit notes 0 0 5' to add/remove 5 from notes for the top-left cell)")
    output_func("Find easy move: 'find easy move' (to find any cells with only one possible value)")
    output_func("Undo move: 'undo' (to undo the last move)")


def handle_command(obj, move_log, user_input, input_func=input, output_func=print) -> bool:
    """Handle one user command and return False when the session should end.

    Accept either a `Board` instance as `obj` (preferred) or the legacy
    `(grid, move_log)` pair where `obj` is the grid list and `move_log` is
    the history list.
    """
    board = obj if isinstance(obj, Board) else None
    if board is not None:
        grid = board.grid
        history = board.move_log
    else:
        grid = obj
        history = move_log

    command = user_input.lower().strip()

    if command == 'exit':
        output_func("Thanks for playing!")
        return False

    if command == 'help':
        show_help(output_func)
        return True

    if command == 'undo':
        if not undo_move(grid, history):
            output_func("No moves to undo.")
        return True

    if command == 'notes':
        try:
            row = int(input_func("Enter the row for notes: "))
            column = int(input_func("Enter the column for notes: "))
            notes = find_notes(grid, row, column)
            output_func(f"Notes for cell ({row}, {column}): {notes}")
        except (ValueError, IndexError):
            output_func("Invalid input. Please enter valid row and column numbers.")
        return True

    if command == 'edit notes':
        try:
            row = int(input_func("Enter the row for editing notes: "))
            column = int(input_func("Enter the column for editing notes: "))
            value = int(input_func("Enter the value to add/remove from notes: "))
            notes = edit_notes(grid, row, column, value)
            output_func(f"Updated notes for cell ({row}, {column}): {notes}")
        except (ValueError, IndexError):
            output_func("Invalid input. Please enter valid row, column, and value numbers.")
        return True

    if command == 'find easy move':
        easy_move = find_easy_move(grid)
        if easy_move:
            output_func(f"Easy move found: {easy_move}")
        else:
            output_func("No easy move found.")
        return True

    try:
        row, column, value = map(int, user_input.split())
    except ValueError:
        output_func("Invalid input. Please enter in the format 'row column value'.")
        return True

    if make_move(grid, row, column, value, history):
        print_grid(grid)
    else:
        output_func("Move could not be made. Try again.")
    return True


def main() -> None:
    board = Board(example_games.example_grid_1)

    print("Loaded example grid. Type 'help' for commands.")
    while True:
        board.print_grid()
        user_input = input("Enter your move, row column value: ")
        if not handle_command(board, None, user_input):
            break


if __name__ == "__main__":
    main()
