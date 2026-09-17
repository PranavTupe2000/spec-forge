# ADR-007 — Retry, repair, degrade, ask

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `pipeline`, `repair`, `api`, `cli`

## Context

The PRD asks: *What happens on failure: retry, repair loop, degrade gracefully, or ask the user?* The inputs are
guaranteed to be incomplete and contradictory, so failure is the normal case, not the exception.

## Decision

**All four, in a fixed order:**

1. **Retry** — transient failures (network, rate limit, timeout), exponential backoff, max 3.
2. **Repair** — deterministic failures with a known repair action, bounded at 3 attempts, patching the **IR**
   and never the emitted text.
3. **Degrade** — emit the best artifact reached plus an explicit gap report. `degraded` is a **success-shaped**
   terminal state that returns HTTP 200 with artifacts.
4. **Ask** — ambiguity only a human can resolve becomes an open question.

**Guarantee: every run produces output.** A run that fails the Modelica gate still delivers the IR, the SysML,
the evidence ledger and the summary, with the failure stated at the top.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Fail fast on any error** | Produces nothing from a mostly-successful run. Directly contradicts the PRD's preference for partial-and-honest over complete-and-wrong. |
| **Repair until success, unbounded** | An unbounded loop against a live compiler is how a 10-minute demo slot disappears. |
| **Always ask the user** | Turns the product into a questionnaire. The PRD wants inference *with a stated assumption* as a valid path, not escalation of everything. |
| **Silently fall back to defaults** | The exact behaviour SF-IN-01 prohibits. A default is acceptable only when it is a registered assumption and is reported. |

## Consequences

- `degraded` must be distinct from `failed` throughout the API, the CLI and the UI, or a partial-but-honest
  result gets presented as an error.
- Every repair attempt is logged with its diagnostic, action and outcome — this is Test-and-Iterate evidence and
  the raw material for `AI-LOG.md`.
- Four of the eight known repair actions create **assumptions** rather than silent fixes, because a repair is
  itself an inference and inherits the same honesty obligation.
