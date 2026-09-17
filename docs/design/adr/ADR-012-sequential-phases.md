# ADR-012 — Strictly sequential implementation phases

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `docs/implementation_plan.md`, team workflow

## Context

`.agents/workingrules.md` requires:

> Do not start next phase till the previous phase is fully implemented and user explicitly asks for
> implementation of next phase.

The team is four people with 12–15 hours each, over six days.

## Decision

**Strictly sequential phases.** Phase N+1 does not begin until Phase N's acceptance tests pass and the user
authorises the next phase.

Within a phase, work is split across the team by module, but the phase gate is collective.

A **defined cut line**: Phases 0–3 are the committed deliverable. Phases 4–5 are delivered if time allows, and
their absence does not affect the compile gate or any minimum-scope requirement.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Four parallel workstreams behind a frozen IR contract** | Faster on paper, and genuinely attractive for a 4-person team. Rejected because it contradicts the project's own working rules, and because a frozen-on-day-1 IR contract is a fiction — the IR changed materially while writing these specs and will change again on contact with real extraction. |
| **Two pairs, two tracks** | Fewer integration seams, but the same contract-freezing problem, and it splits the team into halves that cannot answer individual probes about the other half's work. |
| **No phases, continuous integration of whatever is ready** | No gate means no moment where the compile check is verified green, which is the one thing that must never regress. |

## Consequences

- Integration risk is low; schedule risk is higher. Mitigated by the cut line and by Phase 1 being a complete
  vertical slice rather than a horizontal layer.
- Everyone works on every phase, which directly serves the individual-probe requirement — the Method score caps
  at 27/45 if only one member can explain the design.
- The phase gate is an acceptance-test run, not an opinion.
