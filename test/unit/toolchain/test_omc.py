# Purpose: tests for the omc wrapper — the project's hard compile gate. The parser tests below run
# against stdout strings actually captured from a real `omc` process (see the plan notes), not
# guessed at from the spec, because `omc`'s script-mode output has real quirks (multi-line quoted
# results, inconsistent diagnostic bracketing, an exit code that is 0 even on total failure) that
# no amount of spec-reading would surface. The one integration test at the bottom drives real omc.

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import pytest

from spec_forge.core.errors import SpecForgeError
from spec_forge.toolchain import omc

FIXTURES = Path(__file__).resolve().parents[2] / "testdata" / "fixtures" / "omc_smoke"

# --- real omc stdout shape, from a clean compile of testdata/fixtures/omc_smoke/Smoke.mo ---
# (library paths shortened for line length; the notification text and structure are verbatim)
REAL_SUCCESS_STDOUT = textwrap.dedent(
    """\
    true
    "[C:/omc/cache/index.json:0:0-0:0:readonly] Notification: Cached libraries were found and \
will be installed into C:/Users/dev/.openmodelica/libraries/.
    [C:/Users/dev/.openmodelica/libraries/Modelica 4.1.0/package.mo:0:0-0:0:readonly] \
Notification: Package installed successfully (SHA 7a4bf7de77a).
    "
    true
    ""
    "Check of Smoke completed successfully.
    Class Smoke has 1 equation(s) and 1 variable(s).
    1 of these are trivial equation(s)."
    ""
    """
)

# --- real omc stdout shape, from checkModel(DoesNotExist) on an unrelated class name ---
REAL_MISSING_CLASS_STDOUT = textwrap.dedent(
    """\
    true
    ""
    true
    ""
    ""
    "Error: Failed to load package DoesNotExist (default) using MODELICAPATH C:/omc/libraries/.
    Error: Class DoesNotExist not found in scope <top>.
    Error: Class DoesNotExist not found in scope <TOP>.
    "
    """
)

# --- real omc stdout shape, from loadFile() on a .mo file missing a semicolon ---
REAL_SYNTAX_ERROR_STDOUT = textwrap.dedent(
    """\
    true
    ""
    false
    "[C:/work/Syntax.mo:3:1-3:1:writable] Error: Missing token: SEMICOLON
    "
    ""
    "Error: Failed to load package Syntax (default) using MODELICAPATH C:/omc/libraries/.
    Error: Class Syntax not found in scope <top>.
    Error: Class Syntax not found in scope <TOP>.
    "
    """
)


# ---------------------------------------------------------------------------
# _split_results — the quote-aware positional tokenizer
# ---------------------------------------------------------------------------


def test_split_results_handles_bare_booleans_and_quoted_strings() -> None:
    results = omc._split_results('true\n""\ntrue\n', count=3)
    assert results == ["true", "", "true"]


def test_split_results_handles_multiline_quoted_string() -> None:
    results = omc._split_results(REAL_SUCCESS_STDOUT, count=6)
    assert len(results) == 6
    assert results[0] == "true"
    assert "Notification: Cached libraries were found" in results[1]
    assert results[2] == "true"
    assert results[3] == ""
    assert results[4].startswith("Check of Smoke completed successfully.")
    assert results[5] == ""


def test_split_results_unescapes_backslash_and_quote() -> None:
    results = omc._split_results(r'"a \"quoted\" word and a \\backslash"' + "\n", count=1)
    assert results == ['a "quoted" word and a \\backslash']


def test_split_results_raises_on_short_stream() -> None:
    with pytest.raises(omc.OmcOutputError):
        omc._split_results("true\n", count=6)


# ---------------------------------------------------------------------------
# _parse_diagnostics — bracketed and unbracketed severity lines
# ---------------------------------------------------------------------------


def test_parse_diagnostics_empty_string_yields_nothing() -> None:
    assert omc._parse_diagnostics("", phase="check_model") == []


def test_parse_diagnostics_bracketed_notification() -> None:
    text = (
        "[C:/lib/index.json:0:0-0:0:readonly] Notification: Cached libraries were found.\n"
        "[C:/lib/Modelica/package.mo:0:0-0:0:readonly] Notification: Package installed.\n"
    )
    diags = omc._parse_diagnostics(text, phase="load_model")
    assert [d.severity for d in diags] == ["notification", "notification"]
    assert diags[0].location == "C:/lib/index.json:0:0-0:0:readonly"
    assert diags[0].message == "Cached libraries were found."
    assert all(d.phase == "load_model" for d in diags)


def test_parse_diagnostics_unbracketed_errors() -> None:
    text = (
        "Error: Failed to load package DoesNotExist (default) using MODELICAPATH X.\n"
        "Error: Class DoesNotExist not found in scope <top>.\n"
        "Error: Class DoesNotExist not found in scope <TOP>.\n"
    )
    diags = omc._parse_diagnostics(text, phase="check_model")
    assert len(diags) == 3
    assert all(d.severity == "error" for d in diags)
    assert all(d.location is None for d in diags)


def test_parse_diagnostics_bracketed_syntax_error() -> None:
    text = "[C:/work/Syntax.mo:3:1-3:1:writable] Error: Missing token: SEMICOLON\n"
    diags = omc._parse_diagnostics(text, phase="load_file")
    assert len(diags) == 1
    assert diags[0].severity == "error"
    assert diags[0].location == "C:/work/Syntax.mo:3:1-3:1:writable"
    assert diags[0].message == "Missing token: SEMICOLON"


# ---------------------------------------------------------------------------
# _interpret_check_stdout — end-to-end parsing of a full captured transcript
# ---------------------------------------------------------------------------


def test_interpret_success_transcript_is_ok() -> None:
    result = omc._interpret_check_stdout(REAL_SUCCESS_STDOUT, command=["omc", "check_Smoke.mos"])
    assert result.ok is True
    assert result.load_model_ok is True
    assert result.load_file_ok is True
    assert result.check_output.startswith("Check of Smoke completed successfully.")
    assert not any(d.severity == "error" for d in result.diagnostics)


def test_interpret_missing_class_transcript_is_not_ok() -> None:
    result = omc._interpret_check_stdout(REAL_MISSING_CLASS_STDOUT, command=["omc", "x.mos"])
    assert result.ok is False
    assert result.check_output == ""
    assert any(d.severity == "error" for d in result.diagnostics)


def test_interpret_syntax_error_transcript_is_not_ok() -> None:
    result = omc._interpret_check_stdout(REAL_SYNTAX_ERROR_STDOUT, command=["omc", "x.mos"])
    assert result.ok is False
    assert result.load_file_ok is False
    assert any(d.severity == "error" and "SEMICOLON" in d.message for d in result.diagnostics)


# ---------------------------------------------------------------------------
# find_omc — OPENMODELICA_HOME / PATH resolution, never a hardcoded path
# ---------------------------------------------------------------------------


def test_find_omc_uses_openmodelica_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_omc = bin_dir / "omc.exe"
    fake_omc.write_text("")
    monkeypatch.setenv("OPENMODELICA_HOME", str(tmp_path))
    monkeypatch.delenv("PATH", raising=False)
    assert omc.find_omc() == fake_omc


def test_find_omc_raises_when_home_set_but_binary_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "bin").mkdir()
    monkeypatch.setenv("OPENMODELICA_HOME", str(tmp_path))
    with pytest.raises(omc.OmcNotFoundError):
        omc.find_omc()


def test_find_omc_falls_back_to_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENMODELICA_HOME", raising=False)
    fake_omc = tmp_path / ("omc.exe" if shutil.which("cmd") else "omc")
    fake_omc.write_text("")
    fake_omc.chmod(0o755)
    monkeypatch.setattr(omc.shutil, "which", lambda name: str(fake_omc) if name == "omc" else None)
    assert omc.find_omc() == fake_omc


def test_find_omc_raises_when_nothing_resolves(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENMODELICA_HOME", raising=False)
    monkeypatch.setattr(omc.shutil, "which", lambda name: None)
    with pytest.raises(omc.OmcNotFoundError):
        omc.find_omc()


def test_omc_errors_are_specforge_errors() -> None:
    assert issubclass(omc.OmcNotFoundError, SpecForgeError)
    assert issubclass(omc.OmcTimeoutError, SpecForgeError)
    assert issubclass(omc.OmcOutputError, SpecForgeError)


# ---------------------------------------------------------------------------
# The critical gate: a hand-written model compiling through OUR WRAPPER, for real.
# Skips (does not fail) only when this machine has no omc configured; must run here.
# ---------------------------------------------------------------------------

try:
    _OMC_PATH = omc.find_omc()
except omc.OmcNotFoundError:
    _OMC_PATH = None

requires_real_omc = pytest.mark.skipif(
    _OMC_PATH is None,
    reason="omc not found — set OPENMODELICA_HOME or source environment.bat/.sh (devenv.md §2)",
)


@requires_real_omc
def test_check_compiles_hand_written_smoke_model(tmp_path: Path) -> None:
    model_file = tmp_path / "Smoke.mo"
    model_file.write_text((FIXTURES / "Smoke.mo").read_text(encoding="utf-8"), encoding="utf-8")

    result = omc.run_check(model_file, "Smoke", work_dir=tmp_path)

    assert result.ok is True, f"expected a clean compile, got diagnostics: {result.diagnostics}"
    assert result.load_model_ok is True
    assert result.load_file_ok is True
    assert "Smoke" in result.check_output


@requires_real_omc
def test_check_detects_real_syntax_error(tmp_path: Path) -> None:
    model_file = tmp_path / "Broken.mo"
    model_file.write_text((FIXTURES / "Broken.mo").read_text(encoding="utf-8"), encoding="utf-8")

    result = omc.run_check(model_file, "Broken", work_dir=tmp_path)

    assert result.ok is False
    assert result.load_file_ok is False
    assert any(d.severity == "error" for d in result.diagnostics)


@requires_real_omc
def test_check_liveness_reports_real_version() -> None:
    result = omc.check_liveness()
    assert result.available is True
    assert result.version
