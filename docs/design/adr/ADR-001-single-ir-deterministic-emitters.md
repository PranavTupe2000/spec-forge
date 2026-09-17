# ADR-001 — One IR, deterministic emitters

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `core`, `extract`, `emit`, `validate`

## Context

The PRD requires both a SysML v2 model and a compiling Modelica model of the same system, and warns:

> Generating SysML and Modelica independently is the most common way to get silent divergence between them.

It also asks, in the architecture considerations judges will probe:

> Where does the language model sit: end-to-end generation, or extraction into a schema followed by
> deterministic code generation? **The second is usually more reliable and easier to defend.**

## Decision

1. A single validated **System IR (SFIR)** is the sole source of truth.
2. SysML and Modelica are produced by **deterministic Jinja emitters** that read only a validated IR.
3. **No LLM call occurs in `emit/`.** The model contributes judgment into a typed schema; it never writes
   target syntax.
4. Both emitters produce an **element map**, and a round-trip consistency checker asserts the two outputs
   describe the same set of parts, ports, connections and parameters.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **End-to-end LLM generation** of SysML and Modelica | Two independent generations of the same system diverge. Unfixable class of bug, and the failure is silent — both artifacts look right in isolation. Also the exact failure the PRD names. |
| **Generate SysML, then transform SysML → Modelica** | Better than independent generation, but SysML v2 textual is lossy for what Modelica needs (transition priority, timer suspend semantics, solver hints). The transform would have to re-infer them, which is inference at emission time. |
| **Generate Modelica, then reverse-engineer SysML** | Makes the executable artifact primary and the structural artifact derived. Wrong for our stated user (ADR-010), and SysML would inherit Modelica's implementation artefacts as if they were architecture. |
| **LLM emits, then a validator checks** | Validation catches syntax, not semantics. A model that compiles and is physically wrong passes. Deterministic emission removes the failure mode instead of detecting it. |

## Consequences

- Emission bugs are **template bugs** — reproducible, debuggable, testable, and fixed once for all cases.
- Everything the output needs must exist in the IR first. This forces gaps to surface in extraction, where they
  can be reported honestly, rather than being quietly papered over in a template.
- Adding a target language means adding an emitter, not retraining a prompt.
- The answer to "how do you know they agree?" is a test, not an argument.
