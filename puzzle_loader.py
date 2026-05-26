"""Puzzle download and import helpers for Sudoku.

Supports a public API that returns Sudoku puzzles with a difficulty label,
and a simple CSV importer for Kaggle-style exports.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import json
import socket
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


DEFAULT_API_URL = "https://sudoku-api.vercel.app/api/dosuku"
DEFAULT_CACHE_PATH = Path(__file__).resolve().parent / ".sudoku_cache" / "puzzles.json"


@dataclass(frozen=True)
class Puzzle:
    grid: List[List[Optional[int]]]
    difficulty: str = "unknown"
    solution: Optional[List[List[Optional[int]]]] = None
    source: str = DEFAULT_API_URL

    def to_dict(self) -> dict:
        return {
            "grid": self.grid,
            "difficulty": self.difficulty,
            "solution": self.solution,
            "source": self.source,
        }


def puzzle_from_dict(data: dict) -> Puzzle:
    return Puzzle(
        grid=_normalize_grid(data["grid"]),
        difficulty=str(data.get("difficulty") or "unknown"),
        solution=_normalize_grid(data["solution"]) if data.get("solution") is not None else None,
        source=str(data.get("source") or DEFAULT_API_URL),
    )


def _normalize_cell(value) -> Optional[int]:
    if value in (None, "", 0, "0", "."):
        return None
    return int(value)


def _normalize_grid(grid: Iterable[Iterable]) -> List[List[Optional[int]]]:
    return [[_normalize_cell(cell) for cell in row] for row in grid]


def parse_api_payload(payload: dict) -> Puzzle:
    """Parse a response from the public Sudoku API into a Puzzle."""
    newboard = payload["newboard"]
    grids = newboard["grids"]
    if not grids:
        raise ValueError("API response did not contain any grids")

    board = grids[0]
    grid = _normalize_grid(board["value"])
    solution = board.get("solution")
    normalized_solution = _normalize_grid(solution) if solution else None
    difficulty = str(board.get("difficulty") or newboard.get("difficulty") or "unknown")
    return Puzzle(grid=grid, difficulty=difficulty, solution=normalized_solution, source=DEFAULT_API_URL)


def download_puzzle(difficulty: str = "easy", timeout: int = 10) -> Puzzle:
    """Download a puzzle of the requested difficulty from the public API."""
    url = f"{DEFAULT_API_URL}?difficulty={quote_plus(difficulty)}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise RuntimeError(f"Unable to download puzzle: {exc}") from exc
    return parse_api_payload(payload)


def load_cached_puzzles(cache_path: str | Path = DEFAULT_CACHE_PATH) -> List[Puzzle]:
    cache_file = Path(cache_path)
    if not cache_file.exists():
        return []
    with cache_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [puzzle_from_dict(item) for item in payload]


def save_cached_puzzles(puzzles: List[Puzzle], cache_path: str | Path = DEFAULT_CACHE_PATH) -> Path:
    cache_file = Path(cache_path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with cache_file.open("w", encoding="utf-8") as handle:
        json.dump([puzzle.to_dict() for puzzle in puzzles], handle, indent=2)
    return cache_file


def cache_downloaded_puzzle(difficulty: str = "easy", cache_path: str | Path = DEFAULT_CACHE_PATH,
                            timeout: int = 10) -> Puzzle:
    puzzle = download_puzzle(difficulty=difficulty, timeout=timeout)
    puzzles = load_cached_puzzles(cache_path)
    puzzles.append(puzzle)
    save_cached_puzzles(puzzles, cache_path)
    return puzzle


def cache_downloaded_puzzles(difficulty: str = "easy", count: int = 1,
                             cache_path: str | Path = DEFAULT_CACHE_PATH,
                             timeout: int = 10) -> List[Puzzle]:
    puzzles = load_cached_puzzles(cache_path)
    downloaded: List[Puzzle] = []
    for _ in range(count):
        downloaded.append(download_puzzle(difficulty=difficulty, timeout=timeout))
    puzzles.extend(downloaded)
    save_cached_puzzles(puzzles, cache_path)
    return downloaded


def load_csv_puzzle_row(row: dict) -> Puzzle:
    """Parse a Kaggle-style CSV row.

    Common dataset exports use an 81-character puzzle string with 0 or . for
    blanks, and sometimes include a solution and difficulty column.
    """
    puzzle_text = row.get("puzzle") or row.get("grid") or row.get("board")
    if not puzzle_text:
        raise ValueError("CSV row does not contain a puzzle column")
    puzzle_text = puzzle_text.strip()
    if len(puzzle_text) != 81:
        raise ValueError("Puzzle string must contain exactly 81 characters")

    values = []
    for char in puzzle_text:
        values.append(_normalize_cell(char))
    grid = [values[index:index + 9] for index in range(0, 81, 9)]

    solution_text = row.get("solution") or row.get("answer")
    solution = None
    if solution_text:
        solution_text = solution_text.strip()
        if len(solution_text) == 81:
            solution_values = [_normalize_cell(char) for char in solution_text]
            solution = [solution_values[index:index + 9] for index in range(0, 81, 9)]

    difficulty = str(row.get("difficulty") or row.get("level") or "unknown")
    source = str(row.get("source") or "csv")
    return Puzzle(grid=grid, difficulty=difficulty, solution=solution, source=source)


def load_csv_puzzles(path: str | Path) -> List[Puzzle]:
    path = Path(path)
    puzzles: List[Puzzle] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            puzzles.append(load_csv_puzzle_row(row))
    return puzzles


def download_puzzles(difficulty: str = "easy", count: int = 1, timeout: int = 10) -> List[Puzzle]:
    """Download multiple puzzles by repeatedly calling the public API."""
    puzzles = []
    for _ in range(count):
        puzzles.append(download_puzzle(difficulty=difficulty, timeout=timeout))
    return puzzles
