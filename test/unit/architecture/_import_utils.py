# Purpose: shared AST-based import resolution for the architecture test suite. Relative imports
# (`from .. import x`) are resolved against a file's own package path into a full dotted module
# name — the one genuinely tricky piece several architecture tests need (layer checking, emitter-
# input checking, no-LLM-in-emit checking), so it lives in one place rather than three copies that
# could drift out of sync.

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src" / "spec_forge"


def iter_python_files(root: Path) -> list[Path]:
    """Every .py file under root, sorted for deterministic test output."""
    return sorted(root.rglob("*.py"))


def containing_package_parts(source_file: Path) -> tuple[str, ...]:
    """Dotted-path parts of the package a file belongs to (its own dir, for __init__.py too)."""
    return source_file.parent.relative_to(REPO_ROOT / "src").parts


def resolved_imports(source_file: Path) -> set[str]:
    """Every module this file imports, as a full dotted path with relative imports resolved
    against the file's own package. Third-party and stdlib imports are included as-is (e.g.
    "anthropic", "os.path") — callers filter for what they care about."""
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    modules.add(node.module)
                continue
            parts = list(containing_package_parts(source_file))
            ups = node.level - 1
            cut = max(len(parts) - ups, 0)
            parts = parts[:cut]
            if node.module:
                parts.extend(node.module.split("."))
            if parts:
                modules.add(".".join(parts))

    return modules


def top_level_spec_forge_package(dotted: str) -> str | None:
    """Return the spec_forge subpackage a dotted module path belongs to, or None."""
    parts = dotted.split(".")
    if len(parts) < 2 or parts[0] != "spec_forge":
        return None
    return parts[1]


def package_of(source_file: Path) -> str:
    """The top-level spec_forge subpackage a source file under SRC_ROOT belongs to."""
    return source_file.relative_to(SRC_ROOT).parts[0]
