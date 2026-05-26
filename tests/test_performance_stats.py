import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import main
import performance_stats


class TestPerformanceStats(unittest.TestCase):
    def test_leaderboard_roundtrip_and_filtering(self):
        with TemporaryDirectory() as tmpdir:
            stats_path = Path(tmpdir) / "stats.json"
            performance_stats.record_leaderboard_entry("easy", False, 12.5, "source-a", stats_path)
            performance_stats.record_leaderboard_entry("easy", True, 9.25, "source-b", stats_path)
            performance_stats.record_leaderboard_entry("hard", False, 33.0, "source-c", stats_path)

            all_easy = performance_stats.get_leaderboard("easy", stats_path=stats_path)
            helped_easy = performance_stats.get_leaderboard("easy", helped=True, stats_path=stats_path)
            not_helped_easy = performance_stats.get_leaderboard("easy", helped=False, stats_path=stats_path)

        self.assertEqual([entry["time_seconds"] for entry in all_easy], [9.25, 12.5])
        self.assertEqual(len(helped_easy), 1)
        self.assertEqual(len(not_helped_easy), 1)
        self.assertEqual(helped_easy[0]["puzzle_source"], "source-b")

    def test_solver_metrics_summary(self):
        with TemporaryDirectory() as tmpdir:
            stats_path = Path(tmpdir) / "stats.json"
            performance_stats.record_solver_metric("dfs", "easy", True, 0.95, 18, 20, 4.5, 200, stats_path=stats_path)
            performance_stats.record_solver_metric("dfs", "easy", False, 0.60, 12, 20, 7.0, 350, stats_path=stats_path)

            summary = performance_stats.summarize_solver_metrics("dfs", "easy", stats_path=stats_path)

        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["solved_count"], 1)
        self.assertAlmostEqual(summary["success_rate"], 0.5)
        self.assertAlmostEqual(summary["average_accuracy"], 0.775)
        self.assertAlmostEqual(summary["average_time_seconds"], 5.75)
        self.assertAlmostEqual(summary["average_compute_steps"], 275.0)

    def test_is_solved_grid(self):
        solved = [
            [1, 2, 3, 4],
            [3, 4, 1, 2],
            [2, 1, 4, 3],
            [4, 3, 2, 1],
        ]
        unsolved = [
            [1, 2, 3, None],
            [3, 4, 1, 2],
            [2, 1, 4, 3],
            [4, 3, 2, 1],
        ]
        self.assertTrue(main.is_solved_grid(solved))
        self.assertFalse(main.is_solved_grid(unsolved))


if __name__ == "__main__":
    unittest.main()
