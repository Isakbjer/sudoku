from typing import List, Optional

# Simple depth-first backtracking solver. Modifies grid in-place and
# returns True if solved, False otherwise. Empty cells are represented by None.

def solve_backtracking(grid: List[List[Optional[int]]]) -> bool:
    n = len(grid)
    # find empty cell
    for r in range(n):
        for c in range(n):
            if grid[r][c] is None:
                for val in range(1, n + 1):
                    if _is_valid(grid, r, c, val):
                        grid[r][c] = val
                        if solve_backtracking(grid):
                            return True
                        grid[r][c] = None
                return False
    return True


def _is_valid(grid: List[List[Optional[int]]], row: int, column: int, value: int) -> bool:
    n = len(grid)
    if value in grid[row]:
        return False
    for r in range(n):
        if grid[r][column] == value:
            return False
    block = int(n ** 0.5)
    br = (row // block) * block
    bc = (column // block) * block
    for r in range(br, br + block):
        for c in range(bc, bc + block):
            if grid[r][c] == value:
                return False
    return True
