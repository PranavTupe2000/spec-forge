# Purpose: tests for `spec-forge doctor`'s check aggregation. omc/sysml/DB checks are monkeypatched
# here so this suite validates doctor's own severity/aggregation logic without needing the real
# toolchain — that end-to-end proof belongs to test_omc.py/test_sysml.py's integration tests.

from __future__ import annotations

from pathlib import Path

import pytest

from spec_forge.toolchain import doctor, omc, sysml


def _liveness(available: bool, error: str | None = None) -> omc.LivenessResult:
    return omc.LivenessResult(
        available=available, omc_path="omc" if available else None, version=None, error=error
    )


def _sysml_liveness(available: bool, error: str | None = None) -> sysml.SysmlLivenessResult:
    return sysml.SysmlLivenessResult(
        available=available,
        command=["jupyter"] if available else None,
        kernel_name="sysml",
        error=error,
    )


@pytest.fixture(autouse=True)
def _stub_toolchain_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    # Every check defaults to "green" — individual tests override just the one they're probing.
    monkeypatch.setattr(doctor.omc, "check_liveness", lambda timeout=15.0: _liveness(True))
    monkeypatch.setattr(doctor.omc, "check_msl_available", lambda timeout=60.0: _liveness(True))
    monkeypatch.setattr(doctor.sysml, "check_liveness", lambda timeout=30.0: _sysml_liveness(True))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def _severity(report: doctor.DoctorReport, name: str) -> str:
    (check,) = [c for c in report.checks if c.name == name]
    return check.severity


def test_all_green_report_has_zero_exit_code(tmp_path: Path) -> None:
    report = doctor.run_checks(runs_dir=tmp_path / "runs", build_dir=tmp_path / "build")
    assert report.exit_code == 0
    assert _severity(report, "omc") == "ok"
    assert _severity(report, "sysml") == "ok"


def test_missing_omc_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        doctor.omc, "check_liveness", lambda timeout=15.0: _liveness(False, "not found")
    )
    report = doctor.run_checks(runs_dir=tmp_path / "runs", build_dir=tmp_path / "build")
    assert _severity(report, "omc") == "error"
    assert report.exit_code == 1


def test_missing_sysml_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        doctor.sysml,
        "check_liveness",
        lambda timeout=30.0: _sysml_liveness(False, "not configured"),
    )
    report = doctor.run_checks(runs_dir=tmp_path / "runs", build_dir=tmp_path / "build")
    assert _severity(report, "sysml") == "error"
    assert report.exit_code == 1


def test_missing_database_url_is_warn_not_error(tmp_path: Path) -> None:
    report = doctor.run_checks(runs_dir=tmp_path / "runs", build_dir=tmp_path / "build")
    assert _severity(report, "postgres") == "warn"
    assert report.exit_code == 0


def test_missing_anthropic_key_is_warn_not_error(tmp_path: Path) -> None:
    report = doctor.run_checks(runs_dir=tmp_path / "runs", build_dir=tmp_path / "build")
    assert _severity(report, "anthropic_key") == "warn"
    assert report.exit_code == 0


def test_anthropic_key_present_is_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    report = doctor.run_checks(runs_dir=tmp_path / "runs", build_dir=tmp_path / "build")
    assert _severity(report, "anthropic_key") == "ok"


def test_runs_and_build_dirs_created_and_writable(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    build_dir = tmp_path / "build"
    report = doctor.run_checks(runs_dir=runs_dir, build_dir=build_dir)
    assert _severity(report, "runs_writable") == "ok"
    assert _severity(report, "build_writable") == "ok"
    assert runs_dir.is_dir()
    assert build_dir.is_dir()


def test_python_version_and_uv_present_on_this_dev_machine(tmp_path: Path) -> None:
    # Real checks, not stubbed — this machine is a valid dev environment (uv sync/pytest run here).
    report = doctor.run_checks(runs_dir=tmp_path / "runs", build_dir=tmp_path / "build")
    assert _severity(report, "python_version") == "ok"
    assert _severity(report, "uv") == "ok"
