# Purpose: tests the `spec-forge doctor` Typer command — that it prints every check and that its
# process exit code matches the underlying DoctorReport's exit_code, since CI (Phase 0 item 7) will
# gate on this command's exit code, not on parsing its printed table.

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from spec_forge.cli.main import app
from spec_forge.toolchain import doctor

runner = CliRunner()


def _report(exit_code: int) -> doctor.DoctorReport:
    severity = "error" if exit_code else "ok"
    return doctor.DoctorReport(
        checks=[doctor.DoctorCheck(name="omc", severity=severity, message="x")]
    )


def test_doctor_command_exits_zero_when_report_is_green(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor, "run_checks", lambda **_: _report(0))
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "omc" in result.stdout


def test_doctor_command_exits_nonzero_when_report_has_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(doctor, "run_checks", lambda **_: _report(1))
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "omc" in result.stdout
