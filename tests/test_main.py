import copy
from io import StringIO
from unittest.mock import patch
import unittest

import example_games
import main


class TestSudokuBasics(unittest.TestCase):
    def setUp(self):
        self.grid = copy.deepcopy(example_games.example_grid_1)

    def _make_io(self, inputs):
        input_iter = iter(inputs)
        outputs = []

        def fake_input(prompt=""):
            return next(input_iter)

        def fake_output(message):
            outputs.append(message)

        return fake_input, fake_output, outputs

    def test_get_row_view(self):
        self.assertEqual(main.get_row_view(self.grid, 0), self.grid[0])

    def test_get_column_view(self):
        self.assertEqual(main.get_column_view(self.grid, 0), [row[0] for row in self.grid])

    def test_get_box_view(self):
        box = main.get_box_view(self.grid, 0, 0)
        self.assertEqual(
            box,
            [[None, None, 3], [2, 4, 5], [7, 9, 8]],
        )

    def test_print_grid(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            main.print_grid([[None, 1], [2, None]])
        output = fake_out.getvalue()
        self.assertIn("Current Sudoku Grid:", output)
        self.assertIn(". 1", output)
        self.assertIn("2 .", output)

    def test_find_notes_cell_0_0(self):
        notes = main.find_notes(self.grid, 0, 0)
        self.assertEqual(notes, {1})

    def test_edit_notes_add_and_remove(self):
        notes = main.find_notes(self.grid, 0, 0)
        self.assertEqual(notes, {1})

        removed = main.edit_notes(self.grid, 0, 0, 1)
        self.assertEqual(removed, set())

        added = main.edit_notes(self.grid, 0, 0, 2)
        self.assertEqual(added, {1, 2})

    def test_is_valid_move(self):
        self.assertTrue(main.is_valid_move(self.grid, 0, 0, 1))
        self.assertFalse(main.is_valid_move(self.grid, 0, 0, 2))

    def test_find_easy_move(self):
        easy = main.find_easy_move(self.grid)
        self.assertEqual(easy, (0, 0, 1))

    def test_make_move_enforces_validation(self):
        move_log = []

        res = main.make_move(self.grid, 0, 0, 2, move_log)
        self.assertFalse(res)
        self.assertIsNone(self.grid[0][0])
        self.assertEqual(move_log, [])

        res2 = main.make_move(self.grid, 0, 0, 1, move_log)
        self.assertTrue(res2)
        self.assertEqual(self.grid[0][0], 1)
        self.assertEqual(move_log, [(0, 0, None, 1)])

    def test_handle_command_help(self):
        fake_input, fake_output, outputs = self._make_io([])
        result = main.handle_command(self.grid, [], "help", fake_input, fake_output)
        self.assertTrue(result)
        self.assertTrue(any("Move format" in line for line in outputs))

    def test_handle_command_exit(self):
        fake_input, fake_output, outputs = self._make_io([])
        result = main.handle_command(self.grid, [], "exit", fake_input, fake_output)
        self.assertFalse(result)
        self.assertEqual(outputs, ["Thanks for playing!"])

    def test_handle_command_undo_without_moves(self):
        fake_input, fake_output, outputs = self._make_io([])
        result = main.handle_command(self.grid, [], "undo", fake_input, fake_output)
        self.assertTrue(result)
        self.assertEqual(outputs, ["No moves to undo."])

    def test_handle_command_notes(self):
        fake_input, fake_output, outputs = self._make_io(["0", "0"])
        result = main.handle_command(self.grid, [], "notes", fake_input, fake_output)
        self.assertTrue(result)
        self.assertTrue(any("Notes for cell (0, 0):" in line for line in outputs))

    def test_handle_command_edit_notes(self):
        fake_input, fake_output, outputs = self._make_io(["0", "0", "1"])
        result = main.handle_command(self.grid, [], "edit notes", fake_input, fake_output)
        self.assertTrue(result)
        self.assertTrue(any("Updated notes for cell (0, 0):" in line for line in outputs))

    def test_handle_command_invalid_move_input(self):
        fake_input, fake_output, outputs = self._make_io([])
        result = main.handle_command(self.grid, [], "not a move", fake_input, fake_output)
        self.assertTrue(result)
        self.assertEqual(outputs, ["Invalid input. Please enter in the format 'row column value'."])

    def test_undo_move(self):
        move_log = []
        main.make_move(self.grid, 0, 0, 1, move_log)
        self.assertTrue(main.undo_move(self.grid, move_log))
        self.assertIsNone(self.grid[0][0])
        self.assertEqual(move_log, [])
        self.assertFalse(main.undo_move(self.grid, move_log))

    def test_empty_cell(self):
        grid = copy.deepcopy(example_games.example_grid_1)
        main.empty_cell(grid, 0, 2)
        self.assertIsNone(grid[0][2])
        main.empty_cell(grid, 99, 99)
        self.assertEqual(grid[0][0], None)


if __name__ == "__main__":
    unittest.main()
