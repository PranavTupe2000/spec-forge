# Purpose: wraps the SysML v2 toolchain configured via SYSML_TOOL_CMD (docs/devenv.md §3). The
# real, working option installed for this project is conda-forge's jupyter-sysml-kernel driven
# through `jupyter nbconvert --execute` — there is no headless CLI documented for this pilot-quality
# tool, so this module builds a one-cell probe notebook per model and parses nbconvert's output
# notebook. Like omc, the kernel's process exit code cannot be trusted: nbconvert returns 0 even
# when the kernel reports a parse error, because the kernel emits errors as a plain stderr stream
# output rather than a Jupyter protocol-level error — confirmed against the real installed kernel.

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from pydantic import BaseModel

from spec_forge.core.errors import SpecForgeError

__all__ = [
    "SysmlLivenessResult",
    "SysmlNotConfiguredError",
    "SysmlParseResult",
    "SysmlTimeoutError",
    "check_liveness",
    "find_sysml_command",
    "parse_model",
]


class SysmlNotConfiguredError(SpecForgeError):
    """SYSML_TOOL_CMD is not set."""


class SysmlTimeoutError(SpecForgeError):
    """The configured SysML tool did not finish within the wall-clock timeout."""


class SysmlLivenessResult(BaseModel):
    available: bool
    command: list[str] | None
    kernel_name: str | None
    error: str | None


class SysmlParseResult(BaseModel):
    ok: bool
    element_summary: str | None
    diagnostics: list[str]
    command: list[str]
    duration_ms: float


def find_sysml_command() -> list[str]:
    """Tokenize SYSML_TOOL_CMD. Raises if unset — there is no fallback search path, since (unlike
    omc) there is no single well-known binary name for "the SysML toolchain"."""
    raw = os.environ.get("SYSML_TOOL_CMD")
    if not raw:
        raise SysmlNotConfiguredError(
            "SYSML_TOOL_CMD is not set (docs/devenv.md §3) — e.g. "
            "'jupyter nbconvert --to notebook --execute "
            "--ExecutePreprocessor.kernel_name=sysml --ExecutePreprocessor.timeout=60'"
        )
    return shlex.split(raw)


_KERNEL_NAME_RE = re.compile(r"--ExecutePreprocessor\.kernel_name=(\S+)")


def _configured_kernel_name(raw_command: str) -> str:
    match = _KERNEL_NAME_RE.search(raw_command)
    return match.group(1) if match else "sysml"


def check_liveness(timeout: float = 30.0) -> SysmlLivenessResult:
    """Confirms SYSML_TOOL_CMD is configured, its executable resolves, and the kernel it names is
    actually registered with Jupyter (`jupyter kernelspec list --json`) — a real, specific signal,
    unlike a generic --version probe this tool doesn't document having."""
    raw = os.environ.get("SYSML_TOOL_CMD")
    if not raw:
        return SysmlLivenessResult(
            available=False,
            command=None,
            kernel_name=None,
            error="SYSML_TOOL_CMD is not set (docs/devenv.md §3)",
        )

    tokens = shlex.split(raw)
    exe = shutil.which(tokens[0]) or (tokens[0] if Path(tokens[0]).is_file() else None)
    if not exe:
        return SysmlLivenessResult(
            available=False,
            command=tokens,
            kernel_name=None,
            error=f"{tokens[0]!r} (from SYSML_TOOL_CMD) not found on PATH",
        )

    kernel_name = _configured_kernel_name(raw)
    try:
        proc = subprocess.run(
            [exe, "kernelspec", "list", "--json"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return SysmlLivenessResult(
            available=False, command=tokens, kernel_name=kernel_name, error=str(exc)
        )

    try:
        registered = json.loads(proc.stdout).get("kernelspecs", {})
    except json.JSONDecodeError:
        registered = {}

    available = kernel_name in registered
    return SysmlLivenessResult(
        available=available,
        command=tokens,
        kernel_name=kernel_name,
        error=None if available else f"kernel {kernel_name!r} is not registered with Jupyter",
    )


def _write_probe_notebook(source_text: str, kernel_name: str, notebook_path: Path) -> None:
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": source_text,
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": kernel_name,
                "language": kernel_name,
                "name": kernel_name,
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    notebook_path.write_text(json.dumps(notebook), encoding="utf-8")


def _interpret_output_notebook(output_path: Path) -> tuple[bool, str | None, list[str]]:
    """Parse nbconvert's output notebook. A clean parse is a single execute_result whose
    text/plain names the created element (e.g. "Package Smoke (<uuid>)"); a parse error is a
    stderr stream starting with "ERROR" plus an execute_result with empty text/plain — both
    shapes captured from the real kernel, not assumed from documentation."""
    data = json.loads(output_path.read_text(encoding="utf-8"))
    outputs = data["cells"][0].get("outputs", [])

    diagnostics: list[str] = []
    element_summary: str | None = None
    for output in outputs:
        output_type = output.get("output_type")
        if output_type == "stream" and output.get("name") == "stderr":
            text = "".join(output.get("text", []))
            if text.strip():
                diagnostics.append(text.strip())
        elif output_type == "execute_result":
            text_plain = output.get("data", {}).get("text/plain", [])
            text = "".join(text_plain) if isinstance(text_plain, list) else str(text_plain)
            if text.strip():
                element_summary = text.strip()

    ok = not diagnostics and element_summary is not None
    return ok, element_summary, diagnostics


def parse_model(
    source: Path,
    *,
    work_dir: Path | None = None,
    timeout: float = 120.0,
) -> SysmlParseResult:
    """Parse source through the configured SysML toolchain, for real. Never shell=True, explicit
    cwd, wall-clock timeout. Success/failure is read entirely from the output notebook's cell
    outputs, never from nbconvert's own return code (see module Purpose comment)."""
    command_prefix = find_sysml_command()
    kernel_name = _configured_kernel_name(os.environ.get("SYSML_TOOL_CMD", ""))
    work_dir = work_dir or source.parent
    notebook_path = work_dir / f"{source.stem}.sysml_probe.ipynb"
    output_path = work_dir / f"{source.stem}.sysml_probe_out.ipynb"
    _write_probe_notebook(source.read_text(encoding="utf-8"), kernel_name, notebook_path)

    command = [*command_prefix, notebook_path.name, "--output", output_path.name]
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
        raise SysmlTimeoutError(
            f"sysml parse did not complete within {timeout}s: {' '.join(command)}"
        ) from exc
    duration_ms = (time.monotonic() - start) * 1000

    if not output_path.is_file():
        return SysmlParseResult(
            ok=False,
            element_summary=None,
            diagnostics=[
                f"no output notebook was produced (exit {proc.returncode}): {proc.stderr[-2000:]}"
            ],
            command=command,
            duration_ms=duration_ms,
        )

    ok, element_summary, diagnostics = _interpret_output_notebook(output_path)
    return SysmlParseResult(
        ok=ok,
        element_summary=element_summary,
        diagnostics=diagnostics,
        command=command,
        duration_ms=duration_ms,
    )
