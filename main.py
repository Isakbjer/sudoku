# this is supposed to be the main game loop for the sudoku game



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


def make_move(grid, row, column, value):
    """Makes a move on the Sudoku grid"""
    if grid[row][column] is not None:
        print("Cell is already filled. Choose another cell.")
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
    rows = 9
    columns = 9

    empty_grid = [[None for j in range(columns)] for i in range(rows)]

    example_grid = [[None, None, 3, 5, 9, 7, 2, None, 8],
                    [2, 4, 5, None, 1, 8, 9, 3, 7],
                    [7, 9, 8, None, None, None, 6, 5, None],
                    [None, 8, 2, 4, None, 6, 1, 7, 3],
                    [3, None, None, 1, 8, 9, 5, None, None],
                    [6, 5, 1, None, 7, None, None, 9, None],
                    [5, None, 6, 7, 2, None, 4, 8, 9],
                    [None, 2, 7, 9, 4, 5, 3, 1, 6],
                    [4, None, 9, None, 6, 3, None, 2, 5]]
    
    print_grid(example_grid)


if __name__ == "__main__":    main()