# Purpose: A3 — no LLM call anywhere under emit/ or validate/; both are deterministic. Checked
# directly against an Anthropic SDK import, matching the spec's exact wording ("No Anthropic
# client import under emit/ or validate/") rather than inferring it from the layer graph.

from __future__ import annotations

import _import_utils as iu

SCANNED_PACKAGES = ("emit", "validate")


def test_no_anthropic_import_in_emit_or_validate() -> None:
    violations: list[str] = []

    for package in SCANNED_PACKAGES:
        for source_file in iu.iter_python_files(iu.SRC_ROOT / package):
            for module in iu.resolved_imports(source_file):
                if module == "anthropic" or module.startswith("anthropic."):
                    rel = source_file.relative_to(iu.REPO_ROOT)
                    violations.append(f"{rel}: imports {module}")

    assert not violations, (
        "A3 violated — no LLM call is permitted in emit/ or validate/:\n" + "\n".join(violations)
    )
