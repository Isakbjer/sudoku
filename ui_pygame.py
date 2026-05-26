"""Minimal Pygame UI for the Sudoku Board.

Provides a headless-friendly `draw_board_to_surface(board)` function which
renders the current board onto a pygame.Surface (useful for testing), and a
`run(board)` entrypoint that opens a window for interactive play.
"""
from __future__ import annotations

import os
from time import monotonic
from typing import Optional, Tuple

import example_games
import pygame

import main
import puzzle_loader
import performance_stats


CELL = 50
MARGIN = 20
LINE_WIDTH = 2
THICK_LINE = 4
FONT_SIZE = 28
NOTE_FONT_SIZE = 12
PANEL_HEIGHT = 220
BUTTON_SIZE = 34
BUTTON_GAP = 8
BOARD_PANEL_GAP = 14

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
COLOR_SELECTED_BORDER = (30, 90, 160)


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
    return size, size + BOARD_PANEL_GAP + PANEL_HEIGHT


def _cell_rect(row: int, column: int) -> pygame.Rect:
    return pygame.Rect(MARGIN + column * CELL, MARGIN + row * CELL, CELL, CELL)


def _palette_rect(number: int, panel_top: int) -> pygame.Rect:
    top = panel_top + 34
    return pygame.Rect(MARGIN + (number - 1) * (BUTTON_SIZE + BUTTON_GAP), top, BUTTON_SIZE, BUTTON_SIZE)


def _note_button_rect(panel_top: int) -> pygame.Rect:
    return pygame.Rect(MARGIN + 9 * (BUTTON_SIZE + BUTTON_GAP) + 16, panel_top + 34, 96, BUTTON_SIZE)


def _clear_button_rect(panel_top: int) -> pygame.Rect:
    return pygame.Rect(MARGIN + 9 * (BUTTON_SIZE + BUTTON_GAP) + 124, panel_top + 34, 96, BUTTON_SIZE)


def _undo_button_rect(panel_top: int) -> pygame.Rect:
    return pygame.Rect(MARGIN + 9 * (BUTTON_SIZE + BUTTON_GAP) + 232, panel_top + 34, 76, BUTTON_SIZE)


def _strict_button_rect(panel_top: int) -> pygame.Rect:
    return pygame.Rect(MARGIN + 9 * (BUTTON_SIZE + BUTTON_GAP) + 316, panel_top + 34, 84, BUTTON_SIZE)


def _difficulty_rect(panel_top: int, label_index: int) -> pygame.Rect:
    left = MARGIN + label_index * 88
    return pygame.Rect(left, panel_top + 84, 80, 28)


def _browse_prev_rect(panel_top: int) -> pygame.Rect:
    return pygame.Rect(MARGIN, panel_top + 134, 54, 28)


def _browse_next_rect(panel_top: int) -> pygame.Rect:
    return pygame.Rect(MARGIN + 62, panel_top + 134, 54, 28)


def _refresh_cache_rect(panel_top: int) -> pygame.Rect:
    return pygame.Rect(MARGIN + 124, panel_top + 134, 112, 28)


def _move_selection(selected: Tuple[int, int] | None, row_delta: int, column_delta: int, size: int) -> Tuple[int, int]:
    if selected is None:
        return (0, 0)
    row = (selected[0] + row_delta) % size
    column = (selected[1] + column_delta) % size
    return row, column


def draw_board_to_surface(
    board,
    selected: Tuple[int, int] | None = None,
    active_number: Optional[int] = None,
    show_incorrect: bool = False,
    flash_cells: set | None = None,
    note_mode: bool = False,
    strict_mode: bool = False,
    browser_index: Optional[int] = None,
    browser_total: Optional[int] = None,
) -> pygame.Surface:
    """Render the board to a Surface and return it. Headless-friendly."""
    _init_pygame()
    grid = _grid(board)
    n = len(grid)
    board_size = CELL * n + MARGIN * 2
    panel_top = board_size + BOARD_PANEL_GAP
    surface = pygame.Surface((board_size, board_size + BOARD_PANEL_GAP + PANEL_HEIGHT))
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
                pygame.draw.rect(surface, COLOR_SELECTED_BORDER, rect, 3)
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
            else:
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

    pygame.draw.rect(surface, (245, 245, 245), pygame.Rect(0, panel_top, board_size, PANEL_HEIGHT))
    panel_font = pygame.font.SysFont(None, 22)
    difficulty = getattr(board, "difficulty", None) or "unknown"
    autonote = getattr(board, "autonote", False)
    status = f"{difficulty} | notes:on | pencil:{'on' if note_mode else 'off'} | strict:{'on' if strict_mode else 'off'} | auto:{'on' if autonote else 'off'}"
    if active_number is not None:
        status += f" | active:{active_number}"
    if browser_index is not None and browser_total:
        status += f" | puzzle:{browser_index + 1}/{browser_total}"
    panel_txt = panel_font.render(status, True, (50, 50, 50))
    surface.blit(panel_txt, (MARGIN, panel_top + 8))

    for number in range(1, 10):
        rect = _palette_rect(number, panel_top)
        pygame.draw.rect(surface, COLOR_BUTTON_ACTIVE if active_number == number else COLOR_BUTTON, rect, border_radius=6)
        pygame.draw.rect(surface, (120, 120, 120), rect, 1, border_radius=6)
        txt = panel_font.render(str(number), True, (25, 25, 25))
        surface.blit(txt, (rect.x + (rect.width - txt.get_width()) // 2, rect.y + (rect.height - txt.get_height()) // 2))

    note_rect = _note_button_rect(panel_top)
    pygame.draw.rect(surface, COLOR_BUTTON_NOTE if note_mode else COLOR_BUTTON, note_rect, border_radius=6)
    pygame.draw.rect(surface, (120, 120, 120), note_rect, 1, border_radius=6)
    note_txt = panel_font.render("NOTES", True, (25, 25, 25))
    surface.blit(note_txt, (note_rect.x + (note_rect.width - note_txt.get_width()) // 2, note_rect.y + (note_rect.height - note_txt.get_height()) // 2))

    clear_rect = _clear_button_rect(panel_top)
    pygame.draw.rect(surface, COLOR_BUTTON, clear_rect, border_radius=6)
    pygame.draw.rect(surface, (120, 120, 120), clear_rect, 1, border_radius=6)
    clear_txt = panel_font.render("CLEAR", True, (25, 25, 25))
    surface.blit(clear_txt, (clear_rect.x + (clear_rect.width - clear_txt.get_width()) // 2, clear_rect.y + (clear_rect.height - clear_txt.get_height()) // 2))

    undo_rect = _undo_button_rect(panel_top)
    pygame.draw.rect(surface, COLOR_BUTTON, undo_rect, border_radius=6)
    pygame.draw.rect(surface, (120, 120, 120), undo_rect, 1, border_radius=6)
    undo_txt = panel_font.render("UNDO", True, (25, 25, 25))
    surface.blit(undo_txt, (undo_rect.x + (undo_rect.width - undo_txt.get_width()) // 2, undo_rect.y + (undo_rect.height - undo_txt.get_height()) // 2))

    strict_rect = _strict_button_rect(panel_top)
    pygame.draw.rect(surface, COLOR_BUTTON_ACTIVE if strict_mode else COLOR_BUTTON, strict_rect, border_radius=6)
    pygame.draw.rect(surface, (120, 120, 120), strict_rect, 1, border_radius=6)
    strict_txt = panel_font.render("STRICT", True, (25, 25, 25))
    surface.blit(strict_txt, (strict_rect.x + (strict_rect.width - strict_txt.get_width()) // 2, strict_rect.y + (strict_rect.height - strict_txt.get_height()) // 2))

    prev_rect = _browse_prev_rect(panel_top)
    next_rect = _browse_next_rect(panel_top)
    refresh_rect = _refresh_cache_rect(panel_top)
    for rect, label in ((prev_rect, "<"), (next_rect, ">"), (refresh_rect, "CACHE")):
        pygame.draw.rect(surface, COLOR_BUTTON, rect, border_radius=6)
        pygame.draw.rect(surface, (120, 120, 120), rect, 1, border_radius=6)
        txt = panel_font.render(label, True, (25, 25, 25))
        surface.blit(txt, (rect.x + (rect.width - txt.get_width()) // 2, rect.y + (rect.height - txt.get_height()) // 2))

    for index, (label, diff) in enumerate((("EASY", "easy"), ("MED", "medium"), ("HARD", "hard"))):
        rect = _difficulty_rect(panel_top, index)
        active = difficulty.lower() == diff
        pygame.draw.rect(surface, COLOR_BUTTON_ACTIVE if active else COLOR_BUTTON, rect, border_radius=6)
        pygame.draw.rect(surface, (120, 120, 120), rect, 1, border_radius=6)
        txt = panel_font.render(label, True, (25, 25, 25))
        surface.blit(txt, (rect.x + (rect.width - txt.get_width()) // 2, rect.y + (rect.height - txt.get_height()) // 2))

    return surface


def run(board):
    _init_pygame()
    board_size, window_height = _window_dimensions(board)
    screen = pygame.display.set_mode((board_size, window_height))
    clock = pygame.time.Clock()

    selected: Tuple[int, int] | None = None
    active_number: Optional[int] = None
    show_incorrect = False
    note_mode = False
    strict_mode = False
    flash_cells = set()
    flash_end = 0
    puzzle_cache = puzzle_loader.load_cached_puzzles()
    puzzle_index = 0
    puzzle_started_at = monotonic()
    completion_recorded = False

    def current_grid():
        return _grid(board)

    def update_caption():
        difficulty = getattr(board, "difficulty", None) or "unknown"
        autonote = getattr(board, "autonote", False)
        pygame.display.set_caption(
            f"Sudoku [{difficulty}] | notes:on | pencil:{'on' if note_mode else 'off'} | strict:{'on' if strict_mode else 'off'} | auto:{'on' if autonote else 'off'}"
        )

    def load_difficulty(difficulty: str):
        nonlocal selected, active_number, flash_cells, flash_end, puzzle_cache, puzzle_index, puzzle_started_at, completion_recorded
        difficulty = (difficulty or "easy").lower()
        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "easy"
        try:
            puzzle = puzzle_loader.download_puzzle(difficulty=difficulty)
        except Exception as exc:
            print(f"Failed to load puzzle ({difficulty}): {exc}")
            cached = [p for p in puzzle_loader.load_cached_puzzles() if p.difficulty.lower() == difficulty]
            if cached:
                puzzle = cached[0]
                print(f"Loaded cached {difficulty} puzzle instead.")
            else:
                print("Falling back to the built-in example puzzle.")
                puzzle = puzzle_loader.Puzzle(
                    grid=example_games.example_grid_1,
                    difficulty="example",
                    source="built-in",
                    solution=None,
                )
        if hasattr(board, "load_grid"):
            board.load_grid(puzzle.grid, difficulty=puzzle.difficulty, source=puzzle.source, solution=puzzle.solution)
        else:
            print("Board does not support puzzle loading.")
            return
        selected = None
        active_number = None
        flash_cells = set()
        flash_end = 0
        puzzle_cache = puzzle_loader.load_cached_puzzles()
        puzzle_index = 0 if puzzle_cache else -1
        puzzle_started_at = monotonic()
        completion_recorded = False
        update_caption()

    def load_puzzle(puzzle):
        nonlocal selected, active_number, flash_cells, flash_end, puzzle_started_at, completion_recorded
        if hasattr(board, "load_grid"):
            board.load_grid(puzzle.grid, difficulty=puzzle.difficulty, source=puzzle.source, solution=puzzle.solution)
        selected = None
        active_number = None
        flash_cells = set()
        flash_end = 0
        puzzle_started_at = monotonic()
        completion_recorded = False
        update_caption()

    def load_cached_puzzle(offset: int) -> None:
        nonlocal puzzle_index, puzzle_cache
        if not puzzle_cache:
            print("No cached puzzles yet. Press CACHE to download some first.")
            return
        puzzle_index = (puzzle_index + offset) % len(puzzle_cache)
        load_puzzle(puzzle_cache[puzzle_index])

    def refresh_cache() -> None:
        nonlocal puzzle_cache, puzzle_index
        try:
            puzzle_loader.cache_downloaded_puzzles("easy", count=1)
            puzzle_loader.cache_downloaded_puzzles("medium", count=1)
            puzzle_loader.cache_downloaded_puzzles("hard", count=1)
        except Exception as exc:
            print(f"Failed to refresh cache: {exc}")
            return
        puzzle_cache = puzzle_loader.load_cached_puzzles()
        puzzle_index = 0 if puzzle_cache else -1
        if puzzle_cache:
            load_puzzle(puzzle_cache[0])

    def record_completion_if_solved() -> None:
        nonlocal completion_recorded
        if completion_recorded:
            return
        grid = current_grid()
        if not main.is_solved_grid(grid):
            return
        difficulty = getattr(board, "difficulty", None) or "unknown"
        helped = bool(note_mode or (hasattr(board, "autonote") and board.autonote) or not strict_mode)
        elapsed = monotonic() - puzzle_started_at
        performance_stats.record_leaderboard_entry(
            difficulty=difficulty,
            helped=helped,
            time_seconds=elapsed,
            puzzle_source=getattr(board, "source", "unknown") or "unknown",
        )
        completion_recorded = True

    if puzzle_cache:
        load_puzzle(puzzle_cache[0])

    def place_number(row: int, column: int, number: int):
        if strict_mode:
            if hasattr(board, "try_move"):
                return board.try_move(row, column, number)
            success = board.make_move(row, column, number)
            return success, []

        if hasattr(board, "find_conflicts"):
            conflicts = board.find_conflicts(row, column, number)
        else:
            conflicts = main.find_conflicts(grid, row, column, number)
        if hasattr(board, "force_move"):
            success = board.force_move(row, column, number)
        else:
            success = board.make_move(row, column, number)
        return success, conflicts

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
                            elif conflicts:
                                flash_cells = set(conflicts)
                                flash_end = pygame.time.get_ticks() + 450
                            else:
                                flash_cells = set()
                    elif value is not None:
                        active_number = value
                    continue

                for number in range(1, 10):
                    if _palette_rect(number, board_size + BOARD_PANEL_GAP).collidepoint(ev.pos):
                        active_number = None if active_number == number else number
                        update_caption()
                        break
                else:
                    panel_top = board_size + BOARD_PANEL_GAP
                    if _browse_prev_rect(panel_top).collidepoint(ev.pos):
                        load_cached_puzzle(-1)
                    elif _browse_next_rect(panel_top).collidepoint(ev.pos):
                        load_cached_puzzle(1)
                    elif _refresh_cache_rect(panel_top).collidepoint(ev.pos):
                        refresh_cache()
                    elif _difficulty_rect(panel_top, 0).collidepoint(ev.pos):
                        load_difficulty("easy")
                    elif _difficulty_rect(panel_top, 1).collidepoint(ev.pos):
                        load_difficulty("medium")
                    elif _difficulty_rect(panel_top, 2).collidepoint(ev.pos):
                        load_difficulty("hard")
                    elif _note_button_rect(panel_top).collidepoint(ev.pos):
                        note_mode = not note_mode
                        update_caption()
                    elif _clear_button_rect(panel_top).collidepoint(ev.pos):
                        active_number = None
                        update_caption()
                    elif _undo_button_rect(panel_top).collidepoint(ev.pos):
                        board.undo()
                    elif _strict_button_rect(panel_top).collidepoint(ev.pos):
                        strict_mode = not strict_mode
                        update_caption()

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_LEFT:
                    selected = _move_selection(selected, 0, -1, n)
                elif ev.key == pygame.K_RIGHT:
                    selected = _move_selection(selected, 0, 1, n)
                elif ev.key == pygame.K_UP:
                    selected = _move_selection(selected, -1, 0, n)
                elif ev.key == pygame.K_DOWN:
                    selected = _move_selection(selected, 1, 0, n)
                elif pygame.K_0 <= ev.key <= pygame.K_9:
                    number = ev.key - pygame.K_0
                    if note_mode and selected is not None and grid[selected[0]][selected[1]] is None:
                        toggle_note(selected[0], selected[1], number)
                    elif active_number is None and selected is not None and grid[selected[0]][selected[1]] is None:
                        ok, conflicts = place_number(selected[0], selected[1], number)
                        if not ok and conflicts:
                            flash_cells = set(conflicts)
                            flash_end = pygame.time.get_ticks() + 450
                        elif conflicts:
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
                    note_mode = not note_mode
                    update_caption()
                elif ev.key == pygame.K_p:
                    strict_mode = not strict_mode
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
                elif ev.key in (pygame.K_LEFTBRACKET, pygame.K_PAGEUP):
                    load_cached_puzzle(-1)
                elif ev.key in (pygame.K_RIGHTBRACKET, pygame.K_PAGEDOWN):
                    load_cached_puzzle(1)
                elif ev.key == pygame.K_r:
                    refresh_cache()

        if flash_end and pygame.time.get_ticks() > flash_end:
            flash_cells = set()
            flash_end = 0

        record_completion_if_solved()

        surface = draw_board_to_surface(
            board,
            selected=selected,
            active_number=active_number,
            show_incorrect=show_incorrect,
            flash_cells=flash_cells,
            note_mode=note_mode,
            strict_mode=strict_mode,
            browser_index=puzzle_index if puzzle_cache else None,
            browser_total=len(puzzle_cache) if puzzle_cache else None,
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
