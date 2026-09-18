# Purpose: A1 — emitters read only the validated IR, never raw files (ingest), LLM output
# (extract) or orchestration state (pipeline). The general layer rule already blocks emit (L3)
# importing pipeline (L5, higher), but ingest (L1) and extract (L2) are both *lower* layers emit
# is otherwise free to import — A1 is the stricter, spec-specific rule that forbids them anyway.

from __future__ import annotations

import _import_utils as iu

FORBIDDEN = {"ingest", "extract", "pipeline"}


def test_emit_never_imports_ingest_extract_or_pipeline() -> None:
    violations: list[str] = []

    for source_file in iu.iter_python_files(iu.SRC_ROOT / "emit"):
        for module in iu.resolved_imports(source_file):
            pkg = iu.top_level_spec_forge_package(module)
            if pkg in FORBIDDEN:
                rel = source_file.relative_to(iu.REPO_ROOT)
                violations.append(f"{rel}: imports {module}")

    assert not violations, "A1 violated — emit/ must read only the validated IR:\n" + "\n".join(
        violations
    )
