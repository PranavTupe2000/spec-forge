# Purpose: `spec-forge doctor` — the day-one command from the briefing's first instruction. Runs
# every environment probe devenv.md §5 lists (Python, uv, omc, MSL, SysML, Postgres, Anthropic key,
# writable runs/build dirs) and aggregates them into one report. omc and the SysML toolchain are
# "error" severity — Phase 0's own exit criteria treat the two toolchains as equally blocking.
# Postgres and the Anthropic key are "warn" — A7 requires the pipeline to run without either, and
# neither is wired up yet (Phase 0 item 5).

from __future__ import annotations

import os
import platform
import shutil
import socket
import sys
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel

from spec_forge.toolchain import omc, sysml

__all__ = ["DoctorCheck", "DoctorReport", "run_checks"]

Severity = Literal["ok", "warn", "error"]

MIN_PYTHON = (3, 11)


class DoctorCheck(BaseModel):
    name: str
    severity: Severity
    message: str


class DoctorReport(BaseModel):
    checks: list[DoctorCheck]

    @property
    def exit_code(self) -> int:
        return 1 if any(check.severity == "error" for check in self.checks) else 0


def _check_python_version() -> DoctorCheck:
    version = platform.python_version()
    if sys.version_info[:2] >= MIN_PYTHON:
        return DoctorCheck(name="python_version", severity="ok", message=f"Python {version}")
    return DoctorCheck(
        name="python_version",
        severity="error",
        message=f"Python {version} — 3.11+ required (NFR-PORT-02)",
    )


def _check_uv() -> DoctorCheck:
    found = shutil.which("uv")
    if found:
        return DoctorCheck(name="uv", severity="ok", message=found)
    return DoctorCheck(name="uv", severity="error", message="uv not found on PATH")


def _check_omc(timeout: float = 15.0) -> DoctorCheck:
    result = omc.check_liveness(timeout=timeout)
    if result.available:
        return DoctorCheck(name="omc", severity="ok", message=result.version or "available")
    return DoctorCheck(name="omc", severity="error", message=result.error or "omc not available")


def _check_msl(timeout: float = 60.0) -> DoctorCheck:
    result = omc.check_msl_available(timeout=timeout)
    if result.available:
        return DoctorCheck(name="msl", severity="ok", message="Modelica Standard Library loads")
    return DoctorCheck(
        name="msl", severity="warn", message=result.error or "MSL not confirmed loadable"
    )


def _check_sysml(timeout: float = 30.0) -> DoctorCheck:
    result = sysml.check_liveness(timeout=timeout)
    if result.available:
        return DoctorCheck(
            name="sysml", severity="ok", message=f"kernel {result.kernel_name!r} registered"
        )
    return DoctorCheck(
        name="sysml", severity="error", message=result.error or "SysML toolchain not available"
    )


def _check_postgres(timeout: float = 3.0) -> DoctorCheck:
    url = os.environ.get("DATABASE_URL")
    if not url:
        return DoctorCheck(
            name="postgres",
            severity="warn",
            message="DATABASE_URL not set (Postgres/Alembic land in Phase 0 item 5)",
        )
    parsed = urlsplit(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError as exc:
        return DoctorCheck(
            name="postgres", severity="warn", message=f"{host}:{port} unreachable: {exc}"
        )
    return DoctorCheck(name="postgres", severity="ok", message=f"{host}:{port} reachable")


def _check_anthropic_key() -> DoctorCheck:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return DoctorCheck(name="anthropic_key", severity="ok", message="ANTHROPIC_API_KEY is set")
    return DoctorCheck(
        name="anthropic_key",
        severity="warn",
        message="ANTHROPIC_API_KEY not set — presence only, per D2; liveness is not checked here",
    )


def _check_dir_writable(name: str, path: Path) -> DoctorCheck:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".doctor_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return DoctorCheck(name=name, severity="error", message=f"{path} not writable: {exc}")
    return DoctorCheck(name=name, severity="ok", message=f"{path} writable")


def run_checks(*, runs_dir: Path | None = None, build_dir: Path | None = None) -> DoctorReport:
    root = Path.cwd()
    runs_dir = runs_dir or root / "runs"
    build_dir = build_dir or root / "build"
    checks = [
        _check_python_version(),
        _check_uv(),
        _check_omc(),
        _check_msl(),
        _check_sysml(),
        _check_postgres(),
        _check_anthropic_key(),
        _check_dir_writable("runs_writable", runs_dir),
        _check_dir_writable("build_writable", build_dir),
    ]
    return DoctorReport(checks=checks)
