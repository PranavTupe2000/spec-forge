# ADR-010 — The target user is the systems engineer

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** all output-facing modules

## Context

The PRD lists four users and requires us to state which one we chose:

> Teams may narrow to a single user and build depth rather than breadth. **State which user you chose.**

## Decision

**The systems engineer** — *"Convert a specification or sketch into a first-pass SysML model without starting
from a blank canvas."*

The governing asymmetry, from which most design trade-offs follow:

> **A wrong element that looks right costs the engineer more than a missing element that is flagged.**

Reviewing a stated gap takes seconds. Discovering a silently invented port three days later costs a design
review. Every trade-off resolves toward the flagged gap.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Design reviewer** | Closest fit to the honesty criterion, and genuinely tempting. But the reviewer consumes a model someone else generated — building for them makes traceability the product and generation a means, which understates what we are actually building. Their needs are served anyway, because provenance is mandatory. |
| **Simulation engineer** | Would make Modelica primary and SysML documentation. The PRD makes SysML v2 textual a must, so this inverts the stated priority. |
| **Domain newcomer** | Pushes effort into guardrails and guided dialogue rather than model quality, and the "under a minute to approve or reject" criterion assumes a reader who can judge a model. |

## Consequences

- SysML v2 is the primary artifact; Modelica is the executable proof that the structure is coherent.
- We retain the engineer's own vocabulary and tags rather than imposing a normalised ontology.
- We do not attempt autonomy. The engineer stays in the loop, and the product is explicit that a user who will
  not read the assumption list is using the wrong tool.
- Secondary personas are served as a by-product of the same architecture, not by added features.
