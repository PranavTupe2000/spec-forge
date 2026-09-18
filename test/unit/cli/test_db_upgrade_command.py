# Purpose: `spec-forge db upgrade` CLI test — migrations_runner mocked, exit code matches
# success/failure, mirroring test_doctor_command.py's shape.

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from spec_forge.cli.main import app
from spec_forge.persistence import migrations_runner

runner = CliRunner()


def test_db_upgrade_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_upgrade(revision: str = "head") -> migrations_runner.UpgradeResult:
        return migrations_runner.UpgradeResult(
            ok=True, revision=revision, message=f"upgraded to {revision}"
        )

    monkeypatch.setattr(migrations_runner, "run_upgrade", _fake_upgrade)
    result = runner.invoke(app, ["db", "upgrade"])
    assert result.exit_code == 0
    assert "upgraded to head" in result.stdout


def test_db_upgrade_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(revision: str = "head") -> migrations_runner.UpgradeResult:
        raise migrations_runner.MigrationError("connection refused")

    monkeypatch.setattr(migrations_runner, "run_upgrade", _boom)
    result = runner.invoke(app, ["db", "upgrade"])
    assert result.exit_code == 1
