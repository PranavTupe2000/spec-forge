# Purpose: the project's hard compile gate (08_modelica_emission_spec.md §6) — drives `omc` to
# check a Modelica model and turns its output into a structured result. Three things below were
# derived from a real `omc` process, not from the spec alone: its exit code stays 0 even on total
# failure (success/failure must come from parsed stdout), its script-mode result values are a
# positional stream of Modelica literals where quoted strings can span many lines, and its
# diagnostic lines are sometimes bracketed with a source location and sometimes not.

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from spec_forge.core.errors import SpecForgeError

__all__ = [
    "CheckResult",
    "Diagnostic",
    "LivenessResult",
    "OmcNotFoundError",
    "OmcOutputError",
    "OmcTimeoutError",
    "check_liveness",
    "check_msl_available",
    "find_omc",
    "generate_check_script",
    "run_check",
]


class OmcNotFoundError(SpecForgeError):
    """omc could not be located via OPENMODELICA_HOME or PATH."""


class OmcTimeoutError(SpecForgeError):
    """omc did not finish within the configured wall-clock timeout."""


class OmcOutputError(SpecForgeError):
    """omc's stdout did not have the shape this wrapper expects to parse."""


Phase = Literal["load_model", "load_file", "check_model"]
Severity = Literal["error", "warning", "notification"]


class Diagnostic(BaseModel):
    phase: Phase
    severity: Severity
    location: str | None
    message: str


class LivenessResult(BaseModel):
    available: bool
    omc_path: str | None
    version: str | None
    error: str | None


class CheckResult(BaseModel):
    ok: bool
    load_model_ok: bool
    load_file_ok: bool
    check_output: str
    diagnostics: list[Diagnostic]
    stdout: str
    duration_ms: float
    command: list[str]


def find_omc() -> Path:
    """Locate the omc executable. OPENMODELICA_HOME wins if set, else PATH. Never hardcoded
    (NFR-PORT-03) — the two candidate binary names cover both the Windows and POSIX installs."""
    home = os.environ.get("OPENMODELICA_HOME")
    if home:
        home_path = Path(home)
        for name in ("omc.exe", "omc"):
            candidate = home_path / "bin" / name
            if candidate.is_file():
                return candidate
        raise OmcNotFoundError(
            f"OPENMODELICA_HOME is set to {home!r} but no omc executable was found under "
            f"{home_path / 'bin'} (docs/devenv.md §2)"
        )
    found = shutil.which("omc")
    if found:
        return Path(found)
    raise OmcNotFoundError(
        "omc not found: set OPENMODELICA_HOME or add omc to PATH (docs/devenv.md §2)"
    )


def _split_results(stdout: str, *, count: int) -> list[str]:
    """Split omc's script-mode stdout into its positional result values. Each value is either a
    bare token (true/false) or a double-quoted Modelica string literal — which can itself contain
    literal newlines and \\"/\\\\ escapes, so this cannot be done by splitting on lines."""
    results: list[str] = []
    i = 0
    n = len(stdout)
    while i < n and len(results) < count:
        while i < n and stdout[i] in " \t\r\n":
            i += 1
        if i >= n:
            break
        if stdout[i] == '"':
            j = i + 1
            buf: list[str] = []
            while j < n:
                char = stdout[j]
                if char == "\\" and j + 1 < n:
                    buf.append(stdout[j + 1])
                    j += 2
                    continue
                if char == '"':
                    j += 1
                    break
                buf.append(char)
                j += 1
            results.append("".join(buf))
            i = j
        else:
            j = i
            while j < n and stdout[j] not in " \t\r\n":
                j += 1
            results.append(stdout[i:j])
            i = j
    if len(results) < count:
        raise OmcOutputError(
            f"expected {count} result values from omc, got {len(results)}: {stdout!r}"
        )
    return results


_DIAG_LINE_RE = re.compile(
    r"^(?:\[(?P<location>[^\]]*)\]\s*)?(?P<severity>Error|Warning|Notification):\s*(?P<message>.*)$"
)


def _parse_diagnostics(text: str, *, phase: Phase) -> list[Diagnostic]:
    """Parse a getErrorString() block into Diagnostics. Lines that don't start a new bracketed or
    unbracketed severity marker are treated as a continuation of the previous diagnostic's message;
    an unrecognised line before any marker is conservatively treated as an error rather than
    dropped, matching this project's flag-don't-silently-drop stance."""
    diagnostics: list[Diagnostic] = []
    severity: Severity | None = None
    location: str | None = None
    message_lines: list[str] = []

    def flush() -> None:
        if severity is not None:
            diagnostics.append(
                Diagnostic(
                    phase=phase,
                    severity=severity,
                    location=location,
                    message="\n".join(message_lines).rstrip(),
                )
            )

    for line in text.splitlines():
        if not line.strip():
            continue
        match = _DIAG_LINE_RE.match(line)
        if match:
            flush()
            raw_severity = match.group("severity").lower()
            severity = (
                "error"
                if raw_severity == "error"
                else "warning"
                if raw_severity == "warning"
                else "notification"
            )
            location = match.group("location")
            message_lines = [match.group("message")]
        elif severity is not None:
            message_lines.append(line)
        else:
            severity = "error"
            location = None
            message_lines = [line]
    flush()
    return diagnostics


def _interpret_check_stdout(stdout: str, *, command: list[str]) -> CheckResult:
    results = _split_results(stdout, count=6)
    load_model_ok = results[0] == "true"
    load_file_ok = results[2] == "true"
    check_output = results[4]

    diagnostics = [
        *_parse_diagnostics(results[1], phase="load_model"),
        *_parse_diagnostics(results[3], phase="load_file"),
        *_parse_diagnostics(results[5], phase="check_model"),
    ]
    has_error = any(d.severity == "error" for d in diagnostics)
    ok = load_model_ok and load_file_ok and bool(check_output.strip()) and not has_error

    return CheckResult(
        ok=ok,
        load_model_ok=load_model_ok,
        load_file_ok=load_file_ok,
        check_output=check_output,
        diagnostics=diagnostics,
        stdout=stdout,
        duration_ms=0.0,
        command=command,
    )


def check_liveness(timeout: float = 15.0) -> LivenessResult:
    """omc --version only — fast, no network. Checked at startup, not at point of use
    (NFR-REL-06). Never raises: a missing/broken toolchain is a reportable status."""
    try:
        omc_path = find_omc()
    except OmcNotFoundError as exc:
        return LivenessResult(available=False, omc_path=None, version=None, error=str(exc))

    try:
        proc = subprocess.run(
            [str(omc_path), "--version"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return LivenessResult(
            available=False,
            omc_path=str(omc_path),
            version=None,
            error=f"omc --version did not return within {timeout}s",
        )
    except OSError as exc:
        return LivenessResult(available=False, omc_path=str(omc_path), version=None, error=str(exc))

    output = (proc.stdout or "").strip() or (proc.stderr or "").strip()
    if proc.returncode != 0:
        return LivenessResult(
            available=False,
            omc_path=str(omc_path),
            version=output or None,
            error=f"omc --version exited with code {proc.returncode}",
        )
    return LivenessResult(
        available=True, omc_path=str(omc_path), version=output or None, error=None
    )


def check_msl_available(timeout: float = 60.0) -> LivenessResult:
    """loadModel(Modelica) — slower, and on a fresh machine triggers a one-time network fetch of
    the MSL package index (observed empirically). Kept separate from check_liveness deliberately so
    the fast startup probe never has a hidden network dependency."""
    try:
        omc_path = find_omc()
    except OmcNotFoundError as exc:
        return LivenessResult(available=False, omc_path=None, version=None, error=str(exc))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        script_path = tmp_path / "check_msl.mos"
        script_path.write_text("loadModel(Modelica); getErrorString();\n", encoding="utf-8")
        try:
            proc = subprocess.run(
                [str(omc_path), script_path.name],
                cwd=tmp_path,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return LivenessResult(
                available=False,
                omc_path=str(omc_path),
                version=None,
                error=(
                    f"MSL load did not complete within {timeout}s "
                    "(first run downloads the library index)"
                ),
            )

    results = _split_results(proc.stdout, count=2)
    loaded_ok = results[0] == "true"
    diagnostics = _parse_diagnostics(results[1], phase="load_model")
    has_error = any(d.severity == "error" for d in diagnostics)
    available = loaded_ok and not has_error
    return LivenessResult(
        available=available,
        omc_path=str(omc_path),
        version=None,
        error=None if available else f"loadModel(Modelica) reported errors: {results[1][:500]}",
    )


def generate_check_script(model_file: Path, model_name: str, script_path: Path) -> Path:
    """The exact loadModel/loadFile/checkModel pattern from 08_modelica_emission_spec.md §6."""
    script = (
        "loadModel(Modelica); getErrorString();\n"
        f'loadFile("{model_file.name}"); getErrorString();\n'
        f"checkModel({model_name}); getErrorString();\n"
    )
    script_path.write_text(script, encoding="utf-8")
    return script_path


def run_check(
    model_file: Path,
    model_name: str,
    *,
    work_dir: Path | None = None,
    timeout: float = 120.0,
) -> CheckResult:
    """Run the compile gate on model_file for real. Never shell=True, explicit cwd, wall-clock
    timeout. Success/failure is read entirely from parsed stdout, never from the return code —
    omc's own exit code is 0 even when checkModel fails outright."""
    omc_path = find_omc()
    work_dir = work_dir or model_file.parent
    script_path = generate_check_script(
        model_file, model_name, work_dir / f"check_{model_name}.mos"
    )
    command = [str(omc_path), script_path.name]

    start = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            cwd=work_dir,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise OmcTimeoutError(
            f"omc did not complete within {timeout}s: {' '.join(command)}"
        ) from exc
    duration_ms = (time.monotonic() - start) * 1000

    parsed = _interpret_check_stdout(proc.stdout, command=command)
    return parsed.model_copy(update={"duration_ms": duration_ms})
