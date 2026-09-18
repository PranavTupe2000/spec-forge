# Purpose: A5 — repairs patch the IR, never emitted text. repair/ has no action modules yet
# (Phase 3, 09_validation_and_repair_spec.md §5); this is the guard rail written now, waiting for
# that code, rather than retrofitted after.

from __future__ import annotations

import pytest

pytestmark = pytest.mark.xfail(
    reason=(
        "repair/ has no action modules yet (Phase 3, 09_validation_and_repair_spec.md §5). Once "
        "diagnose.py/localise.py/actions.py/loop.py exist, this test will call each repair "
        "action against a sample IR + diagnostic and assert the result is an IR patch and that "
        "no file under runs/<run_id>/ changes as a side effect."
    ),
    strict=True,
)


def test_repair_actions_patch_ir_not_emitted_text() -> None:
    from spec_forge.repair import actions  # noqa: F401 — doesn't exist yet; that's the point

    raise AssertionError("unreachable until repair/actions.py exists — see xfail reason above")
