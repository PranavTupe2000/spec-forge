# Architecture Decision Record (ADR) Index

This is an index of key Architecture Decision Records. Remember ADRs are high level design decisions which
impact multiple packages or source files. Do not document low level design decisions like class design or
method design here.

The index format is of two types
1. `<relative document path>` : {{short 2-3 lines description of document content}}
2. {{decision description for short decisions}}

## How to use this file
- Remember ADRs are high level design decisions which impact multiple packages or source files.
- Do not document low level design decisions like class design, method design here.
- Every ADR states the alternatives that were rejected and why. The hackathon evaluation includes a decision
  walk in which judges pick entries and ask what the alternative was and why it lost — an ADR without a
  rejected alternative is not finished.

## ADR Index

- `./adr/ADR-001-single-ir-deterministic-emitters.md` : One validated IR is the sole source of truth; SysML and Modelica are produced by deterministic template emitters that never call an LLM. **The most important decision in the project.**
- `./adr/ADR-002-claude-anthropic-api.md` : Claude via the Anthropic API as the single LLM provider, with model tiering by task difficulty. No multi-provider abstraction.
- `./adr/ADR-003-three-input-modalities.md` : Support text/documents, structured engineering artifacts and images-via-vision. CAD and 3D geometry excluded.
- `./adr/ADR-004-langgraph-two-agents.md` : LangGraph orchestration with exactly two agentic (looping) nodes — repair and clarification. Everything else is a single call or plain code.
- `./adr/ADR-005-evidence-authority-tiers.md` : A 12-tier authority model with a transmission rule, and provenance as a schema-level invariant rather than a prompt instruction.
- `./adr/ADR-006-typed-component-library.md` : Domain knowledge injected as a versioned typed archetype library with paired SysML/Modelica bindings, retrieved as a closed set.
- `./adr/ADR-007-degradation-ladder.md` : On failure: retry → repair → degrade → ask. Every run produces output; `degraded` is a success-shaped terminal state.
- `./adr/ADR-008-postgres-from-phase-1.md` : PostgreSQL from Phase 1 for cross-run queries, persisted overrides and binding reuse — while the filesystem remains authoritative for artifact bytes.
- `./adr/ADR-009-saas-over-headless-core.md` : Full SaaS surface, built strictly as a client of a CLI-runnable core, so no UI or database failure can cost the compile gate.
- `./adr/ADR-010-target-user-systems-engineer.md` : The systems engineer is the stated target user; the resulting asymmetry is that a flagged gap always beats a plausible invention.
- `./adr/ADR-011-all-four-benchmarks.md` : Attempt all four benchmark levels with equal effort, with stated per-level expectations rather than uniform claims.
- `./adr/ADR-012-sequential-phases.md` : Strictly sequential implementation phases per `.agents/workingrules.md`, with a defined cut line if time runs short.
- `./adr/ADR-013-record-replay.md` : Every LLM interaction is recorded and replayable with zero network access, for test determinism and for demo survival.
- `./adr/ADR-014-python-package-naming.md` : The Python package is `spec_forge` (underscore); the distribution name remains `spec-forge`.

## Short decisions

- The IR is serialised as **JSON**, not YAML — it is machine-written and machine-read, and JSON Patch gives a standard round-trip editing mechanism for user overrides.
- **`test/`** (singular) is the test root, per the folder map in `AGENTS.md`. The cookiecutter's empty `tests/` directory is not used.
- Units are handled with **pint** rather than a hand-rolled registry; dimensional analysis is not a place to save effort.
- Element ids are **deterministic functions of canonical name and kind**, not UUIDs, because SF-ACC-05 requires two runs over the same input to be structurally comparable.
