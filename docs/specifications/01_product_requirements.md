# 01 — Product Requirements

**Status:** Baseline · **Source:** CCTech Millennium Hackathon PRD — System Modelling, v1.2 / PRD v0.1, 16 Sep 2026
**Traceability:** every requirement below carries an `SF-*` id used by tests and by `14_acceptance_criteria_and_evaluation.md`.

---

## 1. Problem statement

Systems engineers spend a large share of their modelling effort on **translation rather than engineering**.
A plant description arrives as a paragraph of prose, a scanned P&ID, a whiteboard photograph, a
requirements table in a spreadsheet, and a vendor datasheet in PDF. Turning that pile into a structured
system model, and then into something that simulates, is manual, slow, and dependent on the modeller's own
conventions.

Every user arrives with different inputs, notation, completeness and house conventions. **That variability is
precisely why rule-based parsers and fixed templates have historically failed**, and precisely why language
models are a credible approach now.

> The interesting engineering question is not whether a language model can emit Modelica syntax. It is how to
> architect a system that stays **correct, traceable, and honest about what it does not know**, when the input
> is ambiguous and the output must be physically valid.

## 2. Objective

Build a product that takes engineering inputs in natural form and returns a system model that an engineer can
**review, trust, and run** in Modelica tools.

Success means an engineer can hand the tool a messy description of a physical system and get back, without
hand-writing the model, a structural model they recognise as correct and a simulation they can execute.

## 3. Intended users

| User | Need |
|---|---|
| **Systems engineer** ← *our chosen primary* | Convert a specification or sketch into a first-pass SysML model without starting from a blank canvas |
| Simulation engineer | Get a Modelica skeleton that compiles, so effort goes into physics and tuning rather than boilerplate |
| Design reviewer | See the assumptions the model made explicit, and trace each element back to the input that justified it |
| Domain newcomer | Produce a structurally legal model without deep tool expertise |

The PRD permits narrowing to a single user and building depth. **We state our choice: the systems engineer.**
See `02_user_personas_and_journeys.md` and ADR-010. Secondary needs (reviewer traceability, simulation-engineer
compilability) are served because they fall out of the same architecture, not because we targeted them.

## 4. Scope

### 4.1 Minimum scope — required for a valid submission

| ID | Requirement |
|---|---|
| **SF-MIN-01** | Accept **at least one input modality end to end**, with text as the baseline. |
| **SF-MIN-02** | Produce a **structured intermediate representation** of the system: parts, ports, connections, attributes. |
| **SF-MIN-03** | Emit a **SysML representation** of that model. |
| **SF-MIN-04** | Emit a **Modelica model that compiles without error** in OpenModelica or an equivalent tool. |
| **SF-MIN-05** | Demonstrate the full path on **at least one of the four supplied test cases**. |
| **SF-MIN-06** | **List assumptions made and information found missing.** |

> Scope expansion is rewarded when it is **coherent**, not when it is merely large.

### 4.2 Extensions we commit to

Selected from the PRD's suggested list. Each maps to a phase in `docs/implementation_plan.md`.

| ID | Extension | Phase |
|---|---|---|
| **SF-EXT-01** | Additional input modalities: images, scanned drawings, PDFs, spreadsheets | 2 |
| **SF-EXT-02** | Clarifying dialogue — the system asks targeted questions instead of guessing | 4 |
| **SF-EXT-03** | State machine and interlock generation, not just structure | 1–2 |
| **SF-EXT-04** | Simulation execution with plotted results | 3 |
| **SF-EXT-05** | **Model repair** — a compile error is fed back and corrected autonomously | 3 |
| **SF-EXT-06** | Round-trip editing — a user correction updates the model and the traceability record | 4 |
| **SF-EXT-07** | Confidence scoring per generated element | 2 |
| **SF-EXT-08** | **Library / reuse mechanism** — a component modelled once is recognised again | 2 |

### 4.3 Out of scope — do not build

- Proprietary or confidential plant data of any kind. **Use only the supplied cases or material we are free to share.**
- Hardware-in-the-loop or real-time control deployment.
- Chamber-level or plant-level industrial benchmarks requiring curated internal engineering data.

## 5. Inputs

> The product **must assume inputs are unstructured, inconsistent, and incomplete. There is no fixed input
> schema, and there will not be one.**

### 5.1 Modalities

| Modality | Examples | Our support |
|---|---|---|
| **Text** | Prose plant description, operating procedure, numbered requirements list, email thread, pasted specification | Phase 1 |
| **Image** | Whiteboard photo, hand-drawn sketch, scanned P&ID or block diagram, schematic screenshot | Phase 2 (vision) |
| **Document** | PDF spec or datasheet, Word requirements doc, spreadsheet of parameters, tabular component list | Phase 1–2 |
| **Mixed bundle** | Any combination describing one system, **possibly with overlaps and contradictions** | Phase 2 |

### 5.2 Properties the input will have

These are **first-class parts of the evaluation, not edge cases.**

| Property | Meaning | Where we handle it |
|---|---|---|
| **Incomplete** | Parameters, units and initial conditions will be missing | `05_evidence_precedence_spec.md` — assumptions |
| **Ambiguous** | The same component may be named differently in two places | `04_ingestion_spec.md` — alias resolution |
| **Contradictory** | A diagram and a paragraph may disagree | `05_evidence_precedence_spec.md` — conflicts |
| **Implicit** | Conventions assumed rather than stated (a tank has an outlet even when the text never says so) | `06_component_library_spec.md` — archetype defaults |
| **Custom** | Every user brings their own notation and vocabulary | LLM extraction, not rule-based parsing |

### 5.3 Required input-handling behaviour — mandatory

| ID | Requirement | Enforced by |
|---|---|---|
| **SF-IN-01** | Missing information **must be either inferred with a stated assumption, or surfaced as a question. It must not be silently invented.** | Validator `V-TRACE-001` |
| **SF-IN-02** | Contradictions **must be flagged rather than resolved arbitrarily.** | `Conflict` record, `V-CONF-001` |
| **SF-IN-03** | The system **must not fabricate components, ports, or physics** that are not derivable from the input or from a declared standard assumption. | Validator `V-TRACE-001`, `V-LIB-001` |

`SF-IN-01`–`SF-IN-03` are the honesty requirements. They are enforced **mechanically** — the IR cannot
validate if any element lacks provenance. See `03_system_ir_spec.md` §5.1.

## 6. Expected output — five layers

Output is layered. A submission need not deliver every layer, but **the layers it does deliver must be
consistent with one another.** We deliver all five.

| Layer | Name | Content | Our artifact |
|---:|---|---|---|
| **1** | Structured system representation | Parts, ports, connections, attributes and units, and where applicable states and transitions. Format is the team's choice. **This layer exists so the SysML and Modelica outputs come from a single source of truth.** | `model.sfir.json` — see `03_system_ir_spec.md` |
| **2** | SysML model | **SysML v2 textual is a must.** Structural decomposition, ports and interfaces, connections, and behaviour where required. | `model.sysml` — see `07_sysml_emission_spec.md` |
| **3** | Evidence and traceability | Assumptions made, missing or ambiguous information, traceability from **input fragment to model element**, and simulation output where available. | `evidence.json`, `traceability.md` — see `10_traceability_and_reporting_spec.md` |
| **4** | Human-readable summary | The system as the model understands it, suitable for an engineer to **skim and approve or reject in under a minute**. | `summary.md` — see `10_traceability_and_reporting_spec.md` |
| **5** | Modelica model | A `.mo` model of the same system. **It must compile.** Where the problem is well posed enough to run, it should simulate and produce plausible trajectories. MSL use encouraged. | `Model.mo` — see `08_modelica_emission_spec.md` |

> **Note from the PRD:** Generating SysML and Modelica independently is the most common way to get silent
> divergence between them.

**Our answer:** both are deterministic emitters over one validated IR, plus an explicit round-trip consistency
check (`09_validation_and_repair_spec.md` §6). This is ADR-001 and is the single most important architectural
decision in the project.

## 7. Acceptance criteria

> Exact numeric targets are deliberately loose. These are thresholds for a credible submission, not a scoring
> rubric, and judges will weigh reasoning quality alongside them.

### 7.1 Speed

| ID | Stage | Target |
|---|---|---|
| **SF-SPD-01** | First structural draft from a text input | **Under 2 minutes** |
| **SF-SPD-02** | Full pipeline to compiling Modelica, single test case | **Under 10 minutes** (provided cases must meet this) |
| **SF-SPD-03** | End-to-end live demonstration during judging | Within the allotted demo slot, on a normal laptop or standard API access |

> Latency from genuine multi-step reasoning or self-correction is acceptable and **will not be penalised on its
> own. Silence with no progress indication will be.**

→ Progress streaming is therefore a **requirement, not a nicety**: `12_api_spec.md` §5 (SSE) and `11_web_application_spec.md` §4.

### 7.2 Accuracy

| ID | Dimension | Expectation |
|---|---|---|
| **SF-ACC-01** | Structural correctness | Parts, ports and connections materially match the reference for the attempted case. **Aim for 80% or better element coverage on L1 and L2.** |
| **SF-ACC-02** | **Compilability** | The generated Modelica compiles without error. **This is a hard gate, not a target.** |
| **SF-ACC-03** | Simulatability | For L1 and L2, the model runs and produces physically plausible behaviour |
| **SF-ACC-04** | Behavioural correctness | Where a state machine is required, **required states are reachable and forbidden combinations are prevented** |
| **SF-ACC-05** | **Repeatability** | The same input run twice yields a **structurally equivalent** model. Naming variation is acceptable, **topology variation is not.** |
| **SF-ACC-06** | **Honesty** | No fabricated components. **Every element traces to an input fragment or a declared assumption.** |

> A model that is partially complete and honest about its gaps **scores above** one that is superficially
> complete and quietly wrong. This is deliberate.

This sentence is the product thesis. It is why `05_evidence_precedence_spec.md` exists and why the honesty
validators are blocking rather than advisory.

### 7.3 Scope

- **One test case solved end to end beats four solved partially.**
- **Generalisation beats case-specific handling.** If the pipeline contains logic that only fires for the two-tank problem, **say so, because judges will look.**
- Depth in one input modality beats shallow coverage of all three.

→ `SF-SCP-01`: **no case-specific branching is permitted in `src/spec_forge/`.** Case knowledge lives in data
(`test/testdata/benchmarks/*/manifest.yaml`) and in the versioned component library, never in control flow.
Enforced by test `test/unit/test_no_case_specific_logic.py`. See ADR-005.

## 8. Architecture considerations the judges will ask about

Verbatim from PRD §10, with our committed answer and where it is defended.

| Question | Our answer | Where |
|---|---|---|
| Where does the language model sit: end-to-end generation, or **extraction into a schema followed by deterministic code generation**? *The second is usually more reliable and easier to defend.* | Extraction into a typed schema; **all emission is deterministic Jinja over the IR.** The LLM never writes SysML or Modelica syntax. | ADR-001 |
| How do you validate before showing the user: compile-check, schema-validate, unit-check, or simulate? | **All four**, as an ordered gate ladder with defined severities. | `09_validation_and_repair_spec.md` |
| What happens on failure: retry, repair loop, degrade gracefully, or ask the user? | **All four, in that order**, bounded and logged. | `09_validation_and_repair_spec.md` §4–5, ADR-007 |
| How is agentic behaviour used? *Using an agent where a single call would do is not automatically better.* | LangGraph state machine. Exactly two nodes are agentic — **repair** (loops against compiler/validator output) and **clarification** (loops against user answers). Extraction, conflict adjudication, alias resolution and record detection are each a single schema-constrained LLM call, not agents. Emission and validation are plain code. | ADR-004 |
| How do you keep the three output layers consistent? | One IR, deterministic emitters, plus an explicit round-trip consistency checker. | ADR-001, `09_validation_and_repair_spec.md` §6 |
| How is domain knowledge injected: prompting, **retrieval over a component library**, fine-tuning, or **a typed schema that constrains what can be generated**? | Both of the two defensible options: a **versioned typed component library** retrieved at extraction time, binding into a **schema-constrained IR**. | ADR-006, `06_component_library_spec.md` |

## 9. Benchmark cases

Four problems form a **deliberate difficulty ladder, where each level adds one new class of reasoning rather
than a new subject area.**

| Level | Case | Reasoning skill under test |
|---|---|---|
| **L1** | Two-Tank Controller | Sequencing, interlocks, state machines, safe start and stop. Structural basics, no physics coupling |
| **L2** | Room CO2 Ventilation Controller | Closed-loop feedback: disturbance, sensor, control law, actuator acting back on the process |
| **L3** | Magnetic Circuit | Multiphysics energy transfer across domains, with an explicit loss path |
| **L4** | Water and NaCl Evaporation Plant | Integration: material supply, heating, transformation, separation into two streams, coordinated under one controller |

L4 is **not a new skill** — it is the composition of the previous three under competing constraints, which is
why it is the hardest.

> These problems are **proxies**, chosen because their reasoning patterns are structurally faithful to far more
> complex industrial equipment. Valve sequencing in a two-tank rig is the same pattern as sequencing in a
> process gas delivery chain. A CO2 loop is the same pattern as chamber pressure control.
> **Do not optimise for tanks and brine. Optimise for the pattern.**

Full analysis per case: `17_benchmark_cases_spec.md` and `benchmarks/L1`–`L4`.

## 10. Evaluation alignment

| Outcome | How this problem tests it | Our evidence |
|---|---|---|
| **Domain understanding** | Whether the generated model is **physically and structurally sensible, not just syntactically valid** | Physics validators, reference-trace comparison |
| **AI architecture** | How the pipeline is composed, validated, and **made to fail safely**, and whether the agentic design is justified | ADR set, degradation ladder |
| **Design thinking** | Who the product is for, **how ambiguity is surfaced to the user**, and whether an engineer would actually trust and use it | Persona doc, conflict/assumption UI |
