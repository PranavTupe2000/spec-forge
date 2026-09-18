# Purpose: A7 — the pipeline runs without the frontend. cli/main.py has no `run` command yet
# (Phase 1, 16_pipeline_orchestration_spec.md); this is the guard rail written now, waiting for
# that code, rather than retrofitted after.

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[3]
L1_BUNDLE = REPO_ROOT / "test" / "testdata" / "benchmarks" / "L1_two_tank"

pytestmark = pytest.mark.xfail(
    reason=(
        "`spec-forge run` and pipeline/ don't exist yet (Phase 1, "
        "16_pipeline_orchestration_spec.md). Once `run` is registered, this test will invoke it "
        "against test/testdata/benchmarks/L1_two_tank with frontend/ untouched and assert a "
        "completed run — the backend needs nothing from frontend/ (rule A7)."
    ),
    strict=True,
)


def test_run_completes_without_frontend(tmp_path: Path) -> None:
    from spec_forge.cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["run", str(L1_BUNDLE), "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
