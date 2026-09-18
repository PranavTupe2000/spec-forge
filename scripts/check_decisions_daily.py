#!/usr/bin/env python3
# Purpose: fails if DECISIONS.md has no committed entry for some day between the repo's start date
# and today (14_acceptance_criteria_and_evaluation.md §6 — "one commit per day, every day"). The
# start date is derived from the earliest commit in the repo, not hardcoded, so this script never
# needs editing as the project continues (matches D4's own reasoning: the first commit is the only
# unambiguous timestamp that exists). "Committed on day D" means some commit touching DECISIONS.md
# is dated D via `git log --date=short` (each commit's own recorded offset) — a simpler proxy than
# diffing for a genuine new D<n> entry, and a known simplification: gaming it would itself be a
# dated, visible commit in the log. Stdlib only, so it runs without the project's venv in CI.

from __future__ import annotations

import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DECISIONS_FILE = REPO_ROOT / "DECISIONS.md"


def _git_log_dates(*args: str) -> list[date]:
    result = subprocess.run(
        ["git", "log", "--format=%ad", "--date=short", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [date.fromisoformat(line) for line in result.stdout.splitlines() if line.strip()]


def repo_start_date() -> date:
    dates = _git_log_dates("--reverse")
    if not dates:
        raise SystemExit("no commits found in this repository — cannot determine a start date")
    return dates[0]


def decisions_committed_days() -> set[date]:
    return set(_git_log_dates("--", str(DECISIONS_FILE)))


def compute_missing_days(start: date, today: date, committed_days: set[date]) -> list[date]:
    """Every calendar day in [start, today] that is not in committed_days, in order."""
    missing: list[date] = []
    day = start
    while day <= today:
        if day not in committed_days:
            missing.append(day)
        day += timedelta(days=1)
    return missing


def main() -> int:
    start = repo_start_date()
    today = date.today()
    missing = compute_missing_days(start, today, decisions_committed_days())

    if missing:
        print(
            "DECISIONS.md is missing a committed entry for: "
            + ", ".join(day.isoformat() for day in missing),
            file=sys.stderr,
        )
        print(
            "Per 14_acceptance_criteria_and_evaluation.md §6: one commit per day, every day, "
            "through the hard stop. A missed day carries no weight even if backfilled later.",
            file=sys.stderr,
        )
        return 1

    print(
        f"DECISIONS.md: committed every day from {start.isoformat()} through {today.isoformat()}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
