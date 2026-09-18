# DECISIONS

Daily decision log. **One commit every day from the start date through 23 September, weekend included.**

**Format:** `D<n> | what we decided | why the alternative lost`

## Rules

- Two minutes a day. Three lines. Do not write an essay.
- **Log what you killed.** Discarded options are the entries judges pick to question.
- **Timestamps are the evidence.** Retro-added entries show in the git log and carry no weight.
- A missed day is a missed day. There is no making it up.
- At the evaluation, judges pick **three entries — their choice** — and ask what the alternative was and why it
  lost. Every entry must be defensible by **any** team member, not only its author.

---

## Log

<!--
Append below. Newest at the bottom. Example of the expected shape:

D1 | Scoped to the four supplied benchmark cases, no self-proposed problem
   | Self-proposed needed a reachable in-house stakeholder we did not have inside the week

D2 | Extraction into a typed schema + deterministic emitters, not end-to-end LLM generation
   | End-to-end generation makes SysML and Modelica diverge silently; the PRD names this as the common failure

D3 | Dropped rule-based SysML emitter for LLM generation
   | Emitter failed on 4/10 sample specs
-->

D1 | workingrules.md's docs/-edit lock does not apply to `docs/design/sourcemap.md` and `docs/design/packagedesign.md` — both are updated automatically as a routine part of adding a source file or package, no per-edit approval
   | A blanket "ask every time" gate loses because ARCHITECTURE.md requires these two files to be updated on every single new source file; that would mean a permission round-trip per file for the whole build

D2 | `spec-forge doctor` (P0.2) checks only that `ANTHROPIC_API_KEY` is set, not that the Anthropic API actually responds
   | A live liveness ping lost on cost and latency for a check run on every invocation; a bad key surfaces immediately on the first real extraction call regardless, so the ping buys nothing a presence check doesn't already cover — deliberate, not an oversight, despite ADR-002 pinning Claude as sole provider with no fallback

D3 | PRD §8's "how is agentic behaviour used" row corrected to say repair + clarification are the two agentic nodes, not extraction + conflict adjudication + repair
   | The original wording lost because it contradicted its own cited source: ADR-004 defines "agentic" strictly as a looping node and enforces exactly two (repair, clarification) via `test_agent_count.py`; extraction and conflict adjudication are single schema-constrained LLM calls, not agents

D4 | Start date for the daily decision-log rule is today, 2026-09-17 — matches the repo's actual first commit (d279f84), so no backfill is needed
   | Anchoring to "PRD date" or "kickoff meeting" lost because neither is written down anywhere as an actual date; the first commit is the only unambiguous timestamp that exists
