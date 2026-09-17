# L1 — Two-Tank Sequence Controller

**Reasoning under test:** sequencing, interlocks, state machines, safe start and stop. Structural basics, **no
physics coupling.**
**Bundle:** `test/testdata/benchmarks/L1_two_tank/` · 12 files

---

## 1. The system

A demonstration liquid-transfer process: two tanks, three actuated isolation valves, two level transmitters,
three operator pushbuttons, one sequence controller.

```
SRC-101 ──▶ XV-101 ──▶ TK-101 ──▶ XV-102 ──▶ TK-102 ──▶ XV-103 ──▶ DRN-101
            (V1)       (T1)       (V2)       (T2)       (V3)       (drain)
                        │ LT-101              │ LT-102
                        ▼                     ▼
                  ┌───────────────────────────────┐
                  │  PLC-101 (tankController)     │ ◀── START / STOP / SHUT
                  └───────────────────────────────┘
```

## 2. Expected model elements

**Parts (8 + controller):** `TK-101` tank1 · `TK-102` tank2 · `XV-101` valve1 · `XV-102` valve2 · `XV-103`
valve3 · `LT-101` level1 · `LT-102` level2 · `SRC-101` source · `DRN-101` ambient1/drain · `PLC-101`
tankController.

**Connections:** six hydraulic (`IF-HYD-01`…`06`), plus control signals — LT-101/LT-102 → PLC inputs, PLC →
three valve commands, three pushbuttons → PLC inputs.

**Critical:** the reference `.puml` shows **only** the six hydraulic edges and the three valve commands. It
omits LT-101/LT-102, the START/STOP/SHUT inputs, the pause state and shutdown concurrency — **and says so in its
own note**. A pipeline that trusts the diagram produces a controller with no feedback. The note is citable
evidence of known incompleteness and should generate open questions, which the `Interface_Matrix` and the URS
then answer.

## 3. The state machine

Nine states, from `04_control_logic_design_notes.docx` (CDS-02 Rev B):

| State | (V1,V2,V3) | Exit |
|---|---|---|
| `IDLE` | 0,0,0 | START edge → `FILL_T1` |
| `FILL_T1` | **1,0,0** | `LT-101 >= T1_High` |
| `WAIT_AFTER_FILL` | 0,0,0 | post-fill wait elapsed |
| `TRANSFER_T1_T2` | **0,1,0** | `LT-101 <= T1_Low` |
| `WAIT_AFTER_TRANSFER` | 0,0,0 | post-transfer wait elapsed |
| `DRAIN_T2` | **0,0,1** | `LT-102 <= T2_Low` |
| `WAIT_AFTER_DRAIN` | 0,0,0 | inter-cycle wait → `FILL_T1` (cyclic) |
| `PAUSED` | 0,0,0 | START → restore stored state |
| `SHUTDOWN` | **0,1,1** | both tanks at/below low → all closed → `IDLE` |

### 3.1 Semantics that must survive into Modelica

| Rule | Source | Failure if lost |
|---|---|---|
| **Priority `SHUT > STOP > START`** | DR-02 D-01 | Simultaneous commands resolve wrongly |
| STOP closes all valves and **stores the interrupted state** | D-02 | Resume restarts the cycle from FILL |
| STOP during a delay **freezes the remaining delay**; START resumes it | D-03 (restart explicitly **rejected**) | Operator pause duration alters process timing |
| START while already running is **ignored** | D-04 | Spurious restarts |
| START/STOP during active SHUT are **ignored** | D-05 | Shutdown interruptible — unsafe |
| SHUT completes only when **both** LT-101 and LT-102 are at/below low | D-06 | Premature completion |
| After shutdown: all valves closed, context reset to IDLE; later START begins a **new fill cycle** | D-07 | Resumes mid-cycle after a drain |

Implementation: `08_modelica_emission_spec.md` §4.1 (`elsewhen` ordering, `resumeState`, `waitRemaining`).

### 3.2 Interlocks — including the exception

- `V1` and `V2` **never** open together (D-08) — unconditional.
- `V2` and `V3` **not** together in normal automatic operation (D-09) — **waived in `SHUTDOWN`**, where both are
  commanded open by design.

The waiver is confirmed three ways: DR-02 D-09, URS-M-003, and the test engineer's note — *"Shut at 700:
transfer + drain lamps are on together. This is intentional for SHUT, not an interlock failure."* Expressing it
as an unconditional prohibition contradicts the approved design; omitting the interlock fails SF-ACC-04.
See `03_system_ir_spec.md` §4.6 for the `exceptions[]` mechanism.

## 4. Parameters and the precedence problem

| Parameter | URS-001 Rev A | Legacy `.mo` | **Effective** | Authority |
|---|---|---|---|---|
| T1 high limit | 0.78 m | 0.78 m | **0.80 m** | CR-004, approved 2026-03-11 |
| T1 low limit | 0.05 m | 0.05 m | 0.05 m | URS Rev A |
| T2 low limit | 0.05 m | 0.05 m | 0.05 m | URS Rev A |
| Wait after T1 high | 10 s | 10 s | 10 s | URS Rev A |
| **Wait after T1 low** | 10 s | 10 s | **12 s** | CR-004 |
| **Wait after T2 low** | 10 s | 10 s | **8 s** | CR-004 |
| Tank areas | — | 1.20 / 1.40 m² | 1.20 / 1.40 m² | MDS-01 |
| Flows (fill/transfer/drain) | — | 0.0060 / 0.0045 / 0.0050 m³/s | same | MDS-01, Equipment_Schedule |

**Three of these values are wrong in two documents and right in one.** The email thread carries the resolution
explicitly: *"CR-004 is now approved. Please treat 0.80 m as the effective T1 high limit... Jin - the archived
Modelica demo still says 0.78 / 10 / 10. Please do not use those three values as configuration authority."*

The `Operating_Parameters` sheet independently confirms it with `Revision Status` and `Effective?` columns:
`0.78 | URS-001 Rev A | Superseded | No` against `0.80 | CR-004 | Approved | Yes`.

**This is the case's primary test.** Any of three plausible-looking failures produces a wrong model: trusting
the released spec (0.78), trusting the legacy code (0.78), or treating email as low-authority and discarding it
(0.78). Only the transmission rule (`05_evidence_precedence_spec.md` §3) gets 0.80.

## 5. Aliases

| Tag | Aliases |
|---|---|
| TK-101 | tank1, T1, Tank 1 |
| TK-102 | tank2, T2, Tank 2 |
| XV-101 | valve1, V1 |
| XV-102 | valve2, V2 |
| XV-103 | valve3, V3 |
| PLC-101 | tankController |
| LT-101 / LT-102 | level1 / level2 |

Seeded deterministically from `Equipment_Schedule.Alias` and the "Terminology reminders" block in the shift
notes — no inference required (`04_ingestion_spec.md` §7 step 2).

## 6. Reference behaviour

`09_datasets/10_demo_run_900s.csv` — 900 s at 1 Hz. Columns: `time_s, cmd_start, cmd_stop, cmd_shut,
tank1_level_m, tank2_level_m, valve1_open, valve2_open, valve3_open, controller_state, wait_remaining_s`.

Command schedule: **START 20 s · STOP 220 s · START 280 s · STOP 650 s · SHUT 700 s.**

Observed behaviour the model must reproduce (from the shift notes, which read as an independent verification of
the precedence outcome):

- V1 drops out at **0.80**, *"not the 0.78 number in Jin's old model"*.
- STOP at 220 closes all valves; **levels hold steady** through the pause.
- START at 280 **resumes transfer — it does NOT go back to fill**.
- After T1 low, a **noticeably longer dead time than the first wait** — 12 s.
- After T2 low, next fill in **~8 s**.
- SHUT at 700: transfer **and** drain open together; completes quickly because little inventory remained;
  system stays idle to 900 s.

The trace independently confirms the correct effective values, which makes it a strong end-to-end check:
if the model fills to 0.78 or waits 10 s, the deviation table catches it.

`controller_state` is a **string** column of state names — usable for direct state-sequence comparison, not just
numeric deviation.

## 7. Traps

| # | Trap | Wrong outcome | Defence |
|---|---|---|---|
| 1 | CR-004 supersedes three values, transmitted by email | 0.78 / 10 / 10 | Transmission rule, T1 |
| 2 | Legacy `.mo` looks authoritative — it is real, runnable code | Stale parameters | T11, `role=parameter` demotion |
| 3 | V2+V3 interlock has a scoped exception | Asserts during correct shutdown, or no interlock at all | `Constraint.exceptions[]` |
| 4 | `shut` means **controlled drain, not E-stop** | Modelled as power loss / emergency stop | DR-02 modelling note + shift notes, both explicit |
| 5 | Legacy `.mo` **omits** SHUT logic and says so in a comment | Treated as complete reference | `role=structure` vs `role=parameter` split |
| 6 | `.puml` omits sensors, commands, pause, shutdown | Controller with no feedback | Note parsed as known-incompleteness evidence |
| 7 | Timer freeze vs restart | Restart on resume | `timers[].on_suspend: freeze_remaining` |
| 8 | Valve stroke time 0.8 s in the datasheet | Modelled as dynamics, or ignored silently | Out of scope — state it in "does NOT cover" |

## 8. Acceptance

| Check | Target |
|---|---|
| Structural coverage | ≥80% of the reference element set |
| Effective parameters | 0.80 m, 12 s, 8 s selected — **and** losing candidates retained |
| Conflicts reported | T1 high (3 positions), post-transfer wait, inter-cycle wait |
| State machine | 9 states, all reachable; priority order correct |
| Interlocks | V1/V2 unconditional; V2/V3 with SHUTDOWN exception |
| Compile | `omc checkModel` green |
| Simulate | 900 s; levels within tolerance; state transitions within 1 s of reference at all five events |

Expected fixtures: `test/testdata/expected/L1_two_tank/`.

## 9. Sources

| File | Doc | Rev | Status | Tier |
|---|---|---|---|---|
| `01_customer_URS.pdf` | URS-001 | A | Released | 3 |
| `02_engineering_data_register.xlsx` | — | 2026-04-10 | Compiled | 4 |
| `03_reference_control_diagram.png` | — | — | Reference | 8 |
| `11_partial_legacy_architecture.puml` | — | — | Draft, incomplete | 8 |
| `04_control_logic_design_notes.docx` | CDS-02 | B | Released after DR-02 | 3 |
| `06_design_review_minutes.md` | DR-02 | Final | Approved | 2 |
| `12_operator_shift_notes.txt` | — | 2026-04-04 | Uncontrolled | 10 |
| `05_controls_email_thread.eml` | — | 2026-02-16…03-12 | Informal — **carries CR-004** | 9 → **1** |
| `07_legacy_tank_demo.mo` | SIM-LEGACY | 1.2 | Archived, pre-CR-004 | 11 |
| `08_valve_datasheet.pdf` | VD-101 | B | Released | 5 |
| `09_test_procedure_TP17.pdf` | TP-17 | C | Released — *verification input, not design authority* | 6 |
| `10_demo_run_900s.csv` | — | — | Reference trace | 7 |
