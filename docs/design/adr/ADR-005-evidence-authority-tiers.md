# ADR-005 — Authority tiers, the transmission rule, and provenance as an invariant

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `core`, `evidence`, `extract`, `validate`

## Context

The PRD's honesty requirements are the product's differentiator:

> Missing information must be either inferred with a stated assumption, or surfaced as a question. It must not
> be silently invented. Contradictions must be flagged rather than resolved arbitrarily.

Analysis of the four bundles showed every case is built on the same trap: a released spec, a later approved
change record that supersedes it, a stale legacy artifact, and informal notes that agree with the change. The
supplied engineering registers even ship a `Change_Log` with a **Precedence Note** column and a `Source_Index`
with a **Reliability** column.

## Decision

1. A **12-tier authority model** (0 user override … 11 legacy code), assigned per source document and per claim.
2. **The transmission rule**: authority attaches to the *record cited*, not the *medium*. An email announcing an
   approved change record inherits that record's tier.
3. A deterministic resolution algorithm `PRE-01` — tier, then effective date, then specificity — that **always**
   emits a conflict record retaining every losing position, even when resolution is unambiguous.
4. Claims are never merged across `value_kind`. A nominal design value and an as-built measurement are not a
   contradiction.
5. **Provenance is a schema invariant**: every IR entity must cite a fragment, an assumption, or a derivation, or
   it cannot serialise (`V-TRACE-001`, blocking).

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **LLM adjudicates conflicts case by case** | Non-deterministic, unexplainable, and unrepeatable — it would fail SF-ACC-05 and could not answer "why did 0.80 win?" the same way twice. The ranking rule is explicit knowledge and belongs in code. |
| **Latest document always wins** | Fails immediately: the L1 commissioning procedure (Rev C, April) is later than CR-004 (March) and is explicitly *not* design authority. The register says so. |
| **Highest-tier document always wins, ignore email** | Loses CR-004, CR-IAQ-007, CR-MAG-004/006 and CR-017 — every approved change in every case is transmitted by email. This is the single most common way to get all four cases wrong. |
| **Provenance as a prompt instruction** | A model can ignore an instruction. It cannot ignore a schema that will not serialise. Making it structural is what turns "no fabrication" from a claim into a property. |

## Consequences

- The answer to "how do you know it didn't make that up?" is one sentence: **it cannot serialise if it did.**
- Conflict reporting is mandatory even when resolution is obvious, because a silently-correct answer is
  indistinguishable from a silently-wrong one to the user.
- The rule set generalises to any engineering organisation, which is what the PRD rewards over case-specific
  handling.
