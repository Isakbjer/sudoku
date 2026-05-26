import io
import json
import unittest
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


if __name__ == "__main__":
    unittest.main()
