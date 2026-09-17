# ADR-014 — The Python package is `spec_forge`

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `src/`, all imports

## Context

The project folder map in `AGENTS.md` and the original `ARCHITECTURE.md` specified `src/spec-forge/` for the
main application source.

A hyphen is not a legal character in a Python identifier. `import spec-forge` is a syntax error, and a
hyphenated directory cannot be a regular importable package without namespace or `importlib` workarounds.

## Decision

- **Import package:** `src/spec_forge/` (underscore).
- **Distribution name:** `spec-forge` (hyphen), as is conventional on PyPI.
- **CLI command:** `spec-forge` (hyphen).
- `ARCHITECTURE.md` and the `AGENTS.md` folder map are updated to match.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Keep `src/spec-forge/` literally** | Requires `importlib` gymnastics or a namespace-package hack for no benefit, and every tool in the stack — mypy, ruff, pytest, uv — would need special handling. |
| **`src/specforge/`** | Perfectly valid and slightly terser. Rejected only because the underscore form preserves the project's two-word name and matches the distribution name character for character apart from the separator. |

## Consequences

- Python convention is followed: hyphens in distribution and command names, underscores in import names.
- The documentation inconsistency is resolved explicitly rather than being discovered by the first person to
  write an import.
