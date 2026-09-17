# ADR-009 — Full SaaS surface, built on a headless core

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `api`, `cli`, `pipeline`, `frontend`

## Context

The PRD prefers SaaS, and design thinking is explicitly scored — *"how ambiguity is surfaced to the user, and
whether an engineer would actually trust and use it."*

Against that: the live evaluation includes a 10-minute demo slot containing a **binary compile check**, and the
briefing warns that setup comes out of that slot.

## Decision

Build the full SaaS surface — FastAPI + React/ShadCN/R3F — **strictly as a client of a CLI-runnable core.**

- Every artifact is produced by code reachable from `spec-forge run`.
- No extraction, precedence, validation or emission logic exists in `api/` or `frontend/`.
- `test_cli_without_frontend.py` and `test_no_db_mode.py` assert the core runs standalone.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **CLI only** | Safest, but forfeits the design-thinking points and the PRD's stated SaaS preference. The evidence view and clarifying dialogue are the product's most differentiating ideas and they need a UI to land. |
| **UI-first, with pipeline logic in request handlers** | A UI or database failure would take the compile gate with it. Unacceptable when the gate is binary and judged live. |
| **Static HTML report, no server** | Lowest risk, but no clarifying dialogue and no round-trip editing — two committed extensions. |

## Consequences

- If the frontend breaks on the 23rd, the demo falls back to the CLI and the gate still passes.
- The CLI is the reference client, and `test_cli_api_parity.py` keeps the two honest.
- The 3D view renders **placement, never shape**, and only where the inputs actually contain coordinates —
  inventing geometry would violate SF-IN-03 as surely as inventing a component.
