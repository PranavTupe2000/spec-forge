# Implementation Plan

This document describes the phase wise implementation plan of the SpecForge Toolkit application.

## Phase Implementation sequence
- Do not start next phase till the previous phase is fully implemented and user explicitly asks for
  implementation of next phase.
- Strictly follow the implementation sequence below
    1. Phase 0 — Toolchain and skeleton
    2. Phase 1 — Vertical slice to a compiling model
    3. Phase 2 — Full ingestion, evidence and validation
    4. Phase 3 — Repair, simulation and consistency
    5. Phase 4 — SaaS surface
    6. Phase 5 — Hardening and submission

## Context and budget

**Hard stop: Wed 23 Sep 2026, 23:59.** Four people, 12–15 focused hours each — roughly 50–60 team-hours.

**The cut line: Phases 0–3 are the committed deliverable.** They satisfy every minimum-scope requirement
(SF-MIN-01…06) and the compile gate. Phases 4–5 are delivered if time allows. If a phase must be dropped, it is
dropped from the end — never from the middle, and never at the cost of the compile gate.

**Every day, regardless of phase:** commit `DECISIONS.md`. Add to `AI-LOG.md` when an override happens, not
retrospectively.

---

## Phase 0 — Toolchain and skeleton

> *"Set up your toolchain on day one — not day four. Tool friction, not modelling, is what sinks teams."*

**Goal:** prove the tools work before writing anything that depends on them.

**Specifications:** `docs/devenv.md` · `docs/design/ARCHITECTURE.md` · `15_nonfunctional_spec.md`

1. `uv` project, `pyproject.toml`, `ruff`, `mypy`, `pytest`, layer-dependency test.
2. Package skeleton per `docs/design/packagedesign.md` §2 — directories, `__init__.py`, Purpose comments.
3. **`omc` wrapper + liveness check.** Compile a hand-written two-line Modelica model end to end.
4. **SysML v2 toolchain wrapper.** Parse a hand-written `part def` end to end.
5. Postgres via Docker Compose; Alembic initialised; empty migration applied.
6. `spec-forge doctor` — reports Python, `uv`, `omc`, SysML toolchain, Postgres, API key presence.
7. CI: lint, type-check, test, **and `spec-forge doctor`**.
8. `DECISIONS.md` and `AI-LOG.md` created and committed.

**Exit criteria**

- [ ] `spec-forge doctor` green on every team member's machine
- [ ] A trivial `.mo` compiles via our wrapper, not by hand
- [ ] A trivial `.sysml` parses via our wrapper
- [ ] CI green
- [ ] `DECISIONS.md` committed today

---

## Phase 1 — Vertical slice to a compiling model

**Goal:** one benchmark case travels the whole path and produces Modelica that compiles. Narrow and complete,
not broad and partial.

**Specifications:** `03_system_ir_spec.md` · `04_ingestion_spec.md` (§4.1, §4.3, §4.5, §4.6) ·
`06_component_library_spec.md` · `07_sysml_emission_spec.md` · `08_modelica_emission_spec.md` ·
`13_data_model_spec.md` · `16_pipeline_orchestration_spec.md` · `benchmarks/L1_two_tank.md`

1. **`core/`** — full IR Pydantic models, JSON Schema export, pint unit registry, deterministic ids.
2. **`ingest/`** — PDF (text path), xlsx, md, txt, PlantUML, legacy Modelica. Fragments with locators.
3. **`library/`** — `fluid` and `control` archetypes needed by L1, with both bindings; deterministic retrieval.
4. **`extract/`** — structural, topology, attributes, behaviour passes, schema-constrained.
5. **`validate/`** — schema gate and the `V-TRACE`, `V-UNIT`, `V-TOPO` families.
6. **`emit/sysml`** and **`emit/modelica`** — templates, element maps.
7. **`toolchain/omc`** — the compile gate, `COMPILE.md`.
8. **`persistence/`** — schema and repositories per ADR-008.
9. **`pipeline/`** — LangGraph graph, events, checkpoints, recording.
10. **`cli/`** — `run`, `doctor`, `bench`.

**Exit criteria**

- [ ] `spec-forge run test/testdata/benchmarks/L1_two_tank` produces IR, SysML and Modelica
- [ ] **`omc checkModel` passes on the generated L1 model** ← the gate
- [ ] `COMPILE.md` exists and its command runs green
- [ ] SysML parses in the SysML v2 toolchain
- [ ] `V-TRACE-001` blocking and enforced — no element without provenance
- [ ] L1 effective parameters correct: **0.80 m, 12 s, 8 s**
- [ ] Runs end to end in under 10 minutes (SF-SPD-02)

---

## Phase 2 — Full ingestion, evidence and validation

**Goal:** all modalities, the full precedence engine, and all four cases reaching the compile gate.

**Specifications:** `04_ingestion_spec.md` (all) · `05_evidence_precedence_spec.md` ·
`09_validation_and_repair_spec.md` (§2, §3) · `17_benchmark_cases_spec.md` · `benchmarks/L2`–`L4`

1. Remaining loaders: docx, csv, eml (**per-message splitting**), json, png.
2. **Vision path** — images and image-only PDF pages, with `unreadable_regions` mandatory.
3. Alias resolution, seeded from explicit alias columns.
4. **`evidence/`** in full — tiers, transmission rule, `PRE-01`, conflicts, assumptions catalogue, open
   questions, ledger.
5. Remaining extraction passes: requirements, constraints, record detection.
6. Full rule catalogue: `V-BEH`, `V-PHYS`, `V-LIB`, `V-VIS`.
7. Archetypes for `air`, `magnetic`, `electrical`, `thermal`, `sensor`.
8. Confidence scoring per element (SF-EXT-07); binding reuse (SF-EXT-08).
9. Expected fixtures for all four cases.

**Exit criteria**

- [ ] All 56 benchmark files ingest without error
- [ ] Every conflict in `05_evidence_precedence_spec.md` §6.1 detected, with losing positions retained
- [ ] Every listed **non-conflict** correctly *not* reported
- [ ] All four cases compile
- [ ] `test_no_case_specific_logic.py` passes
- [ ] All four cases pass with `--no-manifest`

---

## Phase 3 — Repair, simulation and consistency

**Goal:** the pipeline recovers from its own failures, produces trajectories, and proves its two outputs agree.

**Specifications:** `09_validation_and_repair_spec.md` (§4–§7) · `10_traceability_and_reporting_spec.md` ·
`08_modelica_emission_spec.md` §7

1. **`repair/`** — diagnostic parsing, localisation, the eight known actions, bounded loop, IR patching.
2. Degradation ladder end to end (ADR-007), including the `degraded` terminal state.
3. Simulation via `omc`, results CSV, plots.
4. **Reference-trace comparison** with per-signal deviation tables.
5. **Round-trip consistency checker**.
6. `emit/report` — `summary.md`, `traceability.md`, `evidence.json`.
7. `--replay` verified with networking disabled.
8. Repeatability harness: `spec-forge bench --repeat 2`.

**Exit criteria**

- [ ] A deliberately broken IR is repaired and compiles
- [ ] Repair never exceeds 3 attempts; every attempt logged
- [ ] A forced failure at each stage still produces partial output plus a gap report
- [ ] L1 and L2 simulate and match their reference traces within tolerance
- [ ] Consistency checker catches a deliberately desynchronised emitter pair
- [ ] `summary.md` passes the one-minute test with a human reader
- [ ] `--replay` runs with no network
- [ ] `bench --repeat 2` structurally equivalent

**← This is the cut line. Everything above is the committed deliverable.**

---

## Phase 4 — SaaS surface

**Goal:** the product an engineer would actually use.

**Specifications:** `11_web_application_spec.md` · `12_api_spec.md`

1. FastAPI app, routes, OpenAPI, **SSE with the 2-second heartbeat contract**.
2. React + Vite + ShadCN scaffold; generated TypeScript types.
3. Run overview with the compile gate and coverage card.
4. **Evidence view** — document ranking, claim inspector, conflict cards, fragment viewer.
5. Model explorer — tree, graph, R3F 3D placement view.
6. **Clarifying dialogue** (SF-EXT-02).
7. **Round-trip editing** (SF-EXT-06) with tier-0 overrides.
8. Playwright smoke test.

**Exit criteria**

- [ ] Upload L1 bundle → run → green gate → download, entirely in the browser
- [ ] No gap over 2 s between progress events
- [ ] `test_cli_without_frontend.py` still passes
- [ ] Answering a question changes the model and persists to the next run

---

## Phase 5 — Hardening and submission

**Goal:** survive the 45 minutes.

**Specifications:** `14_acceptance_criteria_and_evaluation.md` · `00_product_brief.md` §4–5

1. Full benchmark suite green; performance measured against SF-SPD-01/02.
2. **Judge-supplied-spec path** — paste prose in the UI, `spec-forge run --text` in the CLI. Rehearsed.
3. Demo fallback ladder rehearsed: live → `--replay` with network off → pre-generated artifacts.
4. `README.md` verified on a clean clone.
5. **8 slides** in `docs/submission/`.
6. `AI-LOG.md` finalised — at least two cases where the model was confidently wrong.
7. `DECISIONS.md` reviewed: every entry names its rejected alternative and is defensible by any member.
8. **Individual-probe rehearsal** — each member walks a subsystem they did not build.
9. Pre-demo checklist (`14_…` §8) executed.

**Exit criteria**

- [ ] `spec-forge bench` green on all four cases
- [ ] Clean clone → compiling model, following `README.md` only
- [ ] Each of the four can explain a subsystem they did not build
- [ ] Judge-supplied-spec path rehearsed under time
- [ ] All four submission artifacts complete

---

## Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Toolchain friction | Fatal — the gate is binary | Phase 0 before anything else; `doctor` in CI |
| Four cases at equal effort leaves all four shallow | Outcome score | Cut line at Phase 3; L1 complete before L2 starts within a phase |
| SaaS consumes the week | Everything | Phase 4 is after the cut line and strictly a client (ADR-009) |
| Only one member can explain the design | **Method capped at 27/45** | Sequential phases; rotation; specs written to be read by non-authors |
| `DECISIONS.md` gaps | **Method scores zero — not partial credit** | CI check from day one |
| Venue network fails during the demo | Demo | `--replay`, tested with networking disabled |
| L4 WaterNaCl convergence | L4 completeness | Planned: StandardWater baseline, gap stated honestly (ADR-011) |
