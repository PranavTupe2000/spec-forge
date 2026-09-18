# SpecForge

**From messy engineering documents to a SysML v2 model and Modelica that compiles — with every element traced
back to the document that justified it.**

AI-in-Engineering Hackathon · Track: System Modelling · 16–23 September 2026

---

## The problem

A systems engineer receives a folder: a requirements PDF, an engineering register spreadsheet, a scanned P&ID,
a design-review markdown, an email thread, and a legacy Modelica file from a colleague who has left. The
documents are incomplete, use three different names for the same valve, and contradict each other — the
requirement says the tank high limit is 0.78 m, an approved change record says 0.80 m, and the legacy model
still says 0.78 m.

Turning that pile into a structured system model is slow, manual, and depends entirely on the modeller's own
conventions.

## What SpecForge does

```
documents → evidence with authority → one validated IR → SysML v2 + Modelica → omc compiles
```

The interesting problem is not emitting Modelica syntax. It is **deciding which source wins, and being able to
say why.** SpecForge ranks every document by authority, resolves contradictions with a stated rule, retains
every losing position, and refuses to emit any element that cannot cite the fragment or assumption it came from.

| | |
|---|---|
| **Single source of truth** | One validated IR. SysML and Modelica are deterministic projections of it, so they cannot silently diverge. |
| **The LLM never writes syntax** | It extracts judgment into a typed schema. All emission is templated. |
| **Provenance is structural** | An element without a citation cannot serialise. "No fabrication" is a property of the build, not a prompt instruction. |
| **Honest about gaps** | Contradictions are flagged with all positions. Assumptions are declared. Unanswerable questions are asked, not guessed. |

## Quickstart

Full setup, including the OpenModelica smoke test, is in [`docs/devenv.md`](docs/devenv.md).

```bash
git clone <repo-url> && cd spec-forge
uv sync
cp .env.example .env          # add ANTHROPIC_API_KEY
docker compose up -d postgres
uv run spec-forge db upgrade

uv run spec-forge doctor      # verify omc, SysML toolchain, Postgres, key
```

Run a benchmark case end to end:

```bash
uv run spec-forge run test/testdata/benchmarks/L1_two_tank
```

## Compiling the generated Modelica

The generated model and the command to compile it are written to the run directory. **This is the command:**

```bash
omc build/omc/check_TwoTankController.mos
```

`checkModel` must report no errors. Each run also writes `runs/<run_id>/COMPILE.md` containing the exact
command for that run's model.

## What a run produces

```
runs/<run_id>/
  model.sfir.json     the IR — the single source of truth
  model.sysml         SysML v2 textual
  Model.mo            Modelica
  COMPILE.md          the compile command
  summary.md          one-minute human summary: coverage, conflicts, assumptions, gaps
  traceability.md     every element → the document fragment that justified it
  evidence.json       the full evidence ledger
  simulation/         results, plots, deviation vs the reference trace
```

## Benchmark cases

Four supplied problems forming a difficulty ladder. Each is a bundle of 12–15 mixed, contradictory documents.

| | Case | Reasoning under test |
|---|---|---|
| **L1** | Two-Tank Controller | Sequencing, interlocks, state machines |
| **L2** | Room CO2 Ventilation | Closed-loop feedback |
| **L3** | Magnetic Circuit | Multiphysics with an explicit loss path |
| **L4** | NaCl Evaporation Plant | Integration under competing constraints |

```bash
uv run spec-forge bench                  # all four
uv run spec-forge bench --repeat 2       # repeatability check
```

Nothing in `src/` branches on a case name — the pipeline is the same for all four, and
`test_no_case_specific_logic.py` enforces it.

## Documentation

| | |
|---|---|
| [`docs/specifications/specindex.md`](docs/specifications/specindex.md) | All specifications, with a reading order |
| [`docs/specifications/00_product_brief.md`](docs/specifications/00_product_brief.md) | Hackathon constraints and scoring |
| [`docs/specifications/03_system_ir_spec.md`](docs/specifications/03_system_ir_spec.md) | The IR — read this before any other subsystem |
| [`docs/specifications/05_evidence_precedence_spec.md`](docs/specifications/05_evidence_precedence_spec.md) | Authority tiers and conflict resolution |
| [`docs/design/ARCHITECTURE.md`](docs/design/ARCHITECTURE.md) | Layers, module boundaries, the eight rules |
| [`docs/design/ADR.md`](docs/design/ADR.md) | Architecture decisions, each with its rejected alternatives |
| [`docs/implementation_plan.md`](docs/implementation_plan.md) | Phase plan and risk register |
| [`DECISIONS.md`](DECISIONS.md) | Daily decision log |
| [`AI-LOG.md`](AI-LOG.md) | Where the AI was wrong, and what we did instead |

## Stack

Python 3.11 · LangGraph · Claude (Anthropic API) · Pydantic v2 · FastAPI · PostgreSQL · React + ShadCN +
React Three Fiber · OpenModelica + MSL · SysML v2 pilot toolchain · uv · PyTest
