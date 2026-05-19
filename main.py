# this is supposed to be the main game loop for the sudoku game


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




def make_move(grid, row, column, value):
    """Makes a move on the Sudoku grid"""
    if not is_valid_move(grid, row, column, value):
        print("Invalid move. Try again.")
        return False
    if not (1 <= value <= 9):
        print("Value must be between 1 and 9.")
        return False
    grid[row][column] = value
    return True

def empty_cell(grid, row, column):
    """Empties a cell on the Sudoku grid, to allow for corrections"""
    if 0 <= row < len(grid) and 0 <= column < len(grid[0]):
        grid[row][column] = None
    return None

def main():
    example_grid = example_games.example_grid_1
    print_grid(example_grid)
    box = get_box_view(example_grid, 0, 0)
    print("Box view for (0, 0):", box)
    notes = find_notes(example_grid, 0, 0)
    print("Notes for (0, 0):", notes)
    easy_move = find_easy_move(example_grid)
    if easy_move:
        print("Easy move found:", easy_move)
    else:        print("No easy move found.")

    # main game loop, asking for user input needing to be in the format "row column value", and then making the move if it's valid, and printing the grid after each move, and allowing the user to exit the game by typing "exit"

    # want to be able to find the notes for a cell, and edit the notes, and use find easy move function as a player as well 
    while True:
        print_grid(example_grid)
        user_input = input("Enter your move (row column value), notes, edit notes,find easy move or 'exit' to quit: ")
        if user_input.lower() == 'exit':
            print("Thanks for playing!")
            break

        elif user_input.lower() == 'notes':
            row = int(input("Enter the row for notes: "))
            column = int(input("Enter the column for notes: "))
            notes = find_notes(example_grid, row, column)
            print(f"Notes for cell ({row}, {column}): {notes}")
            continue

        elif user_input.lower() == 'edit notes':
            row = int(input("Enter the row for editing notes: "))
            column = int(input("Enter the column for editing notes: "))
            value = int(input("Enter the value to add/remove from notes: "))
            notes = edit_notes(example_grid, row, column, value)
            print(f"Updated notes for cell ({row}, {column}): {notes}")
            continue

        elif user_input.lower() == 'find easy move':
            easy_move = find_easy_move(example_grid)
            if easy_move:
                print("Easy move found:", easy_move)
            else:
                print("No easy move found.")
            continue

        try:
            row, column, value = map(int, user_input.split())
            if make_move(example_grid, row, column, value):
                print_grid(example_grid)
            else:
                print("Move could not be made. Try again.")
        
        # want this to only be printed when nothing else is being printed, so that it doesn't interfere with the other outputs, but for now just print it whenever there's an error in the input format
        except ValueError:
            print("Invalid input. Please enter in the format 'row column value'.")




if __name__ == "__main__":    main()