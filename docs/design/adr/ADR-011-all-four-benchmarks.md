# ADR-011 — Attempt all four benchmark levels, with stated per-level expectations

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** scope, `test/`

## Context

The PRD says:

> One test case solved end to end beats four solved partially.

against

> A submission that only solves the four supplied problems has built a demo. A submission that solves them
> because its architecture generalises has built a product.

## Decision

Attempt **all four levels with equal effort**, with **honestly differentiated expectations** per level:

| Level | Target |
|---|---|
| L1, L2 | Full pipeline: compiles, simulates, matches the reference trace |
| L3 | Compiles; analytic verification against AV-11 values |
| L4 | Compiles; sequence runs past 2500 s on the StandardWater configuration, with WaterNaCl recorded as an open gap |

The L4 expectation is what the source documents themselves prescribe — the URS names StandardWater as an
integration baseline and the lab notebook records that WaterNaCl still fails at pump start. Reproducing that
honestly is the correct result.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **L1 deep only** | Safest under a 6-day, 12–15 hour-per-person budget, and the PRD's "one end to end beats four partial" appears to endorse it. Rejected because judges explicitly look for case-specific logic, and one case gives no evidence of generalisation. |
| **L1 + L2 only** | A reasonable middle. Rejected in favour of breadth because L3 and L4 exercise reasoning classes (multiphysics, parallel regions) that would otherwise go untested, and untested architecture is where case-specific shortcuts hide. |
| **Generic pipeline, no per-case tuning at all** | We do no per-case tuning in `src/` regardless (SF-SCP-01), but refusing to look at case outcomes would forfeit the Test-and-Iterate points, which require results that changed the build. |

## Consequences

- Breadth is the generalisation evidence. Four cases passing through one unbranched pipeline is the claim, and
  `test_no_case_specific_logic.py` is the proof.
- The risk is real: four cases at equal effort on a tight budget could leave all four shallow. Mitigated by
  sequential phasing (ADR-012) with a defined cut line, and by the compile gate never being allowed to regress.
- Per-level expectations are stated up front so a partial L4 reads as a planned outcome rather than a shortfall.
