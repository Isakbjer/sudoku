"""Minimal Pygame UI for the Sudoku Board.

Provides a headless-friendly `draw_board_to_surface(board)` function which
renders the current board onto a pygame.Surface (useful for testing), and a
`run(board)` entrypoint that opens a window for interactive play.
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

import example_games
import pygame

import puzzle_loader


CELL = 50
MARGIN = 20
LINE_WIDTH = 2
THICK_LINE = 4
FONT_SIZE = 28
NOTE_FONT_SIZE = 12
PANEL_HEIGHT = 120
BUTTON_SIZE = 34
BUTTON_GAP = 8

COLOR_BASE = (250, 250, 250)
COLOR_SELECTED = (195, 225, 255)
COLOR_ROW = (255, 248, 210)
COLOR_COL = (220, 245, 225)
COLOR_BOX = (245, 230, 205)
COLOR_SAME = (255, 225, 225)
COLOR_FLASH = (255, 200, 200)
COLOR_BUTTON = (235, 235, 235)
COLOR_BUTTON_ACTIVE = (200, 230, 255)
COLOR_BUTTON_NOTE = (255, 230, 180)


def _init_pygame() -> None:
    if not pygame.get_init():
        pygame.init()
        pygame.font.init()


def _grid(board):
    return board.grid if hasattr(board, "grid") else board


def _board_size(board) -> int:
    return len(_grid(board))


def _window_dimensions(board) -> Tuple[int, int]:
    size = CELL * _board_size(board) + MARGIN * 2
    return size, size + PANEL_HEIGHT


def _cell_rect(row: int, column: int) -> pygame.Rect:
    return pygame.Rect(MARGIN + column * CELL, MARGIN + row * CELL, CELL, CELL)


def _palette_rect(number: int) -> pygame.Rect:
    top = MARGIN + CELL * 9 + 24
    return pygame.Rect(MARGIN + (number - 1) * (BUTTON_SIZE + BUTTON_GAP), top, BUTTON_SIZE, BUTTON_SIZE)


def _note_button_rect() -> pygame.Rect:
    return pygame.Rect(MARGIN + 9 * (BUTTON_SIZE + BUTTON_GAP) + 16, MARGIN + CELL * 9 + 24, 96, BUTTON_SIZE)


def _clear_button_rect() -> pygame.Rect:
    return pygame.Rect(MARGIN + 9 * (BUTTON_SIZE + BUTTON_GAP) + 124, MARGIN + CELL * 9 + 24, 96, BUTTON_SIZE)


def draw_board_to_surface(
    board,
    selected: Tuple[int, int] | None = None,
    active_number: Optional[int] = None,
    show_incorrect: bool = False,
    flash_cells: set | None = None,
    show_notes: bool = False,
    note_mode: bool = False,
) -> pygame.Surface:
    """Render the board to a Surface and return it. Headless-friendly."""
    _init_pygame()
    grid = _grid(board)
    n = len(grid)
    board_size = CELL * n + MARGIN * 2
    surface = pygame.Surface((board_size, board_size + PANEL_HEIGHT))
    surface.fill((255, 255, 255))

    selected_value = None
    if selected is not None and 0 <= selected[0] < n and 0 <= selected[1] < n:
        selected_value = grid[selected[0]][selected[1]]

    same_number = active_number if active_number is not None else selected_value
    row_cells = {(selected[0], c) for c in range(n)} if selected is not None else set()
    col_cells = {(r, selected[1]) for r in range(n)} if selected is not None else set()
    box_cells = set()
    if selected is not None:
        block = int(n**0.5)
        br = (selected[0] // block) * block
        bc = (selected[1] // block) * block
        for r in range(br, br + block):
            for c in range(bc, bc + block):
                box_cells.add((r, c))
    same_number_cells = set()
    if same_number is not None:
        for r in range(n):
            for c in range(n):
                if grid[r][c] == same_number:
                    same_number_cells.add((r, c))

    font = pygame.font.SysFont(None, FONT_SIZE)
    note_font = pygame.font.SysFont(None, NOTE_FONT_SIZE)

    for r in range(n):
        for c in range(n):
            rect = _cell_rect(r, c)
            pygame.draw.rect(surface, COLOR_BASE, rect)
            if (r, c) in row_cells:
                pygame.draw.rect(surface, COLOR_ROW, rect)
            if (r, c) in col_cells:
                pygame.draw.rect(surface, COLOR_COL, rect)
            if (r, c) in box_cells:
                pygame.draw.rect(surface, COLOR_BOX, rect)
            if (r, c) in same_number_cells:
                pygame.draw.rect(surface, COLOR_SAME, rect)
            if selected == (r, c):
                pygame.draw.rect(surface, COLOR_SELECTED, rect)
            if flash_cells and (r, c) in flash_cells:
                pygame.draw.rect(surface, COLOR_FLASH, rect)

            value = grid[r][c]
            if value is not None:
                color = (20, 20, 20)
                if hasattr(board, "givens") and (r, c) not in getattr(board, "givens", set()):
                    color = (10, 50, 120)
                if show_incorrect and hasattr(board, "is_valid_move"):
                    if not board.is_valid_move(r, c, value) and (r, c) not in getattr(board, "givens", set()):
                        color = (180, 30, 30)
                txt = font.render(str(value), True, color)
                surface.blit(txt, (rect.x + (CELL - txt.get_width()) // 2, rect.y + (CELL - txt.get_height()) // 2))
            elif show_notes:
                if hasattr(board, "get_notes"):
                    notes = board.get_notes(r, c)
                elif hasattr(board, "find_notes"):
                    notes = board.find_notes(r, c)
                else:
                    notes = set()
                if notes:
                    txt = note_font.render("".join(str(num) for num in sorted(notes)), True, (120, 120, 120))
                    surface.blit(txt, (rect.x + (CELL - txt.get_width()) // 2, rect.y + (CELL - txt.get_height()) // 2))

    for i in range(n + 1):
        lw = THICK_LINE if i % int(n**0.5) == 0 else LINE_WIDTH
        y = MARGIN + i * CELL
        pygame.draw.line(surface, (0, 0, 0), (MARGIN, y), (board_size - MARGIN, y), lw)
        x = MARGIN + i * CELL
        pygame.draw.line(surface, (0, 0, 0), (x, MARGIN), (x, board_size - MARGIN), lw)

    panel_top = board_size
    pygame.draw.rect(surface, (245, 245, 245), pygame.Rect(0, panel_top, board_size, PANEL_HEIGHT))
    panel_font = pygame.font.SysFont(None, 22)
    difficulty = getattr(board, "difficulty", None) or "unknown"
    autonote = getattr(board, "autonote", False)
    status = f"{difficulty} | notes:{'on' if show_notes else 'off'} | pencil:{'on' if note_mode else 'off'} | auto:{'on' if autonote else 'off'}"
    if active_number is not None:
        status += f" | active:{active_number}"
    panel_txt = panel_font.render(status, True, (50, 50, 50))
    surface.blit(panel_txt, (MARGIN, panel_top + 8))

    for number in range(1, 10):
        rect = _palette_rect(number)
        pygame.draw.rect(surface, COLOR_BUTTON_ACTIVE if active_number == number else COLOR_BUTTON, rect, border_radius=6)
        pygame.draw.rect(surface, (120, 120, 120), rect, 1, border_radius=6)
        txt = panel_font.render(str(number), True, (25, 25, 25))
        surface.blit(txt, (rect.x + (rect.width - txt.get_width()) // 2, rect.y + (rect.height - txt.get_height()) // 2))

    note_rect = _note_button_rect()
    pygame.draw.rect(surface, COLOR_BUTTON_NOTE if note_mode else COLOR_BUTTON, note_rect, border_radius=6)
    pygame.draw.rect(surface, (120, 120, 120), note_rect, 1, border_radius=6)
    note_txt = panel_font.render("NOTES", True, (25, 25, 25))
    surface.blit(note_txt, (note_rect.x + (note_rect.width - note_txt.get_width()) // 2, note_rect.y + (note_rect.height - note_txt.get_height()) // 2))

    clear_rect = _clear_button_rect()
    pygame.draw.rect(surface, COLOR_BUTTON, clear_rect, border_radius=6)
    pygame.draw.rect(surface, (120, 120, 120), clear_rect, 1, border_radius=6)
    clear_txt = panel_font.render("CLEAR", True, (25, 25, 25))
    surface.blit(clear_txt, (clear_rect.x + (clear_rect.width - clear_txt.get_width()) // 2, clear_rect.y + (clear_rect.height - clear_txt.get_height()) // 2))

    return surface


def run(board):
    _init_pygame()
    board_size, window_height = _window_dimensions(board)
    screen = pygame.display.set_mode((board_size, window_height))
    clock = pygame.time.Clock()

    selected: Tuple[int, int] | None = None
    active_number: Optional[int] = None
    show_incorrect = False
    show_notes = False
    note_mode = False
    flash_cells = set()
    flash_end = 0

    def current_grid():
        return _grid(board)

    def update_caption():
        difficulty = getattr(board, "difficulty", None) or "unknown"
        autonote = getattr(board, "autonote", False)
        pygame.display.set_caption(
            f"Sudoku [{difficulty}] | notes:{'on' if show_notes else 'off'} | pencil:{'on' if note_mode else 'off'} | auto:{'on' if autonote else 'off'}"
        )

    def load_difficulty(difficulty: str):
        nonlocal selected, active_number, flash_cells, flash_end
        difficulty = (difficulty or "easy").lower()
        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "easy"
        try:
            puzzle = puzzle_loader.download_puzzle(difficulty=difficulty)
        except Exception as exc:
            print(f"Failed to load puzzle ({difficulty}): {exc}")
            return
        if hasattr(board, "load_grid"):
            board.load_grid(puzzle.grid, difficulty=puzzle.difficulty, source=puzzle.source, solution=puzzle.solution)
        else:
            print("Board does not support puzzle loading.")
            return
        selected = None
        active_number = None
        flash_cells = set()
        flash_end = 0
        update_caption()

    def place_number(row: int, column: int, number: int):
        if hasattr(board, "try_move"):
            return board.try_move(row, column, number)
        success = board.make_move(row, column, number)
        return success, []

    def toggle_note(row: int, column: int, number: int):
        if hasattr(board, "toggle_note"):
            return board.toggle_note(row, column, number)
        return False

    def cell_from_mouse(pos):
        mx, my = pos
        if MARGIN <= mx <= board_size - MARGIN and MARGIN <= my <= board_size - MARGIN:
            return ((my - MARGIN) // CELL, (mx - MARGIN) // CELL)
        return None

    update_caption()
    running = True
    while running:
        grid = current_grid()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                continue

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                clicked_cell = cell_from_mouse(ev.pos)
                if clicked_cell is not None:
                    row, column = clicked_cell
                    value = grid[row][column]
                    selected = (row, column)
                    if active_number is not None and value is None:
                        if note_mode:
                            toggle_note(row, column, active_number)
                        else:
                            ok, conflicts = place_number(row, column, active_number)
                            if not ok and conflicts:
                                flash_cells = set(conflicts)
                                flash_end = pygame.time.get_ticks() + 450
                            else:
                                flash_cells = set()
                    elif value is not None:
                        active_number = value
                    continue

                for number in range(1, 10):
                    if _palette_rect(number).collidepoint(ev.pos):
                        active_number = None if active_number == number else number
                        update_caption()
                        break
                else:
                    if _note_button_rect().collidepoint(ev.pos):
                        note_mode = not note_mode
                        update_caption()
                    elif _clear_button_rect().collidepoint(ev.pos):
                        active_number = None
                        update_caption()

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif pygame.K_0 <= ev.key <= pygame.K_9:
                    number = ev.key - pygame.K_0
                    if note_mode and selected is not None and grid[selected[0]][selected[1]] is None:
                        toggle_note(selected[0], selected[1], number)
                    elif active_number is None and selected is not None and grid[selected[0]][selected[1]] is None:
                        ok, conflicts = place_number(selected[0], selected[1], number)
                        if not ok and conflicts:
                            flash_cells = set(conflicts)
                            flash_end = pygame.time.get_ticks() + 450
                    else:
                        active_number = None if active_number == number else number
                        update_caption()
                elif ev.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                    if selected is not None:
                        place_number(selected[0], selected[1], 0)
                elif ev.key == pygame.K_u:
                    board.undo()
                elif ev.key == pygame.K_z and (ev.mod & pygame.KMOD_CTRL):
                    board.undo()
                elif ev.key == pygame.K_i:
                    show_incorrect = not show_incorrect
                    update_caption()
                elif ev.key == pygame.K_n:
                    show_notes = not show_notes
                    update_caption()
                elif ev.key == pygame.K_p:
                    note_mode = not note_mode
                    update_caption()
                elif ev.key == pygame.K_a and hasattr(board, "toggle_autonote"):
                    board.toggle_autonote()
                    update_caption()
                elif ev.key == pygame.K_l:
                    load_difficulty(getattr(board, "difficulty", "easy") or "easy")
                elif ev.key == pygame.K_e:
                    load_difficulty("easy")
                elif ev.key == pygame.K_m:
                    load_difficulty("medium")
                elif ev.key == pygame.K_h:
                    load_difficulty("hard")

        if flash_end and pygame.time.get_ticks() > flash_end:
            flash_cells = set()
            flash_end = 0

        surface = draw_board_to_surface(
            board,
            selected=selected,
            active_number=active_number,
            show_incorrect=show_incorrect,
            flash_cells=flash_cells,
            show_notes=show_notes,
            note_mode=note_mode,
        )
        screen.blit(surface, (0, 0))
        pygame.display.flip()
        clock.tick(30)


def test_headless():
    """Simple headless smoke test: renders the default example board."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    _init_pygame()
    from main import Board

    board = Board(example_games.example_grid_1)
    surf = draw_board_to_surface(board)
    assert isinstance(surf, pygame.Surface)
    print("headless render OK")
    return True


if __name__ == "__main__":
    from main import Board

    run(Board(example_games.example_grid_1))
