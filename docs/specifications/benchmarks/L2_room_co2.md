# L2 — Room CO2 Ventilation Controller (RM-201)

**Reasoning under test:** closed-loop feedback — disturbance, sensor, control law, actuator acting back on the
process.
**Bundle:** `test/testdata/benchmarks/L2_room_co2/` · 14 files

---

## 1. The system

A single-zone demand-controlled outdoor-air demonstration. One well-mixed 100 m³ room; outdoor air through a
controlled supply path; exhaust to an ideal pressure boundary; occupants as a CO2 mass source on a schedule; a
CO2 sensor closing the loop onto fresh-air flow.

```
                      ┌──── occupancy schedule (nPeo) ────┐
                      ▼                                    │
  SRC-OA-201 ──▶ DUCT-IN ──▶ ZON-201 (100 m³) ──▶ DUCT-OUT ──▶ BND-201
  (freshAir)                  ▲     │                            (boundary4)
        ▲                     │     ▼
        │              SRC-CO2-201  SEN-CO2-201 (traceVolume)
        │              (peopleSource)     │  kg/kg
        │                                 ▼
        │                        GAIN-NORM-201 (×1/1.519e-3)
        │                                 │ normalised
        └──── ACH → kg/s ◀── P controller ◀┴── CO2Set = 1.0
```

## 2. Expected model elements

`ZON-201` volume · `SRC-OA-201` freshAir · `BND-201` boundary4 · `SRC-CO2-201` peopleSource ·
`SCH-OCC-201` NumberOfPeople · `SEN-CO2-201` traceVolume · `GAIN-NORM-201` gainSensor · P controller ·
limiter (0.2–6.0 ACH) · ACH→mass-flow gain · supply duct · exhaust duct.

Connections from the `Interface_Matrix`: `IF-AIR-01`…`04` (air path), `IF-TRC-01` (trace injection),
`IF-SIG-*` (signal chain).

## 3. The control law

Fully specified in `04_control_sequence_and_modeling_notes.docx` (CDS-IAQ-02 / MOD-NT-03 Rev B):

1. Measure room CO2 mass fraction at `traceVolume` — **kg/kg**.
2. Normalise: `gainSensor = 1 / 1.519e-3 = 658.327847`.
3. Compare with `CO2Set = 1.0` — **normalised**, not 1 ppm and not 1 kg/kg.
4. P law: `ACH = bias + Kp * (C/C_nom - 1)`, integral **disabled** in the reference run.
5. Limit to `[0.2, 6.0]` ACH.
6. Convert: `m = ACH * V * rho / 3600 = ACH * 100 * 1.2 / 3600 = ACH * 0.033333 kg/s`.
7. **Apply a negative sign** to the Modelica source command — negative source `m_flow` denotes flow *from* the
   source *into* the duct.

### 3.1 Modes

| Mode | Entry | Output |
|---|---|---|
| `AUTO_MIN` | CO2 well below setpoint | 0.2 ACH (lower limit) |
| `AUTO_CO2` | 0.2 < requested < 6.0 | `bias + Kp*(C/C_nom - 1)` |
| `AUTO_MAX` | requested ≥ 6.0 | 6.0 ACH — not expected in baseline |
| `SENSOR_FAULT` | sensor invalid > 60 s | 4.0 ACH + fault indication — **outside the baseline trend run** |

`SENSOR_FAULT` is a stated requirement (DR-IAQ-05 decision 8) that is explicitly **not exercised** in the
reference run. It belongs in the model and in the requirements trace; it must not be expected in the trace
comparison. Getting this right is a small but real test of reading the documents rather than the data.

## 4. The unit chain — this case's core difficulty

Four representations of the same physical quantity coexist, **all correct in their own context**:

| Representation | Value at the limit | Where |
|---|---|---|
| ppm (owner requirement) | 1000 ppm | URS-IAQ-004 |
| kg/kg mass fraction | 1.519e-3 kg/kg | project MW convention |
| normalised controller signal | 1.0 | `CO2Set`, after `gainSensor` |
| outdoor reference | 300 ppm = 0.3 × 1.519e-3 = **4.557e-4 kg/kg** | DR-IAQ-05 decision 2 |

**Every conversion must be an explicit part with a stated factor** (`V-UNIT-004`). A pipeline that silently
unifies these is wrong by a factor of 658 and will still compile. The legacy `.puml` makes the trap concrete:
its note records that the draft *"assumes sensor output is ppm"*, while ICD-IAQ-03 later **froze the internal
feedback interface in kg/kg and added the normalisation gain**.

## 5. Parameters and precedence

| Parameter | Legacy / early | **Effective** | Authority |
|---|---|---|---|
| CO2 limit interpretation | "1000 ppm above outdoor" ≈ 1300 total (email, 10 Feb) | **1000 ppm absolute** | DR-IAQ-05 decision 1 — *"The 1300 ppm interpretation is rejected for this benchmark"* |
| Outdoor CO2 | 300 ppm | 300 ppm | URS-IAQ-005 |
| `Kp` | 4 (legacy `.mo`) | **6.0** | CR-IAQ-007 |
| bias | — | **3.5 ACH** | CR-IAQ-007 |
| ACH limits | — | **0.2 … 6.0** | CR-IAQ-007 |
| Integral | — | **disabled** in reference run | CR-IAQ-007 |
| Peak occupancy | 12 (URS-IAQ-008 "at least 12"; legacy `.mo` peaks at 12) | **15**, 13:00–15:00 | OCC-SCH-04 Rev C |
| Room volume | 100 m³ | 100 m³ | URS-IAQ-001 |
| Air density | 1.2 kg/m³ | 1.2 kg/m³ | IAQ-PER-002 |
| Per-person CO2 | 8.18e-6 kg/s | 8.18e-6 kg/s | URS-IAQ-007 |

### 5.1 The rejected-position rule

The 10 Feb email contains a genuine engineering opinion — *"My first read was 1000 ppm above ambient (so around
1300 ppm total)"* — that was subsequently **rejected by name**. Under `05_evidence_precedence_spec.md` §3, a
record cited as rejected transmits nothing, and the claim is dropped at step 1 of `PRE-01` while remaining
visible in the ledger.

This is a different mechanism from ordinary tier precedence, and L2 is the case that tests it. A system that
merely ranks tiers would still surface 1300 ppm as a losing candidate; a system that reads `record_status` drops
it as rejected and says so.

## 6. Implementation artefacts that are not physical

Two traps of the `value_kind` class. Both are **correct** and must not be "fixed".

### 6.1 `peopleSource.C = 100 kg/kg`

Physically absurd — and intentional. Adding 8.18e-6 kg/s of CO2 directly as a carrier-fluid source would also
add carrier mass to the room's mass and energy balance. The model therefore uses a high trace concentration with
a proportionally reduced carrier flow:

```
m_peopleSource = (8.18e-6 / 100) * nPeo   kg/s      with   C_source = 100 kg/kg
⇒ trace injection = m * C = nPeo * 8.18e-6 kg/s      ✓
```

DR-IAQ-05 decision 7: *"`C_source=100 kg/kg` is a numerical implementation parameter and **shall not be shown as
a realistic room or outdoor gas composition**."* → `value_kind: numerical_device`, with a mandatory comment in
the emitted Modelica (`08_modelica_emission_spec.md` §3).

### 6.2 Negative `m_flow` for inflow

The Modelica source component takes **negative** `m_flow` for flow **into** the zone — a port sign convention.
URS-IAQ-011 requires the model to *"distinguish physical outdoor-air flow direction from any
implementation-specific source sign convention"*, and the field notes warn: *"Don't mix up `freshAir.m_flow` sign
with physical air into room."*

→ `V-PHYS-005`. Physical ventilation is reported as a **positive** quantity; the sign convention is declared, not
propagated into a requirement. A model that reports negative physical ventilation has failed this case.

## 7. Aliases

`ZON-201` = volume · `SRC-OA-201` = freshAir · `BND-201` = boundary4 · `SRC-CO2-201` = peopleSource ·
`SCH-OCC-201` = NumberOfPeople · `SEN-CO2-201` = traceVolume · `GAIN-NORM-201` = gainSensor.

Every tag has a Modelica instance name as its alias — seeded from `Component_Schedule.Alias / Legacy Name`.

## 8. Reference behaviour

`09_datasets/11_reference_run_24h.csv` — 24 h trend. Also `10_occupancy_schedule.csv` (piecewise-constant
weekday schedule, peak 15 at 13:00–15:00) and `12_bim_room_export.json` (room geometry).

Field-note expectations: trend maximum **≈996.52 ppm at ~14:59** — i.e. compliant with the 1000 ppm absolute
limit, but only just. Controller bottoms at **0.2 ACH** during long unoccupied periods.

The 996.52 figure is an **observed fact** (tier 7), not a requirement. A system that turns it into a setpoint has
misread the document class — the compliance criterion is 1000 ppm from URS-IAQ-004.

## 9. Traps

| # | Trap | Wrong outcome | Defence |
|---|---|---|---|
| 1 | Four unit representations of one quantity | Factor-of-658 error that still compiles | `V-UNIT-004`, explicit gain parts |
| 2 | "1000 ppm above outdoor" opinion, later rejected by name | Setpoint at 1300 ppm | `record_status: rejected` |
| 3 | `C_source = 100 kg/kg` | "Corrected" to a realistic value, or reported as a concentration | `value_kind: numerical_device` |
| 4 | Negative `m_flow` for inflow | Negative physical ventilation requirement | `V-PHYS-005` |
| 5 | Legacy `.mo`: Kp=4, peak 12 | Stale tuning | CR-IAQ-007, tier 1 |
| 6 | URS says "at least 12 persons"; schedule says 15 | Sized for 12 | `OCC-SCH-04 Rev C` — a *later approved* schedule, not a contradiction of "at least" |
| 7 | `.puml` assumes sensor in ppm | Missing normalisation gain | Note parsed; ICD-IAQ-03 overrides |
| 8 | `SENSOR_FAULT` required but not in the baseline trend | Expected in trace comparison, or omitted from the model | Model it; exclude from comparison |
| 9 | Observed 996.52 ppm | Treated as the requirement | Tier 7 = fact, not intent |

Trap 6 is worth care: *"at least 12"* and *"peak 15"* are **not** contradictory — a lower bound and an actual
schedule. Reporting this as a conflict would be a false positive, and the expected-conflicts fixture asserts it
is not reported.

## 10. Acceptance

| Check | Target |
|---|---|
| Structural coverage | ≥80% |
| Unit chain | All four representations present, every conversion explicit |
| Effective parameters | Kp=6.0, bias=3.5, limits 0.2–6.0, integral off, peak 15 |
| Conflicts | CO2 interpretation (rejected position retained), Kp, peak occupancy |
| Non-conflicts | "at least 12" vs 15 **not** reported as a conflict |
| `value_kind` | `C_source` marked `numerical_device`; sign convention declared |
| Compile | `omc checkModel` green |
| Simulate | 24 h; peak CO2 within tolerance of ~996.5 ppm; never exceeds 1000 ppm |

## 11. Sources

| File | Doc | Rev | Status | Tier |
|---|---|---|---|---|
| `01_owner_iaq_requirements.pdf` | URS-IAQ-001 | A | Released | 3 |
| `02_iaq_engineering_register.xlsx` | — | — | Compiled | 4 |
| `03_reference_control_diagram.png` | — | — | Reference | 8 |
| `13_partial_existing_architecture.puml` | — | — | Draft, incomplete | 8 |
| `04_control_sequence_and_modeling_notes.docx` | CDS-IAQ-02 / MOD-NT-03 | B | Released 2026-03-01 | 3 |
| `06_iaq_design_review_minutes.md` | DR-IAQ-05 | Final | Approved 2026-02-14 | 2 |
| `14_engineer_field_notes.txt` | — | 2026-03-04 | Uncontrolled | 10 |
| `05_bms_controls_email_thread.eml` | — | Feb–Mar | Informal — **carries CR-IAQ-007** | 9 → **1** |
| `07_legacy_co2_control.mo` | — | — | Archived (Kp=4, peak 12) | 11 |
| `08_co2_sensor_datasheet.pdf` | — | — | Released | 5 |
| `09_commissioning_test_procedure_CP23.pdf` | CP-23 | C | Released | 6 |
| `10_occupancy_schedule.csv` | OCC-SCH-04 | C | Approved schedule | 7 |
| `11_reference_run_24h.csv` | — | — | Reference trace | 7 |
| `12_bim_room_export.json` | — | — | Geometry export | 7 |
