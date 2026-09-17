# ADR-013 — Record and replay every LLM interaction

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `pipeline`, `ingest`, `test/`

## Context

Three problems share one solution: LLM-dependent tests are slow, expensive and non-deterministic; development
iteration re-pays for extraction on every run; and the live demo depends on a venue network, where the briefing
warns that *a compiler that will not start is a compile failure* and setup comes out of the demo slot.

## Decision

Every LLM request/response pair is written to `runs/<run_id>/llm/<pass>/<seq>.json` with model id, prompt
version, token counts and latency. Ingestion is cached content-addressed by file hash plus loader version.

`--replay <run_id>` re-runs a case entirely from cache with **zero network calls**, and is exercised in CI with
networking disabled so it cannot rot.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Mock the LLM in tests** | Mocks encode what we *think* the model returns. Recorded real responses encode what it *did*, including the malformed ones worth keeping as regression fixtures. |
| **Live calls in CI** | Slow, costly, flaky, and requires a key in CI. A test suite that needs a network is a test suite that stops being run. |
| **Local model fallback for the demo** | Considered and rejected in ADR-002 — a weaker model producing worse output is not a fallback, it is a different product. Replay gives a guaranteed-identical result instead. |

## Consequences

- The demo fallback ladder is: live run → `--replay` of a rehearsed case with the network down → pre-generated
  artifacts from disk. Which rung we are on is stated out loud, not concealed.
- Recorded transcripts are the primary evidence for the AI-collaboration segment — the actual prompts, the
  actual wrong answers, and what we did about them.
- Storage cost is trivial; the run directory is already the unit of reproducibility.
