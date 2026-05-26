import io
import json
import socket
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import example_games
import main
import puzzle_loader


class TestPuzzleLoader(unittest.TestCase):
    def test_parse_api_payload_preserves_difficulty_and_solution(self):
        payload = {
            "newboard": {
                "grids": [
                    {
                        "value": [[1, 0, 3], [0, 2, 0], [3, 0, 1]],
                        "solution": [[1, 2, 3], [3, 2, 1], [3, 1, 1]],
                        "difficulty": "Hard",
                    }
                ]
            }
        }
        puzzle = puzzle_loader.parse_api_payload(payload)
        self.assertEqual(puzzle.difficulty, "Hard")
        self.assertEqual(puzzle.grid[0][1], None)
        self.assertEqual(puzzle.solution[0][1], 2)

    def test_download_puzzle_uses_api_response(self):
        payload = {
            "newboard": {
                "grids": [
                    {
                        "value": [[1, 0, 3, 0, 0, 0, 0, 0, 0]] * 9,
                        "solution": [[1, 2, 3, 4, 5, 6, 7, 8, 9]] * 9,
                        "difficulty": "Medium",
                    }
                ]
            }
        }
        response = io.StringIO(json.dumps(payload))

        class DummyContext:
            def __enter__(self):
                return response

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("puzzle_loader.urlopen", return_value=DummyContext()):
            puzzle = puzzle_loader.download_puzzle("medium")

        self.assertEqual(puzzle.difficulty, "Medium")
        self.assertEqual(puzzle.grid[0][0], 1)
        self.assertIsNone(puzzle.grid[0][1])

    def test_download_puzzle_timeout_is_wrapped(self):
        with patch("puzzle_loader.urlopen", side_effect=socket.timeout):
            with self.assertRaises(RuntimeError):
                puzzle_loader.download_puzzle("easy", timeout=0.01)

    def test_board_load_grid_resets_state(self):
        board = main.Board([[None, None], [None, None]], difficulty="example")
        board.make_move(0, 0, 1)
        board.toggle_note(0, 1, 2)
        self.assertTrue(board.move_log)

        board.load_grid([[3, None], [None, 4]], difficulty="hard", source="api")
        self.assertEqual(board.difficulty, "hard")
        self.assertEqual(board.source, "api")
        self.assertEqual(board.move_log, [])
        self.assertIn((0, 0), board.givens)
        self.assertNotIn((0, 1), board.givens)
        self.assertEqual(board.manual_notes, {})

    def test_toggle_note_and_undo(self):
        board = main.Board(example_games.example_grid_1)
        self.assertTrue(board.toggle_note(0, 0, 2))
        self.assertEqual(board.find_notes(0, 0), {1, 2})
        self.assertTrue(board.undo())
        self.assertEqual(board.find_notes(0, 0), {1})

    def test_force_move_prunes_notes_without_autonote(self):
        board = main.Board(example_games.example_grid_1)
        board.autonote = False
        board.manual_notes[(0, 1)] = {1, 5}
        board.force_move(0, 0, 1)
        self.assertNotIn(1, board.manual_notes.get((0, 1), set()))

    def test_player_cells_are_editable_but_givens_are_locked(self):
        board = main.Board(example_games.example_grid_1)
        self.assertTrue(board.is_given(0, 2))
        self.assertFalse(board.force_move(0, 2, 1))
        self.assertTrue(board.force_move(0, 0, 1))
        self.assertTrue(board.is_player_cell(0, 0))
        self.assertTrue(board.force_move(0, 0, 2))
        self.assertEqual(board.grid[0][0], 2)

    def test_cache_roundtrip(self):
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "puzzles.json"
            puzzles = [
                puzzle_loader.Puzzle(grid=[[None, 1], [2, None]], difficulty="easy", source="one"),
                puzzle_loader.Puzzle(grid=[[1, None], [None, 2]], difficulty="hard", source="two"),
            ]
            puzzle_loader.save_cached_puzzles(puzzles, cache_path)
            loaded = puzzle_loader.load_cached_puzzles(cache_path)

        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].difficulty, "easy")
        self.assertEqual(loaded[1].source, "two")

    def test_cache_downloaded_puzzles_appends_downloads(self):
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "puzzles.json"
            downloaded = [
                puzzle_loader.Puzzle(grid=[[None, None], [None, None]], difficulty="easy", source="one"),
                puzzle_loader.Puzzle(grid=[[1, None], [None, 2]], difficulty="medium", source="two"),
            ]

            with patch("puzzle_loader.download_puzzle", side_effect=downloaded):
                result = puzzle_loader.cache_downloaded_puzzles("easy", count=2, cache_path=cache_path)

            self.assertEqual([p.difficulty for p in result], ["easy", "medium"])
            cached = puzzle_loader.load_cached_puzzles(cache_path)
            self.assertEqual(len(cached), 2)
            self.assertEqual(cached[0].source, "one")


if __name__ == "__main__":
    unittest.main()
