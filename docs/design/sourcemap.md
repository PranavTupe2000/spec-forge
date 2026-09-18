# Index of source code for SpecForge Toolkit

## Index format is
- `<relative filepath from src>` : purpose of the source file.

## How to use this file
- Use this file to determine which source code file to load based "purpose" of the source code file
- Do not load all source code documents every time.
- Update the index whenever you add a new source code file.

---

## Status

**Phase 0 is complete** (all 8 items, all 5 exit criteria verified — see `docs/implementation_plan.md`
and `DECISIONS.md` D1-D16). What exists: the `uv` project and full package skeleton; the `omc` and
SysML v2 (conda-forge `jupyter-sysml-kernel`) toolchain wrappers, both proven end to end against the
real toolchain, not mocked; `doctor` and the `spec-forge` CLI (`doctor`, `db upgrade`); the eight-test
architecture suite (`test/unit/architecture/`); Postgres via Docker Compose, Alembic with an empty
baseline migration; GitHub Actions CI (green on a real run, both jobs) plus the daily-decisions gate.
**Phase 1 has not been started** — everything else in the planned table below is still unwritten, and
per `.agents/workingrules.md` it stays that way until explicitly asked for.

The table below is the **planned** allocation — where each responsibility belongs when it is written. Use it to
decide where a new file goes. **When you create a file, move its row into the Sourcemap Index below and give it
the real purpose from its Purpose comment.**

## Planned module allocation

| Path | Responsibility | Phase | Spec |
|---|---|---|---|
| `main.py` | Application entry point | 0 | ARCHITECTURE |
| `spec_forge/core/ir/` | Pydantic IR models — part, port, connection, attribute, state machine, constraint, requirement, provenance, assumption, conflict, open question, trace, document | 1 | `03` |
| `spec_forge/core/units.py` | pint registry and dimensional helpers | 1 | `03` |
| `spec_forge/core/ids.py` | Deterministic id generation | 1 | `03` §3 |
| `spec_forge/core/schema.py` | JSON Schema export for frontend and CI | 1 | `03` |
| `spec_forge/ingest/dispatch.py` | Content sniff → loader selection | 1 | `04` §3 |
| `spec_forge/ingest/loaders/` | One module per file type | 1–2 | `04` §4 |
| `spec_forge/ingest/vision.py` | Claude vision with structured output | 2 | `04` §4.9 |
| `spec_forge/ingest/aliases.py` | Alias harvesting and resolution | 2 | `04` §7 |
| `spec_forge/ingest/cache.py` | Content-addressed ingest cache | 1 | `04` §6 |
| `spec_forge/ingest/manifest.py` | Case manifest loading (test fixtures only) | 1 | `04` §8 |
| `spec_forge/evidence/tiers.py` | The 12-tier authority model | 2 | `05` §2 |
| `spec_forge/evidence/transmission.py` | Authority-of-record detection | 2 | `05` §3 |
| `spec_forge/evidence/precedence.py` | `PRE-01` resolution algorithm | 2 | `05` §4 |
| `spec_forge/evidence/conflicts.py` | Conflict construction and severity | 2 | `05` §6 |
| `spec_forge/evidence/assumptions.py` | Assumption creation, catalogue enforcement | 2 | `05` §7 |
| `spec_forge/evidence/standard_assumptions.yaml` | The catalogue — **data, not code** | 2 | `05` §7.2 |
| `spec_forge/evidence/questions.py` | Open question generation | 2 | `05` §8 |
| `spec_forge/evidence/ledger.py` | The evidence ledger | 2 | `05` §5 |
| `spec_forge/library/archetypes/*.yaml` | Typed archetypes — **data, not code** | 1–2 | `06` §3 |
| `spec_forge/library/retrieval.py` | Deterministic → lexical → semantic retrieval | 1 | `06` §5 |
| `spec_forge/library/bindings.py` | Cross-run binding reuse | 2 | `06` §7 |
| `spec_forge/extract/passes/` | Seven schema-constrained extraction passes | 1–2 | `16` §4 |
| `spec_forge/extract/merge.py` | IR assembly and merge order | 1 | `16` §4 |
| `spec_forge/extract/client.py` | Anthropic client wrapper with recording | 1 | `16` §8 |
| `spec_forge/validate/rules/` | One module per rule family | 1–2 | `09` §2 |
| `spec_forge/validate/ladder.py` | The four validation gates | 1 | `09` §1 |
| `spec_forge/validate/consistency.py` | SysML ↔ Modelica round-trip check | 3 | `09` §6 |
| `spec_forge/validate/reference.py` | Reference-trace comparison | 3 | `09` §7 |
| `spec_forge/emit/sysml/` | SysML v2 emitter and templates | 1 | `07` |
| `spec_forge/emit/modelica/` | Modelica emitter, templates, state-machine strategies | 1 | `08` |
| `spec_forge/emit/report/` | `summary.md`, `traceability.md`, plots | 3 | `10` |
| `spec_forge/repair/` | Diagnosis, localisation, actions, bounded loop | 3 | `09` §5 |
| `spec_forge/pipeline/graph.py` | LangGraph graph definition | 1 | `16` §2 |
| `spec_forge/pipeline/state.py` | Pipeline state | 1 | `16` §3 |
| `spec_forge/pipeline/events.py` | Progress event bus with heartbeat | 1 | `16` §9 |
| `spec_forge/pipeline/replay.py` | Record and replay | 1 | `16` §8 |
| `spec_forge/pipeline/prompts/` | Versioned prompt files — **data, not code** | 1 | `16` §7 |
| `spec_forge/persistence/models.py` / `repositories.py` / `session.py` | SQLAlchemy models and repositories (the real schema) | 1 | `13` |
| `spec_forge/api/` | FastAPI app, routes, SSE | 4 | `12` |
| `spec_forge/cli/main.py` | remaining commands — `run`, `ingest`, `bench`, … | 1 | `12` §8 |

## Sourcemap Index

| Path | Purpose |
|---|---|
| `spec_forge/__init__.py` | Root package for the `spec-forge` distribution (ADR-014); no logic |
| `spec_forge/core/__init__.py` | L0 package marker — IR models, units, ids, errors; no internal deps |
| `spec_forge/core/ir/__init__.py` | Groups the IR Pydantic model modules under one `core.ir` surface |
| `spec_forge/ingest/__init__.py` | L1 package marker — loaders, vision, aliases, cache |
| `spec_forge/ingest/loaders/__init__.py` | Groups one loader module per input file type |
| `spec_forge/evidence/__init__.py` | L1 package marker — tiers, transmission, precedence, conflicts, ledger |
| `spec_forge/library/__init__.py` | L1 package marker — archetype retrieval and bindings |
| `spec_forge/persistence/__init__.py` | L1 package marker — SQLAlchemy models, repositories, migrations |
| `spec_forge/extract/__init__.py` | L2 package marker — schema-constrained extraction passes, IR merge |
| `spec_forge/extract/passes/__init__.py` | Groups the seven schema-constrained extraction passes |
| `spec_forge/validate/__init__.py` | L2 package marker — rule catalogue, four-gate ladder, consistency check |
| `spec_forge/validate/rules/__init__.py` | Groups one rule module per rule family |
| `spec_forge/emit/__init__.py` | L3 package marker — deterministic emitters; no LLM calls (A3) |
| `spec_forge/emit/sysml/__init__.py` | SysML v2 emitter package (emitter.py + templates/) |
| `spec_forge/emit/modelica/__init__.py` | Modelica emitter package (emitter.py + templates/ + strategies/) |
| `spec_forge/emit/modelica/strategies/__init__.py` | Groups the state-machine emission strategy modules |
| `spec_forge/emit/report/__init__.py` | Groups summary/traceability/plot generation modules |
| `spec_forge/toolchain/__init__.py` | L3 package marker — omc and SysML v2 toolchain wrappers, doctor |
| `spec_forge/repair/__init__.py` | L4 package marker — bounded repair loop; patches the IR, not text (A5) |
| `spec_forge/pipeline/__init__.py` | L5 package marker — LangGraph graph, state, events, replay |
| `spec_forge/api/__init__.py` | L6 package marker — FastAPI app, a thin client of pipeline/ (ADR-009) |
| `spec_forge/api/routes/__init__.py` | Groups one route module per frontend resource |
| `spec_forge/cli/__init__.py` | L6 package marker — Typer CLI, a thin client of pipeline/ (A7) |
| `spec_forge/core/errors.py` | `SpecForgeError` — the shared base exception every module-specific error inherits |
| `spec_forge/toolchain/omc.py` | The compile gate: drives `omc`, parses its stdout into structured diagnostics. Never trusts the process exit code — confirmed empirically to be 0 even on total failure |
| `spec_forge/toolchain/sysml.py` | Wraps the SysML v2 toolchain via `SYSML_TOOL_CMD` (the installed conda-forge Jupyter kernel) — builds a probe notebook per model, parses its output; same exit-code caveat as omc |
| `spec_forge/toolchain/doctor.py` | Aggregates every environment probe (Python, uv, omc, MSL, SysML, Postgres, Anthropic key, runs/build writability) into one `DoctorReport` |
| `test/unit/architecture/test_layer_dependencies.py` | Enforces the L0-L6 layer rule (packagedesign.md §3) via AST import analysis |
| `test/unit/toolchain/test_omc.py` | omc wrapper tests — parser unit tests against real captured `omc` stdout, plus a real end-to-end compile of a hand-written model |
| `test/unit/toolchain/test_sysml.py` | SysML wrapper tests — parser unit tests against real captured kernel output, plus a real end-to-end parse of a hand-written model |
| `test/unit/toolchain/test_doctor.py` | `doctor`'s check-aggregation and severity logic, with the toolchain checks monkeypatched |
| `test/unit/cli/test_doctor_command.py` | The `spec-forge doctor` Typer command's exit code matches its `DoctorReport`'s |
| `test/unit/architecture/_import_utils.py` | Shared AST import-resolution (relative imports resolved to full dotted paths) for the architecture test suite |
| `test/unit/architecture/test_emitter_inputs.py` | A1 — no `ingest`/`extract`/`pipeline` import anywhere under `emit/` |
| `test/unit/architecture/test_no_llm_in_emit.py` | A3 — no `anthropic` import anywhere under `emit/` or `validate/` |
| `test/unit/architecture/test_no_case_specific_logic.py` | A4/SF-SCP-01 — greps `src/` for benchmark tags (from `test/testdata/expected/*/elements.yaml`), case ids and bundle filenames, all read from disk at test time |
| `test/unit/architecture/test_repair_patches_ir.py` | A5, `xfail` — repair action modules don't exist yet (Phase 3) |
| `test/unit/architecture/test_cli_without_frontend.py` | A7, `xfail` — `spec-forge run` and `pipeline/` don't exist yet (Phase 1) |
| `test/unit/architecture/test_no_db_mode.py` | A7, `xfail` — `spec-forge run --no-db` doesn't exist yet (Phase 1) |
| `test/unit/architecture/test_agent_count.py` | ADR-004/D3, `xfail` — `pipeline/graph.py` doesn't exist yet (Phase 1) |
| `spec_forge/persistence/migrations/env.py` | Alembic migration environment — reads `DATABASE_URL` from the environment, fails loudly if unset |
| `spec_forge/persistence/migrations/script.py.mako` | Alembic's revision template — unmodified generated boilerplate, used by `alembic revision` |
| `spec_forge/persistence/migrations/README` | Alembic's own generated readme (generic-single-database note) |
| `spec_forge/persistence/migrations/versions/92dd1b8012fb_baseline.py` | The empty baseline migration — establishes the revision chain; the real schema starts in Phase 1 |
| `spec_forge/persistence/migrations_runner.py` | `run_upgrade()` — wraps `alembic upgrade`; `MigrationError` is a hard stop, unlike a toolchain liveness check |
| `spec_forge/cli/main.py` | Typer CLI entry point (`spec-forge` script) — `doctor` and `db upgrade` (`db_app` sub-command group) |
| `test/unit/persistence/test_migrations_runner.py` | Mocked-Alembic failure-wrapping tests, plus a real `alembic upgrade head` against the docker-compose `postgres:16` container |
| `test/unit/cli/test_db_upgrade_command.py` | `spec-forge db upgrade`'s exit code matches `migrations_runner`'s result/error |
| `scripts/check_decisions_daily.py` | Fails if `DECISIONS.md` has no commit for some day between the repo's start date and today (14_acceptance_criteria_and_evaluation.md §6) |
| `test/unit/test_check_decisions_daily.py` | Pure `compute_missing_days` tests, plus a real run against this repo's actual git history |
| `.github/workflows/ci.yml` | `test` job (ruff/mypy/pytest/`db upgrade`/`doctor`, real `omc` + SysML kernel + postgres provisioned) and `decisions` job (the daily-commit gate, `TZ` pinned to IST). Verified green on a real run after fixing two bugs the first run caught — MSL not bundled by `apt install omc`, and a `$CONDA_PREFIX` path error (AI-LOG A1, DECISIONS.md D16) |

## Project configuration

Not "source code" in the navigable sense above, but created this phase and worth indexing.

| Path | Purpose |
|---|---|
| `pyproject.toml` | Project metadata, dependencies, `ruff`/`mypy`/`pytest` config, the `spec-forge` script entry point |
| `.python-version` | Pins `uv`'s resolved Python to 3.11 (NFR-PORT-02) |
| `docker-compose.yml` | `postgres:16` service — db/user/password `specforge`, port 5432, healthcheck |
| `.env.example` | Template for `.env` — `ANTHROPIC_API_KEY`, `DATABASE_URL`, `OPENMODELICA_HOME`, `SYSML_TOOL_CMD` |
| `alembic.ini` | Points Alembic at `src/spec_forge/persistence/migrations` |
