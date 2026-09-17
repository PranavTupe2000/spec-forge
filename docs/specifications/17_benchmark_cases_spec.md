# 17 — Benchmark Cases: Overview

**Status:** Baseline · **Data:** `test/testdata/benchmarks/` · **Per-case detail:** `benchmarks/L1`–`L4`

---

## 1. What these cases are — and are not

Four reference problems, supplied as unit test cases. **They are a calibration set, not the product.**

> A submission that only solves the four supplied problems has built a demo. A submission that solves them
> because its architecture generalises has built a product. **The evaluation is weighted accordingly.**

They form a deliberate difficulty ladder where **each level adds one new class of reasoning rather than a new
subject area**:

| Level | Case | New reasoning skill | Bundle |
|---|---|---|---|
| **L1** | Two-Tank Controller | Sequencing, interlocks, state machines, safe start/stop. Structural basics, **no physics coupling** | `L1_two_tank/` |
| **L2** | Room CO2 Ventilation | **Closed-loop feedback**: disturbance → sensor → control law → actuator acting back on the process | `L2_room_co2/` |
| **L3** | Magnetic Circuit | **Multiphysics** energy transfer across domains, with an explicit loss path | `L3_magnetic_circuit/` |
| **L4** | Water/NaCl Evaporation Plant | **Integration**: supply, heating, transformation, separation into two streams, one coordinating controller | `L4_nacl_evaporation/` |

L4 is **not a new skill** — it is the composition of the previous three under competing constraints, which is
why it is the hardest.

> These problems are **proxies**, structurally faithful to far more complex industrial equipment. Valve
> sequencing in a two-tank rig is the same pattern as sequencing in a process gas delivery chain. A CO2 loop is
> the same pattern as chamber pressure control.
> **Do not optimise for tanks and brine. Optimise for the pattern.**

Operationally: nothing in `src/` may name a case (SF-SCP-01, `test_no_case_specific_logic.py`).

## 2. The shared bundle structure

All four use the same nine-folder layout — itself a realistic model of how engineering evidence actually arrives:

| Folder | Contents | Typical authority tier |
|---|---|---|
| `01_requirements/` | Released URS / SRS, Rev A | T3 |
| `02_engineering_data/` | Engineering register `.xlsx` — multi-sheet | T4 (+ T1–T3 metadata, §4) |
| `03_architecture_diagrams/` | Reference diagram `.png` + partial `.puml` draft | T8 |
| `04_design_notes/` | Design notes `.docx`, review minutes `.md`, engineer notes `.txt` | T2 / T3 / T10 |
| `05_correspondence/` | Email thread `.eml` | T9 — **but see the transmission rule** |
| `06_legacy_code/` | Legacy Modelica `.mo` | T11 |
| `07_datasheets/` | Vendor datasheet `.pdf` | T5 |
| `08_commissioning/` | Test/verification procedure | T6 |
| `09_datasets/` | Reference run `.csv`, schedules, BIM/geometry `.json` | T7 |

56 files, 11 formats. This is the concrete justification for the modality coverage in
`04_ingestion_spec.md` — every format in that spec is present in these bundles.

## 3. The shared trap structure

**Every case is built on the same five-part pattern.** Recognising this is what turns four demos into one
product.

| # | Trap | Generalises to |
|---:|---|---|
| 1 | A **released Rev A spec** states baseline values | Every controlled engineering document set |
| 2 | A **later approved change record** overrides some of them, transmitted by email | Change control in any organisation |
| 3 | A **legacy model/diagram** still carries the superseded values and says so in its own comments | Every codebase older than its requirements |
| 4 | **Informal notes** report observed values that agree with the *new* values, not the spec | Field reality vs documentation |
| 5 | **Aliases** — every component has 2–3 names across artifacts | Tag vs instance vs colloquial naming |

Plus, in every case, at least one **apparent contradiction that is not one** — two values that differ because
they describe *different kinds of thing*. Handling these correctly requires `value_kind`
(`03_system_ir_spec.md` §4.4) and the never-merge rule (`05_evidence_precedence_spec.md` §4.1).

## 4. The registers tell us what to build

The `02_engineering_data/*.xlsx` workbooks contain sheets that are **precedence metadata, not content**:

- **`Change_Log`** — `Date | Record | Revision | Status | Affected Item(s) | Change Summary | Approved By | **Precedence Note**`
- **`Source_Index`** — `Source ID | Filename | Type | Revision/Date | **Reliability** | Contains | **Known Caveat**`
- **`Operating_Parameters`** — `Parameter | Value | Source | **Revision Status** | **Effective?**`
- **`Requirements_Register`** — with `Status` and `Superseded By` columns
- **`Interface_Matrix`** — **port-level** connections: `From | From Port | To | To Port | Medium | Constraint`

The dataset authors built the precedence problem in explicitly, and labelled the answer. L1's `Change_Log`
literally annotates TP-17 as *"Verification input, not design authority"* and CR-004 as *"Latest approved
change; overrides older conflicts."*

Two consequences for implementation:

- These sheets route to `evidence/` rather than `extract/` (`04_ingestion_spec.md` §4.3).
- **The `Interface_Matrix` is the highest-quality topology evidence available** — the only source stating
  connections at port level. Prefer it over diagrams whenever present.

## 5. Per-case acceptance

Each case directory carries:

| File | Purpose |
|---|---|
| `manifest.yaml` | Per-file document metadata (number, revision, status, date, tier, reliability) + acceptance tolerances |
| `test/testdata/expected/<case>/elements.yaml` | Reference parts, ports, connections with accepted aliases — for coverage (SF-ACC-01) |
| `test/testdata/expected/<case>/conflicts.yaml` | Conflicts that **must** be found, and non-conflicts that must **not** be reported |
| `test/testdata/expected/<case>/parameters.yaml` | Effective values the precedence engine must select |

`manifest.yaml` is **test fixture metadata, not production input**. Every case must also pass with
`--no-manifest` (SF-SCP-02), which is how we keep ourselves honest about generalisation.

## 6. Priority and expectations

All four levels, equal effort (ADR-011). Realistic expectations per level, given that the compile gate is
binary and L3/L4 are substantially harder:

| Level | Target | Acceptable outcome |
|---|---|---|
| L1 | Full pipeline, compiles, simulates, matches the 900 s reference trace | Nothing less |
| L2 | Full pipeline, compiles, simulates, matches the 24 h trend | Nothing less |
| L3 | Compiles; analytic verification against AV-11 values | Compiles with stated gaps in phasor handling |
| L4 | Compiles; sequence runs past 2500 s | Compiles with StandardWater baseline; WaterNaCl stated as an open gap |

The L4 row is not a hedge — it is what the source documents themselves prescribe. The URS states that
StandardWater *"may be used as an integration baseline to verify topology and sequence behavior before enabling
composition-dependent property functions"*, and the lab notebook records that WaterNaCl still fails at pump
start. Reproducing that honestly, and saying so, is the correct result. Claiming a working WaterNaCl model
would be the *"superficially complete and quietly wrong"* outcome the PRD ranks lowest.
