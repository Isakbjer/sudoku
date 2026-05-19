# this is supposed to be the main game loop for the sudoku game
import copy

import example_games


def print_grid(grid):
    """Prints the Sudoku grid"""
    print("Current Sudoku Grid:")
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] is None:
                print(".", end=" ")
            else:
                print(grid[i][j], end=" ")
        print()  # New line after each row

# want a way to view the grid, and look and interact with the rows, columns and boxes, so everything else gets easier to implement later on
# use views, so get_row_view, get_column_view, get_box_view functions that return the respective views of the grid, and then use those views in the is_valid_move function to check if a move is valid according to Sudoku rules
def get_row_view(grid, row):
    """Returns a view of the specified row"""
    return grid[row]

def get_column_view(grid, column):
    """Returns a view of the specified column"""
    return [grid[i][column] for i in range(len(grid))]

def get_box_view(grid: list[list[int]], row: int, column: int) -> list[list[int]]:
    """Returns a view of the box specified by row and column"""
    # want to be able to use this, even for not 9x9 grids later on, but leave it with // 3 for now
    box_row = row // 3
    box_column = column // 3
    box = [[] for _ in range(3)]
    for i in range(box_row * 3, (box_row + 1) * 3):
        for j in range(box_column * 3, (box_column + 1) * 3):
            box[(i - box_row * 3)].append(grid[i][j])
    return box 

# also want to get notes, so we can see what values are possible for each cell, by looking at rows, boxes and columns
def find_notes(grid, row, column):
    """ Finds possible values for a cell, based on box, row and column views"""
    row_view = get_row_view(grid, row)
    column_view = get_column_view(grid, column)
    box_view = get_box_view(grid, row, column)
    notes = set(range(1, 10))  # Start with all possible values
    for value in row_view:
        if value is not None:
            notes.discard(value)  # Remove values already in the row
    for value in column_view:
        if value is not None:
            notes.discard(value)  # Remove values already in the column
    for box_row in box_view:
        for value in box_row:
            if value is not None:
                notes.discard(value)  # Remove values already in the box
    return notes

def edit_notes(grid, row, column, value):
    """Allows the user to edit notes for a cell, by adding or removing a value from the notes set"""
    notes = find_notes(grid, row, column)
    if value in notes:
        notes.remove(value)
        print(f"Removed {value} from notes for cell ({row}, {column}).")
    else:
        notes.add(value)
        print(f"Added {value} to notes for cell ({row}, {column}).")
    return notes


def find_easy_move(grid):
    """checks for any cells that have only one possible value, and returns the move if found"""
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] is None:
                notes = find_notes(grid, i, j)
                if len(notes) == 1:
                    return (i, j, next(iter(notes)))
    return None

def is_valid_move(grid, row, column, value):
    """Checks if a move is valid according to Sudoku rules, and if the cell is empty"""
    # check row
    # check column
    # check 3x3 box, or other sizes if the grid is not 9x9
    if not (0 <= row < len(grid) and 0 <= column < len(grid[0])):
        return False
    if not (1 <= value <= 9):
        return False
    if grid[row][column] is not None:
        return False
    row_view = get_row_view(grid, row)
    column_view = get_column_view(grid, column)
    box_view = get_box_view(grid, row, column)
    if value in row_view:
        return False
    if value in column_view:
        return False
    for box_row in box_view:
        if value in box_row:
            return False
    return True

def undo_move(grid, move_log):
    """Undoes the last move made, by restoring the previous cell value."""
    if not move_log:
        return False

    row, column, old_value, new_value = move_log.pop()
    grid[row][column] = old_value
    print(f"Undid move {new_value} at ({row}, {column}).")
    return True

def make_move(grid, row, column, value, move_log=None):
    """Makes a move on the Sudoku grid and optionally logs it for undo."""
    if not is_valid_move(grid, row, column, value):
        print("Invalid move. Try again.")
        return False
    if not (1 <= value <= 9):
        print("Value must be between 1 and 9.")
        return False
    old_value = grid[row][column]
    grid[row][column] = value
    if move_log is not None:
        move_log.append((row, column, old_value, value))
    return True

def empty_cell(grid, row, column):
    """Empties a cell on the Sudoku grid, to allow for corrections"""
    if 0 <= row < len(grid) and 0 <= column < len(grid[0]):
        grid[row][column] = None
    return None


def show_help(output_func=print):
    """Prints the available commands."""
    output_func("Move format: 'row column value' (e.g. '0 0 5' to place a 5 in the top-left cell)")
    output_func("Notes format: 'notes row column' (e.g. 'notes 0 0' to find notes for the top-left cell)")
    output_func("Edit notes format: 'edit notes row column value' (e.g. 'edit notes 0 0 5' to add/remove 5 from notes for the top-left cell)")
    output_func("Find easy move: 'find easy move' (to find any cells with only one possible value)")
    output_func("Undo move: 'undo' (to undo the last move)")


def handle_command(grid, move_log, user_input, input_func=input, output_func=print):
    """Handle one user command and return False when the session should end."""
    command = user_input.lower().strip()

    if command == 'exit':
        output_func("Thanks for playing!")
        return False

    if command == "help":
        show_help(output_func)
        return True

    if command == 'undo':
        if not undo_move(grid, move_log):
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

    if make_move(grid, row, column, value, move_log):
        print_grid(grid)
    else:
        output_func("Move could not be made. Try again.")
    return True

def main():
    grid = copy.deepcopy(example_games.example_grid_1)
    move_log = []

    while True:
        print_grid(grid)
        user_input = input("Enter your move, row column value: ")
        if not handle_command(grid, move_log, user_input):
            break



if __name__ == "__main__":    main()