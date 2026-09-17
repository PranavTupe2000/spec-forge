# 03 — System IR (SFIR) Specification

**Status:** Baseline · **Decision:** ADR-001 · **Schema version:** `sfir/1.0`
**Implements:** PRD output layer 1 · **Consumed by:** SysML emitter, Modelica emitter, report emitter, web UI

---

## 1. Purpose and the rule that follows from it

> *"This layer exists so the SysML and Modelica outputs come from a single source of truth."* — PRD, output layer 1

**The SFIR is the only source of truth.** Two rules follow, and they are absolute:

- **R1 — Single origin.** No emitter may read anything except a validated SFIR document. Not the raw files, not
  the LLM transcript, not the fragments directly. If an emitter needs a fact, that fact must first exist in the IR.
- **R2 — No emission-time inference.** Emitters are pure, total functions `SFIR → text`. They may not guess,
  default, or fill a gap. A missing value is an IR defect to be fixed upstream, never patched in a template.

R1 and R2 exist because the PRD names the failure they prevent: *"Generating SysML and Modelica independently is
the most common way to get silent divergence between them."* If emitters can infer, they will infer differently,
and divergence returns through the back door.

Serialised as **JSON** (`model.sfir.json`), defined by **Pydantic v2** models in `src/spec_forge/core/ir/`,
exported to **JSON Schema** at `build/schema/sfir-1.0.schema.json` for the frontend and for CI validation.

## 2. Document structure

```jsonc
{
  "sfir_version": "1.0",
  "model":        { /* ModelHeader */ },
  "sources":      [ /* SourceDocument[] */ ],
  "fragments":    [ /* SourceFragment[] */ ],
  "parts":        [ /* Part[] */ ],
  "ports":        [ /* Port[] */ ],
  "connections":  [ /* Connection[] */ ],
  "attributes":   [ /* Attribute[] */ ],
  "state_machines": [ /* StateMachine[] */ ],
  "requirements": [ /* Requirement[] */ ],
  "constraints":  [ /* Constraint[] */ ],
  "assumptions":  [ /* Assumption[] */ ],
  "conflicts":    [ /* Conflict[] */ ],
  "open_questions": [ /* OpenQuestion[] */ ],
  "traces":       [ /* TraceLink[] */ ],
  "diagnostics":  [ /* Diagnostic[] */ ],
  "provenance_summary": { /* counts, coverage, confidence histogram */ }
}
```

Flat collections joined by id, **not** a nested tree. Reasons: a part can appear in several decompositions;
the UI needs `O(1)` lookup by id; and JSON Patch diffs stay readable for round-trip editing (SF-EXT-06).

## 3. Identity and naming

| Field | Rule |
|---|---|
| `id` | Stable, unique within the document. Format `<kind>:<slug>`, e.g. `part:tank_1`, `port:tank_1.outlet`, `conn:hyd_03`. |
| `name` | The **canonical** name chosen by alias resolution. |
| `aliases[]` | **Every** surface form seen in the inputs, each with the fragments it appeared in. |
| `tag` | The formal engineering tag when one exists (`TK-101`). Null if the documents never give one. |
| `qualified_name` | Dotted path for nested parts (`plant.tank_1`). Derived, not stored by hand. |

Alias retention is not cosmetic. L1 alone uses `tank1`, `T1` and `TK-101` for one object across five documents;
L2 distinguishes `freshAir` (Modelica instance) from `SRC-OA-201` (tag) from "outdoor air supply" (prose). The
traceability report must be able to answer *"which words in which document produced this part?"*, and the
Modelica emitter must be able to reuse the legacy instance name so a human recognises the output.

**Determinism requirement (SF-ACC-05):** `id` generation must be a pure function of canonical name and kind, and
all collections are sorted by `id` before serialisation. No UUIDs, no timestamps, no dict-iteration order in the
output. Two runs over the same input must produce byte-comparable structure.

## 4. Core entities

### 4.1 `Part`

A structural element. Maps to a SysML `part def` + `part` usage, and to a Modelica component instance.

```jsonc
{
  "id": "part:tank_1",
  "name": "tank1",
  "tag": "TK-101",
  "aliases": [ {"text": "T1", "fragment_ids": ["frag:urs001#p1.t2.r3"]} ],
  "archetype": "fluid.tank.vertical",      // → component library key, see 06
  "kind": "component",                      // component | subsystem | boundary | actor | environment
  "parent_id": null,
  "description": "Intermediate receiving tank",
  "port_ids": ["port:tank_1.inlet", "port:tank_1.outlet", "port:tank_1.level"],
  "attribute_ids": ["attr:tank_1.area", "attr:tank_1.level_init"],
  "provenance": { /* Provenance */ }
}
```

`archetype` is the binding point to the component library (`06_component_library_spec.md`). It is what lets the
Modelica emitter know that `fluid.tank.vertical` maps to a specific MSL component with known ports, and what lets
the SysML emitter reuse a shared `part def`. **An unbound archetype is a hard validation error** — it means we
recognised a part but not what it *is*, and emitting it would be guesswork.

### 4.2 `Port`

```jsonc
{
  "id": "port:tank_1.outlet",
  "owner_id": "part:tank_1",
  "name": "outlet",
  "port_type": "fluid",          // see table below
  "direction": "out",            // in | out | inout | acausal
  "medium": "liquid_water",
  "quantity": "VolumeFlowRate",
  "unit": "m3/s",
  "provenance": { /* Provenance */ }
}
```

| `port_type` | Physical meaning | SysML | Modelica |
|---|---|---|---|
| `fluid` | Mass/volume flow with pressure | interface with flow/effort | `Modelica.Fluid.Interfaces.FluidPort_a/b` |
| `electrical` | Current/voltage | " | `Modelica.Electrical.Analog.Interfaces.Pin` |
| `magnetic` | Flux / magnetic potential | " | `Modelica.Magnetic.FluxTubes.Interfaces.PositiveMagneticPort` |
| `thermal` | Heat flow / temperature | " | `Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a` |
| `mechanical` | Force/velocity, torque/angle | " | `Modelica.Mechanics.*.Interfaces.Flange_a` |
| `signal_real` | Causal real signal | directed interface | `Modelica.Blocks.Interfaces.RealInput/Output` |
| `signal_boolean` | Causal boolean | " | `Modelica.Blocks.Interfaces.BooleanInput/Output` |
| `signal_integer` | Causal integer | " | `Modelica.Blocks.Interfaces.IntegerInput/Output` |

**`direction: "acausal"` is mandatory for physical port types.** Fluid, electrical, magnetic, thermal and
mechanical ports do not have a direction in the causal sense — assigning one is a modelling error that produces
Modelica which compiles but is physically wrong. Only signal ports carry `in`/`out`. Validator `V-PORT-002`.

### 4.3 `Connection`

```jsonc
{
  "id": "conn:hyd_02",
  "source_port_id": "port:valve_1.outlet",
  "target_port_id": "port:tank_1.inlet",
  "medium": "liquid_water",
  "interface_tag": "IF-HYD-02",
  "nominal_value": {"value": 0.006, "unit": "m3/s"},
  "provenance": { /* Provenance */ }
}
```

Connections join **ports, never parts**. A part-to-part edge (which is all a PlantUML draft or a hand sketch
gives us) is ingested as a `proto_connection` diagnostic and must be resolved to ports before validation passes.
This matters because every supplied benchmark ships a `.puml` that draws exactly such part-level arrows.

### 4.4 `Attribute`

```jsonc
{
  "id": "attr:tank_1.high_limit",
  "owner_id": "part:tank_1",
  "name": "T1_High",
  "value": 0.80,
  "unit": "m",
  "quantity": "Length",
  "value_kind": "effective_setpoint",
  "candidates": [
    {"value": 0.80, "unit": "m", "authority": "CR-004",       "tier": 1,  "effective_date": "2026-03-11", "selected": true},
    {"value": 0.78, "unit": "m", "authority": "URS-001 Rev A","tier": 3,  "effective_date": "2026-01-15", "selected": false,
     "status": "superseded"}
  ],
  "conflict_id": "conflict:t1_high",
  "provenance": { /* Provenance */ }
}
```

`candidates[]` is **required whenever more than one value was found**, and losing candidates are retained
permanently. Discarding them would violate SF-IN-02 (*flag, do not resolve arbitrarily*) and would make the
traceability report unable to answer *"why not 0.78?"* — which is exactly the question a design reviewer asks.

`value_kind` carries the distinction L3's design review demands as decision 10 (*"preserve the distinction
between model parameter, as-built measurement, and verification configuration"*):

| `value_kind` | Meaning | Benchmark example |
|---|---|---|
| `requirement` | A stated requirement value | CO2 ≤ 1000 ppm |
| `effective_setpoint` | Current approved operating value | T1 high = 0.80 m (CR-004) |
| `nominal_design` | Design/analytic value | air gap δ = 1.50 mm |
| `as_built_measurement` | Measured on physical hardware — **never** silently replaces nominal | gap measured 1.58 mm |
| `verification_config` | Value used in a test configuration only | TP-17 event schedule |
| `numerical_device` | An implementation artefact with no physical meaning | `C_source = 100 kg/kg` |
| `derived` | Computed from other attributes; carries `derivation` | `gainSensor = 1/1.519e-3` |

`numerical_device` and `as_built_measurement` exist solely because the benchmark authors built traps around
them. A model that promotes an as-built measurement into the nominal analytic case is wrong (L3); a model that
presents a numerical device as a physical concentration is wrong (L2). The type system prevents both.

### 4.5 `StateMachine`, `State`, `Transition`

Required for L1 and L4; used for mode logic in L2.

```jsonc
{
  "id": "sm:tank_controller",
  "owner_id": "part:plc_101",
  "initial_state_id": "state:idle",
  "regions": [ {"id": "region:main", "state_ids": ["state:idle", "..."]} ],
  "states": [
    {
      "id": "state:fill_t1",
      "name": "FILL_T1",
      "outputs": [ {"port_id": "port:plc_101.cmd_v1", "value": true} ],
      "entry_actions": [], "exit_actions": [],
      "invariants": ["not cmd_v2", "not cmd_v3"],
      "provenance": {}
    }
  ],
  "transitions": [
    {
      "id": "trans:fill_to_wait",
      "source_state_id": "state:fill_t1",
      "target_state_id": "state:wait_after_fill",
      "trigger": {"kind": "condition", "expression": "LT_101 >= T1_High"},
      "priority": 10,
      "guard": null,
      "actions": [],
      "provenance": {}
    }
  ],
  "timers": [ {"id": "timer:post_fill", "duration_attr_id": "attr:ctrl.wait_after_fill",
               "on_suspend": "freeze_remaining"} ]
}
```

Three fields exist because the benchmarks require them:

- **`priority`** — L1 mandates `SHUT > STOP > START`. Without explicit priority, a generated state machine has
  ambiguous simultaneous-event behaviour and the interlock check cannot be decided.
- **`timers[].on_suspend`** — L1's DR-02 decision D-03 chose **freeze remaining delay** over restart. This is a
  behavioural semantic that cannot be recovered from the state graph alone.
- **`regions[]`** — L4 requires a **parallel split after evaporation and a join before cycle reset**. One flat
  region cannot express it.

### 4.6 `Constraint` — including interlocks

```jsonc
{
  "id": "constraint:interlock_v1_v2",
  "kind": "interlock",              // interlock | limit | invariant | permissive | relation
  "expression": "not (cmd_v1 and cmd_v2)",
  "scope": "global",                 // global | state:<id> | part:<id>
  "exceptions": [
    {"scope": "state:shutdown", "rationale": "DR-02 D-09 waives V2/V3 concurrency during controlled shutdown",
     "provenance": {}}
  ],
  "severity": "safety",
  "provenance": {}
}
```

`exceptions[]` is load-bearing. L1's V2/V3 interlock is waived **only** in SHUTDOWN — a scoped exception stated
in DR-02 and confirmed in the field notes (*"transfer + drain lamps on together. This is intentional for SHUT,
not an interlock failure"*). A model expressing it as an unconditional prohibition contradicts the approved
design; one that omits the interlock entirely fails SF-ACC-04. The exception must be *scoped and justified*, and
validator `V-BEH-003` checks that every waiver cites evidence.

### 4.7 `Requirement`

```jsonc
{
  "id": "req:urs_f_003",
  "external_id": "URS-F-003",
  "text": "V1 shall close when Tank 1 reaches the specified high-level limit.",
  "category": "functional",
  "priority": "must",
  "verification_method": "test",
  "status": "active",               // active | superseded | draft | withdrawn
  "superseded_by": null,
  "satisfied_by": ["state:fill_t1", "trans:fill_to_wait"],
  "verified_by": ["test:tp17_step_3"],
  "provenance": {}
}
```

`satisfied_by` is what makes the SysML output a *requirements model* rather than a block diagram. Unsatisfied
`must` requirements are reported, never hidden (`V-REQ-001`, severity `warn`).

## 5. Provenance — the honesty mechanism

Attached to **every** entity above. This is the schema-level enforcement of SF-IN-01/02/03 and SF-ACC-06.

```jsonc
{
  "kind": "evidence",              // evidence | assumption | derived | user_override
  "fragment_ids": ["frag:urs001#p1.s3.r4"],
  "assumption_id": null,
  "derived_from": [],
  "authority_tier": 3,
  "authority_record": "URS-001 Rev A",
  "confidence": 0.94,
  "extractor": "llm:claude-opus-5/structural_v3",
  "notes": null
}
```

### 5.1 The invariant

> **Every entity must have provenance where at least one of `fragment_ids`, `assumption_id`, or `derived_from`
> is non-empty.**

Enforced by validator **`V-TRACE-001`**, severity **error**, **blocking**. An IR that fails it cannot be emitted.

This single rule is how "no fabrication" stops being a prompt instruction — which a model can ignore — and
becomes a property of the type system, which it cannot. It is the most defensible answer we have to the PRD's
honesty criterion, and the individual-probe question *"how do you know it didn't make that up?"* has a
one-sentence answer: **it cannot serialise if it did.**

### 5.2 `confidence`

Float `0.0–1.0`, per element (SF-EXT-07). Bands: `≥0.9` high (direct statement in a controlled document);
`0.7–0.9` medium (inferred from structure or a single informal mention); `<0.7` low (surfaced in the UI and
listed in `summary.md`). Confidence **never** substitutes for provenance — a high-confidence element with no
fragment is still a validation error.

## 6. Source model

### 6.1 `SourceDocument`

```jsonc
{
  "id": "src:urs_001",
  "uri": "test/testdata/benchmarks/L1_two_tank/01_requirements/01_customer_URS.pdf",
  "media_type": "application/pdf",
  "title": "User Requirement Specification - Two-Tank Sequence Controller",
  "document_number": "URS-001",
  "revision": "A",
  "status": "released",             // approved | released | final | draft | superseded | informal | archived
  "issued_date": "2026-01-15",
  "authority_record": "URS-001 Rev A",
  "authority_tier": 3,
  "reliability": "high",
  "sha256": "...",
  "ingest_method": "pymupdf.text",
  "notes": "Some values later superseded."
}
```

`document_number`, `revision`, `status`, `issued_date` and `authority_tier` drive the entire precedence engine
(`05_evidence_precedence_spec.md`). They are extracted when the document states them and supplied by the case
manifest when it does not.

### 6.2 `SourceFragment`

The atomic unit of evidence. Every citation in the system points at a fragment id.

```jsonc
{
  "id": "frag:urs001#p1.s3.r4",
  "source_id": "src:urs_001",
  "locator": {"kind": "pdf", "page": 1, "block": 3, "bbox": [72, 431, 523, 449]},
  "text": "URS-F-003 - V1 shall close when Tank 1 reaches the specified high-level limit.",
  "modality": "text",
  "extraction_method": "pymupdf.text",
  "extraction_confidence": 1.0
}
```

`locator` is discriminated by `kind`, so a citation is reproducible and the UI can deep-link:

| `kind` | Fields | Applies to |
|---|---|---|
| `pdf` | `page`, `block`, `bbox` | PDF text |
| `pdf_image` | `page`, `bbox`, `render_dpi` | PDF pages with **no text layer** — rendered and read by vision |
| `spreadsheet` | `sheet`, `cell_range`, `header_row` | xlsx |
| `docx` | `paragraph_index`, `table`, `row`, `col` | Word |
| `text` | `line_start`, `line_end` | txt, md, mo, puml |
| `email` | `message_index`, `header`, `line_start` | eml — **per message in a thread** |
| `image` | `bbox`, `render_dpi` | png |
| `tabular` | `row_range`, `columns` | csv |
| `json_path` | `pointer` | json |

`pdf_image` is not hypothetical: the hackathon's own Participant Briefing PDF has **no text layer on any of its
13 pages**. Any ingester that assumes PDF means extractable text silently returns nothing for it. Our PDF loader
therefore always checks text yield per page and falls back to render-plus-vision. See `04_ingestion_spec.md` §4.1.

`email` fragments are **per message**, because a thread contains the superseded opinion *and* the approval that
overrides it. L1's thread holds Jin's "T1_high=0.78" **and** Samir's "CR-004 is now approved, treat 0.80 m as
effective" — collapsing the thread into one fragment destroys the precedence signal.

## 7. Conflicts, assumptions, open questions

Full semantics in `05_evidence_precedence_spec.md`; shapes here.

```jsonc
// Conflict
{
  "id": "conflict:t1_high",
  "subject": {"kind": "attribute", "id": "attr:tank_1.high_limit"},
  "positions": [
    {"value": "0.80 m", "authority_record": "CR-004", "tier": 1, "fragment_ids": ["..."], "date": "2026-03-11"},
    {"value": "0.78 m", "authority_record": "URS-001 Rev A", "tier": 3, "fragment_ids": ["..."], "date": "2026-01-15"}
  ],
  "resolution": "selected",         // selected | unresolved | user_resolved
  "selected_position": 0,
  "rule_applied": "PRE-01-tier-then-date",
  "rationale": "CR-004 is an approved change record (tier 1) dated after URS-001 Rev A (tier 3).",
  "severity": "info"                // info | warn | blocking
}

// Assumption
{
  "id": "assume:tank_1_outlet",
  "statement": "Tank TK-101 has a liquid outlet port.",
  "category": "standard_engineering",   // standard_engineering | library_default | inferred_from_topology
                                        // | unit_normalisation | numerical_necessity
  "standard_assumption_id": "SA-FLUID-002",
  "rationale": "No document states an outlet, but IF-HYD-03 requires flow from TK-101 to XV-102.",
  "affects": ["port:tank_1.outlet"],
  "confidence": 0.95,
  "reviewable": true
}

// OpenQuestion
{
  "id": "oq:b7_cooling_temp",
  "question": "What is the B7 concentrate cooling completion temperature?",
  "why_it_matters": "Determines the guard on the concentrate-branch join before cycle reset.",
  "blocking": false,
  "candidates": ["20 C (handwritten commissioning sheet)", "25 C (CR-017, approved)"],
  "default_taken": "25 C",
  "default_assumption_id": "assume:b7_temp",
  "gates": ["trans:cool_b7_to_join"]
}
```

An `OpenQuestion` with `blocking: true` **stops emission**. Non-blocking questions proceed under a stated
default, which must itself be a registered `Assumption` — this is precisely the PRD's *"inferred with a stated
assumption, or surfaced as a question"*, with the two paths kept distinct rather than blurred.

## 8. `TraceLink`

```jsonc
{
  "id": "trace:00412",
  "from": {"kind": "fragment", "id": "frag:urs001#p1.s3.r4"},
  "to":   {"kind": "state",    "id": "state:fill_t1"},
  "relation": "justifies",   // justifies | supersedes | contradicts | refines | verifies | implements
  "confidence": 0.91
}
```

Traces are **derived and rebuilt** from provenance on each run, never hand-maintained. They exist as an explicit
collection so the report generator and the UI graph view can query the relation in both directions without
walking every entity.

## 9. Validation contract

An SFIR document is **valid** only if all of the following hold. `09_validation_and_repair_spec.md` gives the
full rule catalogue with ids and severities.

| # | Invariant |
|---|---|
| 1 | Conforms to JSON Schema `sfir/1.0` |
| 2 | All id references resolve; no dangling ids |
| 3 | **Every entity satisfies the provenance invariant (§5.1)** |
| 4 | Every `Connection` joins two compatible ports (type, medium, causality) |
| 5 | Every physical port has `direction: "acausal"` |
| 6 | Every `Attribute` with a value has a `unit` **or** an explicit `dimensionless: true` |
| 7 | Units are dimensionally consistent within each `Constraint` expression |
| 8 | Every `Part` binds to a known `archetype` in the component library |
| 9 | Every `StateMachine` has a reachable initial state and no unreachable states |
| 10 | No `Conflict` with `severity: blocking` is unresolved |
| 11 | No `OpenQuestion` with `blocking: true` is unanswered |
| 12 | Collections are sorted by `id` and ids are deterministic (SF-ACC-05) |

## 10. Versioning and round-trip editing

- `sfir_version` is semver. Breaking field changes bump major; additive changes bump minor.
- Every pipeline run writes an immutable `model.sfir.json` under `runs/<run_id>/`.
- A user override (SF-EXT-06) is applied as a **JSON Patch** against the prior IR, recorded with
  `provenance.kind = "user_override"` and `authority_tier = 0` — **user input outranks every document tier**,
  because the engineer is the authority of last resort. The patch, its author and its timestamp are persisted
  (`13_data_model_spec.md`), so the traceability record survives editing rather than being invalidated by it.

## 11. Worked example — L1 fragment

Abridged, showing the interesting parts only. Full expected IR fixtures live in
`test/testdata/expected/L1_two_tank/`.

```jsonc
{
  "sfir_version": "1.0",
  "model": {"id": "model:two_tank", "name": "TwoTankController", "domain": "process_control",
            "case_id": "L1_two_tank"},
  "parts": [
    {"id": "part:tank_1", "name": "tank1", "tag": "TK-101", "archetype": "fluid.tank.vertical",
     "aliases": [{"text": "T1"}, {"text": "Tank 1"}],
     "provenance": {"kind": "evidence", "fragment_ids": ["frag:reg#Equipment_Schedule.A3"],
                    "authority_tier": 4, "confidence": 0.99}},
    {"id": "part:valve_2", "name": "valve2", "tag": "XV-102", "archetype": "fluid.valve.onoff",
     "provenance": {"kind": "evidence", "fragment_ids": ["frag:reg#Equipment_Schedule.A5"],
                    "authority_tier": 4, "confidence": 0.99}}
  ],
  "attributes": [
    {"id": "attr:ctrl.t1_high", "name": "T1_High", "value": 0.80, "unit": "m",
     "value_kind": "effective_setpoint", "conflict_id": "conflict:t1_high",
     "candidates": [
       {"value": 0.80, "authority": "CR-004", "tier": 1, "effective_date": "2026-03-11", "selected": true},
       {"value": 0.78, "authority": "URS-001 Rev A", "tier": 3, "status": "superseded", "selected": false},
       {"value": 0.78, "authority": "SIM-LEGACY 1.2", "tier": 11, "status": "archived", "selected": false}
     ],
     "provenance": {"kind": "evidence", "fragment_ids": ["frag:email#m1.l7"], "authority_record": "CR-004",
                    "authority_tier": 1, "confidence": 0.97}}
  ],
  "constraints": [
    {"id": "constraint:v2_v3", "kind": "interlock", "expression": "not (cmd_v2 and cmd_v3)",
     "scope": "global", "severity": "safety",
     "exceptions": [{"scope": "state:shutdown", "rationale": "DR-02 D-09 permits V2+V3 during controlled shutdown"}]}
  ],
  "open_questions": [],
  "conflicts": [{"id": "conflict:t1_high", "resolution": "selected", "selected_position": 0,
                 "rule_applied": "PRE-01-tier-then-date"}]
}
```

Note what the example demonstrates: the same value `0.78` appears **twice** as a losing candidate from two
different authorities (the original requirement and the stale legacy model), and both are retained with distinct
tiers and statuses. That is the shape of the problem the product exists to solve.
