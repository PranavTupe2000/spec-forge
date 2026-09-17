# Index of Specification Documents for SpecForge Toolkit

This is the index of specification documents of SpecForge Toolkit.

The index format is
- `<relative document path>` : {{short 2-3 lines description of document content}}

## How to use this file
- Use this file to determine which specification documents to load.
- Do not load all specification documents every time.
- Update the index whenever you add a new specification document.

## Reading order for a new contributor

Read **00**, **01** and **02** first — they establish the constraints, the requirements and the user.
Then **03**, because every other subsystem is defined in terms of the IR.
Then the spec for the subsystem you are working on.

## Specification Document Index

### Frame — read first

- `00_product_brief.md` : Hackathon constraints, the 45/10/45 scoring split, the four submission artifacts, the 45-minute evaluation structure, fair-play rules, and our committed scope decisions. **The non-negotiable frame — if another document conflicts with this one, this one wins.**
- `01_product_requirements.md` : The PRD migrated into numbered `SF-*` requirements: objective, users, minimum scope, committed extensions, input properties and mandatory handling behaviour, the five output layers, and the speed/accuracy/scope acceptance criteria.
- `02_user_personas_and_journeys.md` : The chosen target user (systems engineer), the primary journey through a messy document folder, the six things the user must never experience, and the five design principles in priority order.

### Core — the single source of truth

- `03_system_ir_spec.md` : **The SFIR schema.** Parts, ports, connections, attributes, state machines, constraints, requirements, provenance, conflicts, assumptions, open questions, traces. Defines the provenance invariant that makes fabrication structurally impossible. **Every other module is defined in terms of this document.**

### Input side

- `04_ingestion_spec.md` : Loaders for 11 file types across three modality groups, the fragment and locator model, the image-only-PDF fallback, per-message email splitting, PlantUML and legacy Modelica parsing, vision extraction, alias resolution, caching and replay.
- `05_evidence_precedence_spec.md` : **The heart of the product.** The 12 authority tiers, the transmission rule (authority attaches to the record cited, not the medium), the `PRE-01` resolution algorithm, the never-merge-across-`value_kind` rule, conflicts, the standard-assumption catalogue, and open questions.
- `06_component_library_spec.md` : Typed engineering archetypes with paired SysML and Modelica bindings, the retrieval strategy with closed-set selection, the unbound-archetype error, and cross-run binding reuse.

### Output side

- `07_sysml_emission_spec.md` : Deterministic SysML v2 textual emission — mapping rules, units from ISQ/SI, port causality, state machines, requirements and satisfy relations, assumptions and conflicts as documentation, and the element map used for round-trip checking.
- `08_modelica_emission_spec.md` : Deterministic Modelica emission — component binding, mandatory units, the two state-machine strategies, interlocks with scoped exceptions, **the `omc` compile gate**, simulation, and the nine known MSL hazards.
- `10_traceability_and_reporting_spec.md` : The one-minute human summary (layer 4) and the full traceability record (layer 3), the mandatory "what this model does NOT cover" section, simulation reporting, and the run directory layout.

### Control

- `09_validation_and_repair_spec.md` : The four-gate validation ladder, the full rule catalogue (`V-TRACE`, `V-UNIT`, `V-TOPO`, `V-BEH`, `V-PHYS`, `V-LIB`, `V-MOD`), the retry→repair→degrade→ask ladder, the bounded repair loop, the SysML↔Modelica consistency check, and reference-trace comparison.
- `16_pipeline_orchestration_spec.md` : The LangGraph graph and state, why only two nodes are agents, the seven extraction passes and their merge order, model selection, prompt versioning, and record/replay.

### Product surface

- `11_web_application_spec.md` : React/ShadCN/R3F SaaS — information architecture, the run overview, progress streaming, the evidence view, the three-view model explorer, clarifying dialogue, round-trip editing. Constrained to be a client of the pipeline, never a participant.
- `12_api_spec.md` : FastAPI contract — resources, endpoints, the run lifecycle including the `degraded` terminal state, SSE progress events with the 2-second heartbeat contract, RFC 7807 errors, and CLI parity.
- `13_data_model_spec.md` : PostgreSQL schema — projects, sources, fragments, runs, the claim/conflict ledger, tier-0 overrides that persist across runs, component bindings, migrations, and `--no-db` degradation.

### Cross-cutting

- `14_acceptance_criteria_and_evaluation.md` : The definition of done. Every speed, accuracy, scope and honesty criterion mapped to an automated test, submission readiness for the four artifacts, evaluation preparation per segment, and the pre-demo checklist.
- `15_nonfunctional_spec.md` : Determinism and repeatability, performance, observability, reliability and failure, security and data handling, portability (Windows-first), maintainability, testing, cost, documentation.

### Benchmarks

- `17_benchmark_cases_spec.md` : The four-level ladder, the shared nine-folder bundle structure, **the shared five-part trap pattern**, what the engineering registers reveal about precedence, and per-case acceptance expectations.
- `benchmarks/L1_two_tank.md` : Sequencing, interlocks, state machines. Nine controller states, `SHUT > STOP > START` priority, timer freeze-on-pause, the V2/V3 interlock waived only in SHUTDOWN, and the CR-004 precedence problem (0.78 → 0.80 m).
- `benchmarks/L2_room_co2.md` : Closed-loop feedback. The four-representation unit chain (ppm / kg/kg / normalised / ACH), the rejected "1000 ppm above outdoor" reading, `C_source = 100 kg/kg` as a numerical device, and the negative-`m_flow` sign convention.
- `benchmarks/L3_magnetic_circuit.md` : Multiphysics with a loss path. The parallel gap/leakage branch, RMS phasor convention, both grounds mandatory, and the nominal-vs-as-built air gap that must **not** be reported as a conflict.
- `benchmarks/L4_nacl_evaporation.md` : Integration. Parallel split/join forcing StateGraph emission, the CR-017 return-routing correction that topology cannot derive, StandardWater vs WaterNaCl as configurations rather than a conflict, and mandatory junction volumes.
