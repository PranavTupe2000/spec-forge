# ADR-002 — Claude via the Anthropic API, with model tiering

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `extract`, `ingest`, `pipeline`, `repair`

## Context

The pipeline needs an LLM for extraction, alias resolution, record detection, vision over diagrams, and repair
diagnosis. The briefing states that using AI is expected and that what is scored is judgment in using it.

## Decision

**Claude via the Anthropic API**, single provider, with tiering by task difficulty:

| Task | Model |
|---|---|
| Structural, topology, behaviour, constraints extraction; vision; repair diagnosis | **Opus 5** |
| Requirements extraction, record detection, high-volume structured passes | **Sonnet 5** |

All calls use structured output against a Pydantic schema, `temperature=0`, and versioned prompt files. Model
ids are configuration and are recorded per run.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Multi-provider abstraction layer** | Real cost, no benefit within the hackathon. Every provider's structured-output and vision APIs differ enough that the abstraction leaks, and it adds a failure surface to the demo path. |
| **Local model fallback (Ollama)** | Attractive for demo resilience, but a local model that cannot do schema-constrained extraction well produces worse output than no output. Demo resilience is solved properly by record/replay (ADR-013) instead. |
| **Single model for everything** | Opus for high-volume requirement extraction is wasteful; Sonnet for behaviour extraction measurably degrades the hardest pass. Tiering is a judgment we can defend with per-pass cost and quality data. |

## Consequences

- One SDK, one auth path, one set of retry semantics.
- Vision is native, which matters because every benchmark bundle contains a reference diagram PNG and the
  hackathon's own briefing PDF has no text layer.
- Per-run token and cost accounting gives the AI-collaboration segment actual data rather than recollection.
- Switching providers later means implementing one client interface, not unpicking an abstraction.
