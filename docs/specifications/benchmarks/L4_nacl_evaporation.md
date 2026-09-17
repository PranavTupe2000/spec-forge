# L4 — Water / NaCl Evaporation Plant

**Reasoning under test:** integration — material supply, heating, transformation, separation into two streams,
coordinated under one controller.
**Bundle:** `test/testdata/benchmarks/L4_nacl_evaporation/` · 14 files

> L4 is **not a new skill**. It is the composition of L1 (sequencing), L2 (feedback) and L3 (multi-domain
> physics) **under competing constraints**, which is why it is the hardest.

---

## 1. The system

A laboratory plant concentrating a water/NaCl batch through staged charging, mixing, buffering, evaporation,
condensation, cooling and return pumping.

| Vessel | Role |
|---|---|
| **B1** | Water charge vessel |
| **B2** | Concentrated brine charge vessel |
| **B3** | Batch preparation / mixing |
| **B4** | Buffer |
| **B5** | Evaporator (heated) |
| **K1** | Condenser |
| **B6** | Condensate cooling |
| **B7** | Concentrate cooling |
| **P1 / P2** | Return pumps |

```
B1 ─V8─┐                         ┌── K1 ──▶ B6 ──[cool]──▶ P2? ──▶ B1   (condensate, branch A)
       ├──▶ B3 ──V11──▶ B4 ──V12──▶ B5 ──┤
B2 ─V9─┘                         └──V15──▶ B7 ──[cool]──▶ P1? ──▶ B2   (concentrate, branch B)
```

## 2. Sequence

From the URS phase table and `04_control_sequence_design.docx` Rev B. A **StateGraph-style sequential function
chart** with a **parallel split and join**.

| Step | Action | Guard | Region |
|---|---|---|---|
| Initial | All automated valves closed; pumps/heaters/coolers off | `startEnable AND B3 available` | single |
| Step1 | `V8 = OPEN` (B1→B3, water) | `LIS-301 >= 0.13 m` | single |
| Step2 | `V9 = OPEN` (B2→B3, brine + mix) | `QI-302 >= 0.080 kg/kg` | single |
| Step3 | `V11 = OPEN` (B3→B4, buffer) | `LIS-301 < 0.01 m` | single |
| Step4 | `V12 = OPEN` (B4→B5) when B5 idle | `LIS-501` reaches batch level | single |
| Step5 | `B5 heater = ON` | `QIS-502` reaches evaporation target | single |
| Step6 | — | completion **splits into two branches** | split |
| Step7 | (no transfer actuator) | `LIS-701 < 0.01 m` | **Parallel A** |
| Step8 | `V15 = OPEN` (B5→B7) | `LIS-501 < 0.01 m` | **Parallel B** |
| Step9 | `B7_Cooler = ON` | `TIS-702 <= 25 degC` | **Parallel B** |
| Step10/11 | `P1 = ON` + corrected return valve group | B7 return complete | **Parallel B** |
| Join | — | **A complete AND B complete AND time > 2500 s** | join |

### 2.1 Why this forces `state_graph` emission

Two concurrent regions cannot be encoded in a single-region `Integer state` machine. The Modelica emitter
selects `Modelica.StateGraph` because `len(regions) > 1` — a **structural property of the IR**, never a case
name (`08_modelica_emission_spec.md` §4, SF-SCP-01). L1 takes the algorithmic path by the same rule.

The join guard also carries a **time condition** (`> 2500 s`) alongside the branch completions, and the URS
requires the acceptance simulation to *"continue beyond 2500 s to demonstrate cycle reset."*

## 3. Interlocks and permissives

| Element | Condition |
|---|---|
| B5 heater permissive | `LIS-501 >= 0.05 m` **AND** `FIS-801 >= 0.10 kg/s` |
| P1 permissive | `LIS-701 > 0.02 m` (dry-run inhibit) |
| P2 permissive | `LIS-601 > 0.02 m` (dry-run inhibit) |
| P1 alarm | `PIS-901 < 0.8 bar(g)` while running |
| P2 alarm | `PIS-1001 < 0.8 bar(g)` while running |
| Automated valves | Discrete, **fail closed**, not modulating |

DR-07 decision 3 states the dry-run inhibits; decision 4 the fail-closed discrete behaviour. These are
`Constraint` entities of kind `permissive`, and `V-BEH-004` checks them across reachable states.

## 4. The routing correction — this case's primary precedence test

| Branch | Archived StateGraph | **CR-017 (approved 2026-03-05)** |
|---|---|---|
| B6 condensate | → B2 (via P2 valve group) | **→ B1** |
| B7 concentrate | → B1 (via P1 valve group) | **→ B2** |
| B7 cooling completion | 20 °C (handwritten sheet) | **≤ 25 °C** |

The design note states the trap directly: *"The archived StateGraph extract paired the B7/P1 branch with the B1
valve group and the B6/P2 branch with the B2 valve group. CR-017 subsequently corrected the destination
semantics... Controller valve-group assignments **shall follow CR-017**."*

The email explains **why** the legacy routing looks plausible and is still wrong: *"That is what the teaching
model did, but it does not preserve the stream identities stated in the URS."* And Marco adds the reason the
mistake is easy to make: ***"The bottom headers are cross-connected, so pump physical location is not the
destination."***

That last sentence is the whole difficulty in one line. Topology alone cannot tell you where a stream ends up,
because the headers are cross-connected — **stream identity is a semantic property stated in the requirements,
not a graph property derivable from the P&ID.** A pipeline that infers routing from connectivity gets it
backwards and produces a model that compiles, simulates, and returns brine to the water vessel.

Note also the proposal/approval split: Marco writes *"I will raise CR-017"* on 3 Mar — a **proposal**, tier 9.
The approval arrives 5 Mar from a different author — **tier 1**. Only the latter transmits authority
(`05_evidence_precedence_spec.md` §3).

## 5. Configurations, not conflicts

### 5.1 Medium

| Configuration | Role |
|---|---|
| `StandardWater` | *"A topology/control integration baseline ... to verify topology and sequence behavior before enabling composition-dependent property functions"* (URS §3, DR-07 decision 7) |
| `WaterNaCl` | The **intended physical medium** |

**Not a conflict** — two configurations, per `05_evidence_precedence_spec.md` §4.1. The lab notebook records the
real state of affairs: *"StandardWater topology runs all the way past 2500 s. WaterNaCl still gets ugly when a
pump transition becomes active."* Open action A-19 is still open.

**Correct behaviour:** deliver the StandardWater configuration as the compiling, simulating baseline; record
WaterNaCl as the intended variant with the convergence issue as a stated open gap. This is the *"partially
complete and honest"* outcome the PRD ranks above superficial completeness — and claiming a working WaterNaCl
model would be exactly the failure it ranks lowest.

### 5.2 K1 — physical vs simulation abstraction

DR-07 decision 5: *"K1 remains a physical condenser even if the legacy Modelica component combines evaporator
and condenser equations."* The URS permits the combined component *"provided the physical condenser K1 remains
identifiable in the system architecture."*

→ **K1 is a `Part` in the SysML architecture** with its own identity, while the Modelica emission may bind it
into a combined evaporator/condenser component. This is a clean demonstration of why one IR with two emitters is
the right architecture: the same element projects differently into a structural view and an executable view
without either being wrong.

## 6. Modelling constraints stated by the documents

| Constraint | Source | Rule |
|---|---|---|
| Junction volumes **mandatory** where closed-valve combinations could leave pressure/enthalpy/composition undefined | URS §4, DR-07 decision 6 | `SA-NUM-001`, `V-MOD-007` |
| All **non-horizontal pipes** include static head in pressure drop | URS §4 | archetype parameter |
| Tank connections may pass **above or below** the liquid level | URS §4 | port elevation attribute |
| Regularised **asymmetric loss factor with hysteresis** around port elevation | URS §4 | `V-MOD-009` |
| Manual/isolation valves on the P&ID are **excluded** from the StateGraph actuator bundle unless the ICD says otherwise | Design note §1 | see §7 |

The lab notebook confirms these are real, not theoretical: *"Tiny solver steps around port-level crossing
disappeared with hysteresis"* and *"Q_up fix stopped B5 boil/no-boil switching."* The library encodes what the
documents already learned.

## 7. Controller ownership — which valves are the controller's?

*"The P&ID includes both controller-operated and manual/local valves."* The lab notebook raises it as an open
action: ***"P&ID shows more valves than the StateGraph. Determine ownership before generating controller
ports."***

A pipeline that generates a controller port per P&ID valve produces a controller with actuators it does not own.
Ownership is determined by the ICD and the StateGraph actuator bundle, **not** by the drawing. Where it cannot be
determined, it becomes an `OpenQuestion` — this is a case where "ask" is the correct branch of the degradation
ladder (ADR-007).

## 8. Interfaces

The controller uses a **single `sensors` connector bundle** and a **single `actuators` connector bundle**;
plant-level equations assign individual instrument values in and actuator commands out:

```
controller.sensors.LIS_301 = B3.level;
controller.sensors.QIS_502 = B5.medium.Xi[NaCl];
V9.open = controller.actuators.V9;
HeatB5.Q_flow = if controller.actuators.T5_Heater then 20000 else 0;
```

Bundled connectors are a structural pattern in their own right, and one the archetype library must support
(`control.statemachine.sequential` with bundle ports) rather than flattening into individual signals.

## 9. Reference behaviour

`09_datasets/10_batch_run_3000s.csv` — full cycle, **3000 s** (beyond the 2500 s reset threshold).
`12_layout_coordinates.json` — spatial layout, usable by the 3D view (`11_web_application_spec.md` §6.1).

## 10. Traps

| # | Trap | Wrong outcome | Defence |
|---|---|---|---|
| 1 | Return routing reversed by CR-017 | Condensate to B2, concentrate to B1 — compiles and simulates | Tier 1; stream identity is semantic, not topological |
| 2 | Cross-connected headers | Routing inferred from connectivity | Explicit URS stream identity |
| 3 | CR-017 proposed 3 Mar, approved 5 Mar | Proposal treated as authority | `record_status: proposed` |
| 4 | B7 cooling 20 vs **25 °C** | Handwritten sheet wins | Tier 10 vs tier 1 |
| 5 | StandardWater vs WaterNaCl | Reported as a conflict, or WaterNaCl claimed working | Two configurations; honest gap |
| 6 | K1 combined in legacy Modelica | K1 disappears from the architecture | DR-07 decision 5; IR keeps identity |
| 7 | Parallel split/join | Flattened to one region | `regions` → `state_graph` strategy |
| 8 | Junction volumes mandatory | Undefined states, solver failure | `SA-NUM-001`, `V-MOD-007` |
| 9 | P&ID has more valves than the controller owns | Phantom controller actuators | Ownership question |
| 10 | Join needs `time > 2500 s` **and** both branches | Cycle reset never demonstrated | Composite guard |
| 11 | Pump states removed to fix convergence | *"Do NOT delete pump states"* — lab notebook | Explicit prohibition in evidence |

Trap 11 is a good example of evidence that reads as an instruction to the modeller: the notebook anticipates the
obvious shortcut and forbids it. An extraction pass that only looks for parameters will miss it.

## 11. Acceptance

| Check | Target |
|---|---|
| Structural coverage | ≥80% — all nine vessels, K1 identifiable, both pumps |
| Routing | B6 → B1, B7 → B2 per CR-017 |
| B7 cooling | ≤ 25 °C |
| Sequence | Steps 1–11 with parallel split after Step6 and a join |
| Join guard | Both branches complete **AND** `time > 2500 s` |
| Interlocks | Heater permissive, both pump dry-run inhibits |
| Conflicts | Routing, B7 temperature |
| Non-conflicts | StandardWater vs WaterNaCl **not** reported as a conflict |
| Compile | `omc checkModel` green — **StandardWater configuration** |
| Simulate | Full cycle past 2500 s, cycle reset demonstrated |
| Honesty | WaterNaCl convergence recorded as an open gap in the summary |

## 12. Sources

| File | Doc | Rev | Status | Tier |
|---|---|---|---|---|
| `01_process_requirement_specification.pdf` | URS | A | Released | 3 |
| `02_process_data_register.xlsx` | — | — | Compiled | 4 |
| `03_reference_PID.png` | — | — | Reference P&ID | 8 |
| `11_legacy_architecture.puml` | — | — | Legacy draft | 8 |
| `04_control_sequence_design.docx` | — | B | Released | 3 |
| `06_design_review_minutes.md` | DR-07 | Final | Approved 2026-02-21 | 2 |
| `13_water_nacl_medium_notes.pdf` | — | — | Medium note | 5 |
| `15_lab_notebook.txt` | — | 2026-04-01 | Uncontrolled | 10 |
| `05_process_controls_email_thread.eml` | — | Mar 2026 | Informal — **carries CR-017** | 9 → **1** |
| `07_legacy_evaporation_plant.mo` | — | — | Archived, superseded routing | 11 |
| `08_valve_pump_datasheet.pdf` | — | — | Released | 5 |
| `09_batch_acceptance_test.pdf` | — | — | Verification input | 6 |
| `14_operator_runbook.docx` | — | — | Operations | 6 |
| `10_batch_run_3000s.csv` | — | — | Reference trace | 7 |
| `12_layout_coordinates.json` | — | — | Layout | 7 |
