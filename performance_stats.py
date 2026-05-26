"""Local performance and leaderboard storage for Sudoku.

Keeps two kinds of data:
- player leaderboard entries grouped by difficulty and help mode
- solver evaluation metrics for future solver implementations

The storage is local JSON so it works offline and does not require a backend.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_STATS_PATH = Path(__file__).resolve().parent / ".sudoku_stats" / "stats.json"


@dataclass(frozen=True)
class LeaderboardEntry:
    difficulty: str
    helped: bool
    time_seconds: float
    completed_at: str
    puzzle_source: str = "unknown"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SolverMetric:
    solver_name: str
    difficulty: str
    solved: bool
    accuracy: float
    solvable_count: int
    attempted_count: int
    time_seconds: float
    compute_steps: int
    recorded_at: str
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_payload() -> Dict[str, Any]:
    return {
        "leaderboard": [],
        "solver_metrics": [],
    }


def load_stats(stats_path: str | Path = DEFAULT_STATS_PATH) -> Dict[str, Any]:
    path = Path(stats_path)
    if not path.exists():
        return _default_payload()
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    payload.setdefault("leaderboard", [])
    payload.setdefault("solver_metrics", [])
    return payload


def save_stats(payload: Dict[str, Any], stats_path: str | Path = DEFAULT_STATS_PATH) -> Path:
    path = Path(stats_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path


def record_leaderboard_entry(
    difficulty: str,
    helped: bool,
    time_seconds: float,
    puzzle_source: str = "unknown",
    stats_path: str | Path = DEFAULT_STATS_PATH,
) -> LeaderboardEntry:
    payload = load_stats(stats_path)
    entry = LeaderboardEntry(
        difficulty=difficulty,
        helped=helped,
        time_seconds=float(time_seconds),
        completed_at=_utc_now(),
        puzzle_source=puzzle_source,
    )
    payload["leaderboard"].append(entry.to_dict())
    # Keep only the best 20 per difficulty/help combination.
    payload["leaderboard"] = _trim_leaderboard(payload["leaderboard"])
    save_stats(payload, stats_path)
    return entry


def _trim_leaderboard(entries: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
    grouped: Dict[tuple, List[Dict[str, Any]]] = {}
    for entry in entries:
        key = (str(entry.get("difficulty") or "unknown"), bool(entry.get("helped")))
        grouped.setdefault(key, []).append(entry)
    trimmed: List[Dict[str, Any]] = []
    for key, group in grouped.items():
        sorted_group = sorted(group, key=lambda item: float(item.get("time_seconds") or 0.0))
        trimmed.extend(sorted_group[:limit])
    return trimmed


def get_leaderboard(
    difficulty: Optional[str] = None,
    helped: Optional[bool] = None,
    stats_path: str | Path = DEFAULT_STATS_PATH,
) -> List[Dict[str, Any]]:
    payload = load_stats(stats_path)
    entries = payload["leaderboard"]
    if difficulty is not None:
        entries = [entry for entry in entries if str(entry.get("difficulty") or "unknown").lower() == difficulty.lower()]
    if helped is not None:
        entries = [entry for entry in entries if bool(entry.get("helped")) is helped]
    return sorted(entries, key=lambda item: float(item.get("time_seconds") or 0.0))


def record_solver_metric(
    solver_name: str,
    difficulty: str,
    solved: bool,
    accuracy: float,
    solvable_count: int,
    attempted_count: int,
    time_seconds: float,
    compute_steps: int,
    notes: str = "",
    stats_path: str | Path = DEFAULT_STATS_PATH,
) -> SolverMetric:
    payload = load_stats(stats_path)
    metric = SolverMetric(
        solver_name=solver_name,
        difficulty=difficulty,
        solved=solved,
        accuracy=float(accuracy),
        solvable_count=int(solvable_count),
        attempted_count=int(attempted_count),
        time_seconds=float(time_seconds),
        compute_steps=int(compute_steps),
        recorded_at=_utc_now(),
        notes=notes,
    )
    payload["solver_metrics"].append(metric.to_dict())
    save_stats(payload, stats_path)
    return metric


def get_solver_metrics(
    solver_name: Optional[str] = None,
    difficulty: Optional[str] = None,
    stats_path: str | Path = DEFAULT_STATS_PATH,
) -> List[Dict[str, Any]]:
    payload = load_stats(stats_path)
    metrics = payload["solver_metrics"]
    if solver_name is not None:
        metrics = [item for item in metrics if str(item.get("solver_name") or "") == solver_name]
    if difficulty is not None:
        metrics = [item for item in metrics if str(item.get("difficulty") or "unknown").lower() == difficulty.lower()]
    return sorted(metrics, key=lambda item: str(item.get("recorded_at") or ""))


def summarize_solver_metrics(
    solver_name: Optional[str] = None,
    difficulty: Optional[str] = None,
    stats_path: str | Path = DEFAULT_STATS_PATH,
) -> Dict[str, Any]:
    metrics = get_solver_metrics(solver_name=solver_name, difficulty=difficulty, stats_path=stats_path)
    if not metrics:
        return {
            "count": 0,
            "solved_count": 0,
            "success_rate": 0.0,
            "average_accuracy": 0.0,
            "average_time_seconds": 0.0,
            "average_compute_steps": 0.0,
        }

    count = len(metrics)
    solved_count = sum(1 for item in metrics if bool(item.get("solved")))
    total_accuracy = sum(float(item.get("accuracy") or 0.0) for item in metrics)
    total_time = sum(float(item.get("time_seconds") or 0.0) for item in metrics)
    total_compute = sum(int(item.get("compute_steps") or 0) for item in metrics)
    return {
        "count": count,
        "solved_count": solved_count,
        "success_rate": solved_count / count,
        "average_accuracy": total_accuracy / count,
        "average_time_seconds": total_time / count,
        "average_compute_steps": total_compute / count,
    }
