# 15 — Non-Functional Requirements

**Status:** Baseline

---

## 1. Determinism and repeatability

Directly serves SF-ACC-05 (*"the same input run twice yields a structurally equivalent model"*).

| ID | Requirement |
|---|---|
| **NFR-DET-01** | LLM calls use `temperature = 0` and a fixed `seed` where the API supports it |
| **NFR-DET-02** | Element ids are pure functions of canonical name and kind. No UUIDs, timestamps or hashes of mutable state in ids |
| **NFR-DET-03** | All IR collections are sorted by id before serialisation |
| **NFR-DET-04** | No iteration over unordered sets or dicts influences output order |
| **NFR-DET-05** | Prompt templates are versioned; the version is recorded in `run.config` |
| **NFR-DET-06** | Non-determinism that remains is **structural-equivalence tested**, not asserted away |

NFR-DET-06 is the honest position: an LLM will vary its wording between runs and we do not pretend otherwise.
What must not vary is topology. `spec-forge bench --repeat 2` compares structure after canonical renaming and
fails on any topology difference.

## 2. Performance

| ID | Requirement |
|---|---|
| NFR-PERF-01 | First structural draft < 2 min (SF-SPD-01) |
| NFR-PERF-02 | Full pipeline per case < 10 min (SF-SPD-02) |
| NFR-PERF-03 | Ingestion parallel across files, bounded worker pool |
| NFR-PERF-04 | Independent extraction passes run concurrently |
| NFR-PERF-05 | Ingestion and LLM responses cached content-addressed; a warm re-run avoids all network calls |
| NFR-PERF-06 | Large CSVs summarised, never loaded row-by-row into context (`04_ingestion_spec.md` §4.7) |
| NFR-PERF-07 | API first paint < 1.5 s; artifact downloads streamed |

## 3. Observability

| ID | Requirement |
|---|---|
| NFR-OBS-01 | Structured JSON logging with `run_id` on every record |
| NFR-OBS-02 | Every pipeline stage emits start/complete events with duration |
| NFR-OBS-03 | **No stage silent for more than 2 seconds** (SF-UX-03) |
| NFR-OBS-04 | Every LLM call records model id, prompt version, token counts, latency and cost |
| NFR-OBS-05 | `runs/<run_id>/events.jsonl` is a complete replayable record of the run |
| NFR-OBS-06 | Token and cost totals per run are reported in the summary |

NFR-OBS-04 and 06 exist so the AI-collaboration segment has data rather than recollection — delegation judgment
is easier to defend with the actual per-stage cost and token profile on screen.

## 4. Reliability and failure

| ID | Requirement |
|---|---|
| NFR-REL-01 | Every run produces output; a failed stage degrades with a stated gap (ADR-007) |
| NFR-REL-02 | Transient failures retry with exponential backoff, max 3 |
| NFR-REL-03 | Repair loops are bounded (max 3 attempts) and every attempt is recorded |
| NFR-REL-04 | The pipeline is runnable with `--no-db` and with no frontend |
| NFR-REL-05 | `--replay <run_id>` reproduces a run with **zero network calls** |
| NFR-REL-06 | Toolchain liveness (`omc`, SysML) is checked at startup, not at point of use |

NFR-REL-05 is a demo-slot requirement, not a convenience. The briefing warns that setup comes out of the demo
time and a compiler that will not start is a compile failure; a venue network failure must not be able to end
the demo. It is exercised in CI so it cannot rot.

## 5. Security and data handling

| ID | Requirement |
|---|---|
| NFR-SEC-01 | **No proprietary or confidential plant data** — supplied benchmark cases and shareable material only (PRD §5.3) |
| NFR-SEC-02 | API keys from environment only; never committed, never logged, never in run manifests |
| NFR-SEC-03 | Uploaded files stored outside the web root; served only through authorised endpoints |
| NFR-SEC-04 | Generated Modelica is compiled, never executed as arbitrary code; `omc` runs with a timeout |
| NFR-SEC-05 | Upload limits: 50 MB per file, 200 MB per project |
| NFR-SEC-06 | No secret or file content in LLM prompts beyond the ingested engineering documents |

NFR-SEC-04 is worth stating because the pipeline generates code and then invokes a compiler on it. `checkModel`
and `simulate` run in a subprocess with a wall-clock timeout and a bounded working directory.

## 6. Portability

| ID | Requirement |
|---|---|
| NFR-PORT-01 | Windows 11, macOS and Linux. **Development is on Windows** — paths via `pathlib`, no shell assumptions |
| NFR-PORT-02 | Python 3.11+, managed with `uv` |
| NFR-PORT-03 | `omc` located via `OPENMODELICA_HOME` or `PATH`; never a hardcoded path |
| NFR-PORT-04 | Postgres via Docker Compose; no host install required |
| NFR-PORT-05 | Node 20+ for the frontend |

NFR-PORT-01 matters for the demo: the evaluation runs on our laptop, which is Windows. Any code path that has
only ever run under WSL or a POSIX shell is a demo risk.

## 7. Maintainability

| ID | Requirement |
|---|---|
| NFR-MNT-01 | Module dependencies are acyclic and respect layer order (`docs/design/ARCHITECTURE.md`) |
| NFR-MNT-02 | Every source file opens with a Purpose comment (`.agents/workingrules.md`) |
| NFR-MNT-03 | Every new source file is registered in `docs/design/sourcemap.md` |
| NFR-MNT-04 | Public functions are type-annotated; `mypy --strict` on `core/` and `emit/` |
| NFR-MNT-05 | `ruff` lint and format, enforced in CI |
| NFR-MNT-06 | Domain knowledge lives in `library/` data, never in control flow (SF-SCP-01) |

## 8. Testing

| ID | Requirement |
|---|---|
| NFR-TST-01 | PyTest. Unit tests in `test/unit/`, fixtures in `test/testdata/`, plans in `test/plans/` |
| NFR-TST-02 | **Tests are written before the change** (`.agents/workingrules.md`) |
| NFR-TST-03 | The compile gate runs in CI for all four cases |
| NFR-TST-04 | LLM-dependent tests use recorded fixtures by default; live tests are opt-in via `--live` |
| NFR-TST-05 | Coverage ≥80% on `core/`, `evidence/`, `emit/`, `validate/` |
| NFR-TST-06 | The benchmark suite is one command: `spec-forge bench` |

NFR-TST-04 keeps the suite fast and deterministic. A test suite that needs an API key and a network to run is a
test suite that stops being run.

## 9. Cost

| ID | Requirement |
|---|---|
| NFR-COST-01 | Per-case run cost tracked and reported |
| NFR-COST-02 | Caching makes re-runs during development near-free |
| NFR-COST-03 | Model tiering: Opus 5 for extraction and adjudication, Sonnet 5 for high-volume passes (ADR-002) |
| NFR-COST-04 | Vision calls are cached by image hash — an unchanged diagram is never re-analysed |

## 10. Documentation

| ID | Requirement |
|---|---|
| NFR-DOC-01 | Every subsystem has a standalone spec in `docs/specifications/` |
| NFR-DOC-02 | Every cross-cutting decision has an ADR |
| NFR-DOC-03 | `docs/design/sourcemap.md` is current |
| NFR-DOC-04 | `README.md` gets a clean clone to a compiling model |
| NFR-DOC-05 | Each spec is readable by a team member who did not build that subsystem |

NFR-DOC-05 is the individual-probe requirement (`14_acceptance_criteria_and_evaluation.md` §7.3) expressed as a
documentation standard. It is why specs state rationale, not just mechanism.
