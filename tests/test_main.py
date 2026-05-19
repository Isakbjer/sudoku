import copy
import unittest

import example_games
import main


class TestSudokuBasics(unittest.TestCase):
    def setUp(self):
        self.grid = copy.deepcopy(example_games.example_grid_1)

    def test_find_notes_cell_0_0(self):
        notes = main.find_notes(self.grid, 0, 0)
        self.assertEqual(notes, {1})

    def test_is_valid_move(self):
        self.assertTrue(main.is_valid_move(self.grid, 0, 0, 1))
        self.assertFalse(main.is_valid_move(self.grid, 0, 0, 2))

    def test_make_move_enforces_validation(self):
        res = main.make_move(self.grid, 0, 0, 2)
        self.assertFalse(res)
        self.assertIsNone(self.grid[0][0])
        res2 = main.make_move(self.grid, 0, 0, 1)
        self.assertTrue(res2)
        self.assertEqual(self.grid[0][0], 1)


if __name__ == "__main__":
    unittest.main()
