# ADR-004 — LangGraph orchestration with exactly two agents

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `pipeline`, `repair`

## Context

The PRD asks how agentic behaviour is used, and warns:

> Using an agent where a single call would do is not automatically better.

We expect to defend every agent in the individual probes.

## Decision

LangGraph state machine with checkpointing. **Exactly two nodes are agentic** — that is, loop over unpredictable
external feedback:

1. **Repair** — loops against compiler and validator output, bounded at 3 attempts.
2. **Clarification** — loops against user answers.

Everything else is either a **single schema-constrained LLM call** (alias resolution, record detection, each
extraction pass) or **plain deterministic code** (ingestion, precedence, validation, emission).

The test we apply: *an LLM call is warranted where the task requires judgment over ambiguous natural language;
an agent is warranted only where it additionally requires iteration against feedback that cannot be predicted
in advance.*

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Multi-agent crew** (planner, researcher, modeller, critic) | Impressive-sounding, harder to debug, non-deterministic, and most of the roles have no unpredictable feedback to iterate against. Would fail the PRD's own warning. |
| **Single monolithic agent with tools** | One long trajectory is impossible to test per-stage, impossible to cache, and impossible to explain in an individual probe. |
| **No framework, hand-rolled orchestration** | We would reimplement checkpointing, state typing and resumability. LangGraph is already in the stated stack. |
| **One large "extract everything" prompt** | Lower quality, undebuggable, and cannot be improved one concern at a time. Rejected in favour of seven focused passes. |

## Consequences

- Per-stage caching and checkpointing make development iteration cheap and `--replay` straightforward.
- `test_agent_count.py` asserts exactly two looping nodes exist, which guards against agent creep under time
  pressure.
- "We use two agents, here is the test for why the rest are not agents" is a stronger answer than a large
  architecture diagram.
