"""Minimal Pygame UI for the Sudoku Board.

Provides a headless-friendly `draw_board_to_surface(board)` function which
renders the current board onto a pygame.Surface (useful for testing), and a
`run(board)` entrypoint that opens a window for interactive play.
"""
from __future__ import annotations

import os
import pygame
import example_games
from typing import Tuple

CELL = 50
MARGIN = 20
LINE_WIDTH = 2
THICK_LINE = 4
FONT_SIZE = 28


def _init_pygame():
    if not pygame.get_init():
        pygame.init()
        pygame.font.init()


def draw_board_to_surface(board, selected: Tuple[int, int] | None = None, show_incorrect: bool = False,
                          flash_cells: set | None = None) -> pygame.Surface:
    """Render the board to a Surface and return it. Headless-friendly.

    `board` may be either the `Board` instance from `main.py` or a raw
    grid (list of lists). The function does not create a display window,
    so it can be used under the `SDL_VIDEODRIVER=dummy` environment.
    """
    _init_pygame()
    grid = board.grid if hasattr(board, 'grid') else board
    n = len(grid)
    size = CELL * n + MARGIN * 2
    surface = pygame.Surface((size, size))
    surface.fill((255, 255, 255))

    # draw cells and numbers
    font = pygame.font.SysFont(None, FONT_SIZE)
    for r in range(n):
        for c in range(n):
            x = MARGIN + c * CELL
            y = MARGIN + r * CELL
            rect = pygame.Rect(x, y, CELL, CELL)
            # cell background
            pygame.draw.rect(surface, (250, 250, 250), rect)
            # highlight selected cell
            if selected is not None and selected == (r, c):
                pygame.draw.rect(surface, (200, 230, 255), rect)
            # flash/conflict overlay
            if flash_cells and (r, c) in flash_cells:
                pygame.draw.rect(surface, (255, 200, 200), rect)
            val = grid[r][c]
            if val is not None:
                # givens (if provided) are drawn darker
                color = (20, 20, 20)
                if hasattr(board, 'givens') and (r, c) not in board.givens:
                    color = (10, 50, 120)
                # show incorrects if toggled
                if show_incorrect and hasattr(board, 'is_valid_move'):
                    if not board.is_valid_move(r, c, val) and (r, c) not in getattr(board, 'givens', set()):
                        color = (180, 30, 30)
                txt = font.render(str(val), True, color)
                tx = x + (CELL - txt.get_width()) // 2
                ty = y + (CELL - txt.get_height()) // 2
                surface.blit(txt, (tx, ty))

    # grid lines
    for i in range(n + 1):
        lw = THICK_LINE if i % int(n**0.5) == 0 else LINE_WIDTH
        y = MARGIN + i * CELL
        pygame.draw.line(surface, (0, 0, 0), (MARGIN, y), (size - MARGIN, y), lw)
        x = MARGIN + i * CELL
        pygame.draw.line(surface, (0, 0, 0), (x, MARGIN), (x, size - MARGIN), lw)

    return surface


def run(board):
    _init_pygame()
    grid = board.grid if hasattr(board, 'grid') else board
    n = len(grid)
    size = CELL * n + MARGIN * 2
    screen = pygame.display.set_mode((size, size))
    pygame.display.set_caption('Sudoku')
    clock = pygame.time.Clock()

    selected = (0, 0)
    show_incorrect = False
    flash_cells = set()
    flash_end = 0

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if MARGIN <= mx <= size - MARGIN and MARGIN <= my <= size - MARGIN:
                    c = (mx - MARGIN) // CELL
                    r = (my - MARGIN) // CELL
                    selected = (r, c)
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif pygame.K_0 <= ev.key <= pygame.K_9:
                    num = ev.key - pygame.K_0
                    # use try_move to get conflicts for flashing
                    if hasattr(board, 'try_move'):
                        ok, conflicts = board.try_move(selected[0], selected[1], num)
                        if not ok and conflicts:
                            flash_cells = set(conflicts)
                            flash_end = pygame.time.get_ticks() + 450
                        else:
                            flash_cells = set()
                    else:
                        board.make_move(selected[0], selected[1], num)
                elif ev.key == pygame.K_BACKSPACE or ev.key == pygame.K_DELETE:
                    if hasattr(board, 'try_move'):
                        board.try_move(selected[0], selected[1], 0)
                    else:
                        board.make_move(selected[0], selected[1], 0)
                elif ev.key == pygame.K_u:
                    board.undo()
                elif ev.key == pygame.K_z and (ev.mod & pygame.KMOD_CTRL):
                    board.undo()
                elif ev.key == pygame.K_i:
                    show_incorrect = not show_incorrect

        # update flash state
        if flash_end and pygame.time.get_ticks() > flash_end:
            flash_cells = set()
            flash_end = 0
        surf = draw_board_to_surface(board, selected, show_incorrect, flash_cells)
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        clock.tick(30)


def test_headless():
    """Simple headless smoke test: renders the default example board.

    Returns True on success, raises on failure.
    """
    # Use dummy video driver if not already set (CI/headless)
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    _init_pygame()
    from main import Board
    board = Board(example_games.example_grid_1)
    surf = draw_board_to_surface(board)
    assert isinstance(surf, pygame.Surface)
    print('headless render OK')
    return True


if __name__ == '__main__':
    # when run directly, open a window
    from main import Board
    run(Board(example_games.example_grid_1))
