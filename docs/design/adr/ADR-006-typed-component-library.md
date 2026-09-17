# ADR-006 — Domain knowledge as a versioned typed archetype library

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `library`, `extract`, `emit`, `validate`

## Context

The PRD asks how domain knowledge is injected, offering four options: prompting, retrieval over a component
library, fine-tuning, or a typed schema that constrains what can be generated.

## Decision

Use **two of the four, together**: a versioned typed **archetype library**, retrieved at extraction time, binding
into a **schema-constrained IR**.

Each archetype declares its ports, attributes, standard assumptions, **and both its SysML `part def` and its
Modelica component binding with parameter and port maps**. Retrieval supplies the extraction agent with a
**closed set** of candidates; the agent selects or returns `unbound` with a reason, and may not invent a key.
An unbound archetype is a hard validation error.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Prompt-only domain knowledge** | Invisible, unversioned, untestable, and different on every call. Worst of all, it cannot guarantee the SysML and Modelica views of one part agree — which reopens ADR-001's failure mode. |
| **Fine-tuning** | No training data, no time, and unfalsifiable at judging. |
| **Full MSL wrapper** | Enormous surface for no benefit. We need the archetypes the four reasoning patterns require, not all of Modelica. |
| **Let the LLM name MSL components freely** | It will emit `Modelica.Fluid.Vessels.MagicTank` and it will look plausible. Closed-set selection makes that unrepresentable. |

## Consequences

- `test_modelica_bindings.py` verifies **every** binding resolves in the installed MSL via `omc`, catching
  invented components in CI rather than at generation time. We expect this test to produce `AI-LOG.md` entries.
- A single archetype is the reason a part's two projections cannot disagree.
- Extending to a new domain means adding YAML, not adding a branch — which is how SF-SCP-01 stays true.
- MSL hazards (`inner System`, `nPorts` arity, grounds) are encoded once instead of rediscovered per case.
