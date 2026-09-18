# Purpose: tests for the SysML v2 toolchain wrapper. Unlike omc, no SysML v2 toolchain existed on
# this machine before this project installed one (conda-forge's jupyter-sysml-kernel, the option
# devenv.md §3 calls "the Jupyter kernel"). The parser tests below run against real notebook JSON
# captured from that kernel — both a clean parse and a genuine syntax error — because, exactly like
# omc, its process exit code cannot be trusted: nbconvert returns 0 even when the kernel reports a
# parse error, since the kernel emits it as a plain stderr stream, not a Jupyter `error` output.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from spec_forge.core.errors import SpecForgeError
from spec_forge.toolchain import sysml

FIXTURES = Path(__file__).resolve().parents[2] / "testdata" / "fixtures" / "sysml_smoke"

# --- real notebook JSON, captured verbatim after nbconvert executed a clean "package Smoke { part
# def Tank; part tank1 : Tank; }" model against the real sysml kernel ---
REAL_SUCCESS_OUTPUTS = [
    {
        "data": {"text/plain": ["Package Smoke (6d93f43a-23a0-4b86-b8ef-62d626fb6254)\n"]},
        "execution_count": 1,
        "metadata": {},
        "output_type": "execute_result",
    }
]

# --- real notebook JSON, captured verbatim after nbconvert executed a model with a missing
# semicolon ("part def Tank" with no terminator) against the real sysml kernel ---
REAL_SYNTAX_ERROR_OUTPUTS = [
    {
        "name": "stderr",
        "output_type": "stream",
        "text": ["ERROR:no viable alternative at input 'part' (1.sysml line : 3 column : 5)\r\n"],
    },
    {
        "data": {"text/plain": []},
        "execution_count": 1,
        "metadata": {},
        "output_type": "execute_result",
    },
]


def _write_output_notebook(tmp_path: Path, outputs: list[dict]) -> Path:
    path = tmp_path / "out.ipynb"
    path.write_text(
        json.dumps(
            {
                "cells": [{"cell_type": "code", "outputs": outputs, "source": "irrelevant"}],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# _interpret_output_notebook — the real captured success/failure shapes
# ---------------------------------------------------------------------------


def test_interpret_success_notebook(tmp_path: Path) -> None:
    path = _write_output_notebook(tmp_path, REAL_SUCCESS_OUTPUTS)
    ok, element_summary, diagnostics = sysml._interpret_output_notebook(path)
    assert ok is True
    assert element_summary == "Package Smoke (6d93f43a-23a0-4b86-b8ef-62d626fb6254)"
    assert diagnostics == []


def test_interpret_syntax_error_notebook(tmp_path: Path) -> None:
    path = _write_output_notebook(tmp_path, REAL_SYNTAX_ERROR_OUTPUTS)
    ok, element_summary, diagnostics = sysml._interpret_output_notebook(path)
    assert ok is False
    assert element_summary is None
    assert len(diagnostics) == 1
    assert "no viable alternative" in diagnostics[0]


def test_interpret_empty_outputs_is_not_ok(tmp_path: Path) -> None:
    path = _write_output_notebook(tmp_path, [])
    ok, element_summary, diagnostics = sysml._interpret_output_notebook(path)
    assert ok is False
    assert element_summary is None


# ---------------------------------------------------------------------------
# find_sysml_command / kernel name extraction
# ---------------------------------------------------------------------------


def test_find_sysml_command_raises_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SYSML_TOOL_CMD", raising=False)
    with pytest.raises(sysml.SysmlNotConfiguredError):
        sysml.find_sysml_command()


def test_find_sysml_command_tokenizes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "SYSML_TOOL_CMD",
        "jupyter nbconvert --to notebook --execute --ExecutePreprocessor.kernel_name=sysml",
    )
    tokens = sysml.find_sysml_command()
    assert tokens[:2] == ["jupyter", "nbconvert"]
    assert "--ExecutePreprocessor.kernel_name=sysml" in tokens


def test_configured_kernel_name_extracts_from_command() -> None:
    raw = "jupyter nbconvert --execute --ExecutePreprocessor.kernel_name=sysml --other=1"
    assert sysml._configured_kernel_name(raw) == "sysml"


def test_configured_kernel_name_defaults_to_sysml() -> None:
    assert sysml._configured_kernel_name("jupyter nbconvert --execute") == "sysml"


def test_sysml_errors_are_specforge_errors() -> None:
    assert issubclass(sysml.SysmlNotConfiguredError, SpecForgeError)
    assert issubclass(sysml.SysmlTimeoutError, SpecForgeError)


# ---------------------------------------------------------------------------
# The critical gate: a trivial .sysml model parsing through OUR WRAPPER, for real.
# Skips (does not fail) only when SYSML_TOOL_CMD/the kernel isn't configured here; must run given
# the conda-forge jupyter-sysml-kernel environment installed for this project.
# ---------------------------------------------------------------------------

try:
    _LIVE = sysml.check_liveness().available
except Exception:  # pragma: no cover - liveness probe itself must never raise
    _LIVE = False

requires_real_sysml = pytest.mark.skipif(
    not _LIVE,
    reason="SysML kernel not configured/live — source environment.bat/.sh (docs/devenv.md §3)",
)


@requires_real_sysml
def test_parse_model_compiles_hand_written_smoke_model(tmp_path: Path) -> None:
    source = tmp_path / "Smoke.sysml"
    source.write_text((FIXTURES / "Smoke.sysml").read_text(encoding="utf-8"), encoding="utf-8")

    result = sysml.parse_model(source, work_dir=tmp_path)

    assert result.ok is True, f"expected a clean parse, got diagnostics: {result.diagnostics}"
    assert result.element_summary and "Smoke" in result.element_summary


@requires_real_sysml
def test_parse_model_detects_real_syntax_error(tmp_path: Path) -> None:
    source = tmp_path / "Broken.sysml"
    source.write_text((FIXTURES / "Broken.sysml").read_text(encoding="utf-8"), encoding="utf-8")

    result = sysml.parse_model(source, work_dir=tmp_path)

    assert result.ok is False
    assert result.diagnostics


@requires_real_sysml
def test_check_liveness_reports_real_kernel() -> None:
    result = sysml.check_liveness()
    assert result.available is True
    assert result.kernel_name == "sysml"
