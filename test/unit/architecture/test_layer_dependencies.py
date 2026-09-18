# Purpose: enforces the L0-L6 layer rule from docs/design/packagedesign.md §3 — a package under
# src/spec_forge/ may import only from a strictly lower layer, never a peer or a higher one. This
# is the automated gate ARCHITECTURE.md's rule table cites for "acyclic; higher layer only; no
# intra-layer dependency." LAYER mirrors packagedesign.md §3 exactly and must be kept in lockstep
# whenever a package is added (packagedesign.md §6). Import resolution lives in _import_utils.py,
# shared with test_emitter_inputs.py and test_no_llm_in_emit.py.

from __future__ import annotations

from pathlib import Path

import _import_utils as iu

LAYER: dict[str, int] = {
    "core": 0,
    "ingest": 1,
    "evidence": 1,
    "library": 1,
    "persistence": 1,
    "extract": 2,
    "validate": 2,
    "emit": 3,
    "toolchain": 3,
    "repair": 4,
    "pipeline": 5,
    "api": 6,
    "cli": 6,
}


def _iter_layered_python_files() -> list[Path]:
    """Every .py file inside one of the layered subpackages — excludes spec_forge/__init__.py
    itself, which roots the package but belongs to no layer."""
    return [
        f for f in iu.iter_python_files(iu.SRC_ROOT) if len(f.relative_to(iu.SRC_ROOT).parts) >= 2
    ]


def test_layer_map_covers_every_package_directory() -> None:
    # __pycache__ is a runtime artifact of importing these packages (e.g. via pytest), not a
    # package — it didn't exist when this test was first written, before anything imported them.
    on_disk = {p.name for p in iu.SRC_ROOT.iterdir() if p.is_dir() and p.name != "__pycache__"}
    assert on_disk == set(LAYER), (
        "LAYER in this test must be updated in lockstep with src/spec_forge/ and "
        "docs/design/packagedesign.md §3 whenever a package is added or removed."
    )


def test_no_upward_or_intra_layer_imports() -> None:
    violations: list[str] = []

    for source_file in _iter_layered_python_files():
        importer_pkg = iu.package_of(source_file)
        importer_layer = LAYER[importer_pkg]

        for module in iu.resolved_imports(source_file):
            imported_pkg = iu.top_level_spec_forge_package(module)
            if imported_pkg is None or imported_pkg == importer_pkg:
                continue
            imported_layer = LAYER[imported_pkg]
            if not (imported_layer < importer_layer):
                rel = source_file.relative_to(iu.REPO_ROOT)
                violations.append(
                    f"{rel}: {importer_pkg} (L{importer_layer}) imports "
                    f"{imported_pkg} (L{imported_layer})"
                )

    assert not violations, "Layer rule violated:\n" + "\n".join(violations)
