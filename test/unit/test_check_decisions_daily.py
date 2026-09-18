# Purpose: tests for scripts/check_decisions_daily.py. compute_missing_days is pure and tested
# with synthetic dates; one real test runs the actual script against this repo's own git history,
# which is true today (commits touching DECISIONS.md exist on both 2026-09-17 and 2026-09-18, and
# today is 2026-09-18) — the intended, ongoing proof that the daily-commit habit is being kept.

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import check_decisions_daily as script  # noqa: E402


def test_no_missing_days_when_every_day_committed() -> None:
    start = date(2026, 9, 17)
    today = date(2026, 9, 19)
    committed = {date(2026, 9, 17), date(2026, 9, 18), date(2026, 9, 19)}
    assert script.compute_missing_days(start, today, committed) == []


def test_detects_a_gap_in_the_middle() -> None:
    start = date(2026, 9, 17)
    today = date(2026, 9, 20)
    committed = {date(2026, 9, 17), date(2026, 9, 19), date(2026, 9, 20)}
    assert script.compute_missing_days(start, today, committed) == [date(2026, 9, 18)]


def test_detects_the_start_day_itself_missing() -> None:
    start = date(2026, 9, 17)
    today = date(2026, 9, 18)
    committed = {date(2026, 9, 18)}
    assert script.compute_missing_days(start, today, committed) == [date(2026, 9, 17)]


def test_detects_today_missing() -> None:
    start = date(2026, 9, 17)
    today = date(2026, 9, 18)
    committed = {date(2026, 9, 17)}
    assert script.compute_missing_days(start, today, committed) == [date(2026, 9, 18)]


def test_single_day_range_no_gap() -> None:
    day = date(2026, 9, 17)
    assert script.compute_missing_days(day, day, {day}) == []


def test_script_passes_against_this_repos_real_history() -> None:
    result = subprocess.run(
        [sys.executable, str(script.REPO_ROOT / "scripts" / "check_decisions_daily.py")],
        cwd=script.REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "committed every day" in result.stdout
