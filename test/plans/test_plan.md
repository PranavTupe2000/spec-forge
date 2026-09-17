# Test Plan — SpecForge Toolkit

**Framework:** PyTest · **Layout:** `test/unit/`, fixtures in `test/testdata/`, plans here
**Rule:** tests are written **before** the change (`.agents/workingrules.md`)

---

## 1. Strategy

Three tiers, fastest first. CI runs tiers 1 and 2 on every commit; tier 3 on every push.

| Tier | Scope | Network | Runtime |
|---|---|---|---|
| **1 · Unit** | Pure logic — precedence, units, validators, id generation, templates | none | seconds |
| **2 · Integration** | Loaders, emitters, toolchain wrappers, persistence | none (recorded LLM fixtures) | ~1 min |
| **3 · Benchmark** | All four cases end to end, including `omc` | none by default | minutes |

**LLM-dependent tests use recorded fixtures by default.** Live calls are opt-in via `--live` (NFR-TST-04). A
suite that needs an API key and a network is a suite that stops being run.

## 2. Directory layout

```
test/
├── plans/            this document and per-phase plans
├── unit/
│   ├── core/         IR models, units, ids, schema
│   ├── ingest/       one module per loader, plus dispatch and aliases
│   ├── evidence/     tiers, transmission, precedence, conflicts, assumptions
│   ├── library/      archetype schema, bindings, retrieval
│   ├── extract/      pass schemas, merge order
│   ├── validate/     one module per rule family, plus the ladder and consistency
│   ├── emit/         sysml, modelica, report
│   ├── toolchain/    omc and sysml wrappers
│   ├── repair/       diagnosis, actions, loop bounds
│   ├── pipeline/     graph, state, events, replay
│   ├── persistence/  migrations, repositories
│   ├── api/          routes, SSE, errors
│   └── architecture/ layer dependencies, the A1–A8 rules
└── testdata/
    ├── benchmarks/   the four supplied bundles + manifest.yaml
    ├── expected/     elements, conflicts, parameters per case
    └── fixtures/     small crafted inputs for unit tests
```

## 3. Architecture tests — the rules that must not decay

These fail the build if the design erodes. They are the highest-value tests in the suite because each one
protects a decision we will be asked to defend.

| Test | Asserts | Rule |
|---|---|---|
| `test_layer_dependencies.py` | Module imports respect layer order; graph is acyclic | ARCHITECTURE §Layers |
| `test_emitter_inputs.py` | Emitters import nothing from `ingest`, `extract` or `pipeline` | A1 |
| `test_no_llm_in_emit.py` | No Anthropic client import under `emit/` or `validate/` | A3 |
| **`test_no_case_specific_logic.py`** | No benchmark name, case tag or bundle filename in `src/` | **A4, SF-SCP-01** |
| `test_repair_patches_ir.py` | No repair action writes to an emitted artifact | A5 |
| `test_cli_without_frontend.py` | Pipeline completes with `frontend/` absent | A7 |
| `test_no_db_mode.py` | Pipeline completes with `--no-db` | A7 |
| `test_agent_count.py` | Exactly two looping nodes in the graph | ADR-004 |

`test_no_case_specific_logic.py` deserves a note. It greps `src/` for case identifiers, benchmark tags
(`TK-101`, `RM-201`, `LIS-301`, …) and bundle filenames. The allowlist is `library/` data files and `test/`. If
a case-specific shortcut ever becomes genuinely necessary, the test is updated **and the exception is declared
in `DECISIONS.md`** — visible rather than hidden, because the PRD says judges will look.

## 4. Honesty tests

The product's differentiator, tested directly.

| Test | Asserts |
|---|---|
| `test_provenance_invariant.py` | An IR with an unprovenanced entity fails to validate |
| `test_no_assumed_components.py` | A part justified only by an assumption is rejected (`V-TRACE-002`) |
| `test_assumption_catalogue_only.py` | A free-form assumption is rejected (`V-TRACE-003`) |
| `test_no_silent_defaults.py` | Every applied default is a registered assumption and appears in the summary |
| `test_summary_sections.py` | "What this model does NOT cover" present and non-empty |
| `test_expected_conflicts.py` | Per case: every `must_detect` found, every `must_not_report` absent |

`test_expected_conflicts.py` tests **both directions**. Missing a real conflict and inventing a false one are
equal failures — L3's nominal-vs-as-built air gap and L4's medium configurations must *not* be reported.

## 5. Per-case benchmark tests

Driven by `test/testdata/expected/<case>/`.

| Test | Target |
|---|---|
| `test_ingest_<case>.py` | Every file ingests; fragment counts within expected bounds |
| `test_conflicts_<case>.py` | Against `conflicts.yaml` |
| `test_parameters_<case>.py` | Effective values against `parameters.yaml`; `must_not_select` absent |
| `test_structural_coverage_<case>.py` | ≥80% coverage and reported precision, against `elements.yaml` |
| **`test_compiles_<case>.py`** | **`omc checkModel` green — the hard gate** |
| `test_simulate_<case>.py` | L1, L2, L4: runs and matches the reference trace within manifest tolerances |
| `test_no_manifest_<case>.py` | Case passes with `--no-manifest` |

## 6. Determinism and repeatability

| Test | Asserts |
|---|---|
| `test_deterministic_ids.py` | Ids are a pure function of name and kind |
| `test_sorted_collections.py` | Serialised collections are id-sorted |
| `test_emit_deterministic.py` | Same IR twice → identical bytes, both emitters |
| `test_repeatability.py` | `bench --repeat 2` → structurally equivalent (topology identical, names may vary) |

## 7. Failure-mode tests

Because degradation is a feature (ADR-007), it is tested like one.

| Test | Asserts |
|---|---|
| `test_degradation_per_stage.py` | A forced failure at each stage still yields partial output + a gap report |
| `test_unsupported_file.py` | An unknown file type is recorded, not fatal |
| `test_corrupt_file.py` | A corrupt file produces a diagnostic, not a traceback |
| `test_zero_fragments.py` | No extractable content anywhere → blocking, stated plainly |
| `test_repair_bounded.py` | Never exceeds 3 attempts |
| `test_blocking_question_halts.py` | A blocking question halts emission and returns partial artifacts |
| `test_consistency_detects_divergence.py` | A desynchronised emitter pair is caught |

## 8. Known-hazard regression tests

One per trap found in the supplied data. Each encodes a real failure the pipeline must not regress into.

| Test | Hazard |
|---|---|
| `test_pdf_image_only.py` | A PDF with no text layer still yields fragments (the briefing PDF proves this is real) |
| `test_email_per_message_split.py` | A thread splits into dated messages, each independently citable |
| `test_quoted_printable_numbers.py` | QP soft line breaks do not corrupt numbers (`0.8=\n0 m`) |
| `test_transmission_rule.py` | An email announcing an approved CR inherits tier 1 |
| `test_proposed_not_approved.py` | "I will raise CR-017" does not transmit authority |
| `test_rejected_record_dropped.py` | A record rejected by name transmits nothing |
| `test_value_kind_never_merged.py` | Nominal and as-built are not treated as competing candidates |
| `test_legacy_mo_demoted.py` | Legacy parameter fragments are demoted; structural fragments are not |
| `test_puml_omission_note.py` | A diagram's "does not show" note becomes open questions |
| `test_interlock_scoped_exception.py` | A waived interlock emits with its scope condition intact |
| `test_vision_not_sole_numeric_source.py` | A numeric value resting only on vision is rejected (`V-VIS-001`) |

## 9. Performance

| Test | Target |
|---|---|
| `test_speed_first_draft.py` | Structural draft < 2 min (SF-SPD-01) |
| `test_speed_full_pipeline.py` | Full pipeline per case < 10 min (SF-SPD-02) |
| `test_sse_heartbeat.py` | No gap over 2 s between progress events (SF-UX-03) |

## 10. Coverage targets

≥80% line coverage on `core/`, `evidence/`, `emit/`, `validate/` (NFR-TST-05). Coverage is not tracked on
`api/` or `cli/`, which are thin and covered by integration tests instead.

## 11. Running

```bash
uv run pytest                              # tiers 1-2
uv run pytest test/unit/architecture       # the rules
uv run pytest -m benchmark                 # tier 3
uv run pytest --live                       # include live API calls
uv run spec-forge bench                    # the full benchmark suite
uv run spec-forge bench --repeat 2         # repeatability
```
