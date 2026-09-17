# L3 — Quasi-Static Magnetic Circuit

**Reasoning under test:** multiphysics energy transfer across domains, with an **explicit loss path**.
**Bundle:** `test/testdata/benchmarks/L3_magnetic_circuit/` · 15 files

---

## 1. The system

A rectangular iron core with square cross-section, one discrete air gap, an exciting coil, a measuring coil at
the gap, a useful-flux sensor, and a **leakage flux path**. Modelled as quasi-static magnetic flux tubes under a
**linear-reluctance** assumption.

Three physical domains meet: **electrical** (coil current, induced voltage), **magnetic** (mmf, flux, reluctance),
and the **geometric** parameterisation that links them.

```
  CurrentRamp ──▶ ExcitingCoil (N=600)  ──mmf = N·I──▶  magnetic network
                        │                                     │
  Left leg ── Upper yoke ── Right-leg iron ──┬── AirGap (δ) ───┬── Lower yoke
   (l-a)       (l-a)        (l-a-δ)          └── Leakage ──────┘
                                              (parallel branch, same Vm)
                                                    │
                            MeasuringCoil (N=50) ◀──┤ useful gap flux
                            FluxSensor          ◀───┘
  ElectricGround                     MagneticGround
```

## 2. Expected model elements

**Magnetic:** left leg · upper yoke · right-leg iron · air gap · **leakage branch** · lower yoke ·
**magnetic ground**.
**Electrical:** current source (RMS phasor ramp) · exciting coil (600 turns) · measuring coil (50 turns) ·
**electrical ground**.
**Sensing:** useful-flux sensor · measuring-coil induced voltage.

### 2.1 What the draft `.puml` omits

Its own note lists the omissions: **leakage branch, element-wise core segmentation, electric ground, magnetic
ground, revision/configuration values**. Three of those five are mandatory (DR-MAG-03 decisions 3 and 8), so a
pipeline that treats the diagram as the architecture produces a model missing its loss path and both reference
potentials — and, for the grounds, one that will not even compile.

The recovery path is the assumption catalogue: `SA-ELEC-001` and `SA-MAG-001` (`05_evidence_precedence_spec.md`
§7.2) add the grounds as *declared assumptions* justified by the design-review requirement, while the leakage
branch comes from the model definition notes and SRS §1.

## 3. Physics

### 3.1 Network

Series flux-tube reluctances: left leg → upper yoke → right-leg iron. A **parallel branch** where the air gap and
the leakage path split, rejoining before the lower yoke.

| Element | Area | Mean length | μ_r |
|---|---|---|---|
| Left leg | a² | l − a | μ_r |
| Upper yoke | a² | l − a | μ_r |
| Right-leg iron | a² | **l − a − δ** | μ_r |
| Air gap | a² | **δ** | 1 |
| Lower yoke | a² | l − a | μ_r |

Relations: `Rm = length / (μ0·μ_r·A)` · `B = Φ / A` · `H = B / (μ0·μ_r)` · `Vm = H · length` · mmf `= N·I`
· `|U| = 2πf·N·|Φ|`.

### 3.2 The leakage branch — `V-PHYS-003`

```
Φ_gap = (1 − σ) · Φ_core          σ = 0.08  ⇒  Φ_gap = 0.92 · Φ_core
R_leak = R_gap · (1 − σ) / σ
```

The gap and leakage branches are **parallel**: same magnetic potential difference, different flux. The scratch
note states the failure mode directly — ***"Do not put total Phi_core into gap B calculation."*** A model that
routes total core flux through the gap overestimates gap flux density by ~8.7% and will still compile and run.

This is `V-PHYS-003` (parallel branches share the same effort difference) and it is the reason that rule exists.

## 4. Parameters and precedence

| Quantity | Legacy / alternative | **Released** | Authority |
|---|---|---|---|
| μ_r | 1000 (CoreCatalog_A) | **1200** | CR-MAG-004 |
| σ (leakage coefficient) | 0.05 (v1.0 model, "early idealized estimate") | **0.08** | CR-MAG-006, approved 2026-02-26 |
| Measuring-coil turns | 40 (old sketch) | **50** | Coil Data Rev B (has the polarity dots) |
| Exciting-coil turns | — | **600** | SRS / Coil Data |
| Air gap δ | — | **1.50 mm nominal** | Drawing MC-101 |
| a (core side) | — | 25 mm | SRS §3 |
| l (reference length) | — | 150 mm | SRS §3 |

## 5. The nominal-vs-as-built distinction — this case's signature trap

| Value | Kind | Source |
|---|---|---|
| δ = **1.50 mm** | `nominal_design` | Drawing MC-101, analytic benchmark |
| δ = **1.58 mm** | `as_built_measurement` | Metrology note, physical shim stack |

**These are not in conflict.** DR-MAG-03 decision 5: *"The nominal design/analytic air gap is 1.50 mm; the
1.58 mm measurement is a separate as-built prototype configuration."* The email is emphatic: ***"the technician
measured 1.58 mm at the physical shim stack. Please do NOT silently replace the 1.50 mm nominal gap in the
analytic benchmark. We need both."***

Decision 10 generalises it into a modelling requirement: *"The model shall preserve the distinction between
**model parameter**, **as-built measurement**, and **verification configuration**."*

This is the requirement that `value_kind` exists to satisfy (`03_system_ir_spec.md` §4.4) and that the
never-merge-across-`value_kind` rule protects (`05_evidence_precedence_spec.md` §4.1). Correct output: **both
values retained**, the nominal parameterising the analytic benchmark, the as-built parameterising a separate
validation configuration. Reporting them as a conflict is a **false positive** and fails the expected-conflicts
fixture just as surely as missing a real one.

## 6. Phasor conventions

| Rule | Consequence if lost |
|---|---|
| Current input is an **RMS phasor magnitude** — not instantaneous, not peak | A √2 error (2 A rms → 2.828 A peak) |
| For linear real reluctance, `Rm` is real, so Φ and `Vm` share phasor angle | Spurious phase |
| Exciting-coil induced voltage: **positive** electric orientation | Sign error |
| Measuring-coil voltage: **negative** orientation relative to useful gap flux | Sign error |
| Both magnitudes follow `\|U\| = 2πf·N·\|Φ\|` | — |

The scratch note flags the exact confusion to avoid: *"Scope screenshot from bench uses peak scale, so 2 Arms
would be 2.828 A peak if converted."* The bench screenshot is tier 10 evidence about an instrument setting, not
about the model's input convention.

## 7. Scope boundaries — stated explicitly

DR-MAG-03 decision 9: **no force interaction, no saturation, no hysteresis, no eddy-current loss** in the
baseline. SRS §5: *"The core is linear in this benchmark; nonlinear saturation is handled only by a separate
model variant and **shall not be inferred into the baseline**."*

A model that adds saturation because "real iron saturates" is **wrong for this case**. This is a direct test of
SF-IN-03 — not fabricating physics that is not derivable from the input — in its least intuitive form, where the
fabrication would be physically reasonable and still incorrect. These exclusions belong in the summary's *"What
this model does NOT cover"* section.

## 8. Grounds

Both are mandatory: `ElectricGround` in the coil circuit, `MagneticGround` in the flux-tube network
(SRS §5, DR-MAG-03 decision 8). `V-TOPO-007` requires exactly one of each; `V-MOD-005`/`V-MOD-006` catch the
omission at compile time — an ungrounded network is one of the most common ways generated Modelica fails.

## 9. Reference behaviour

`09_datasets/10_quasistatic_ramp_results.csv` — quasi-static current ramp. `12_geometry_metrology_export.json` —
as-built geometry (a `as_built_measurement` source, not `nominal_design`).

Verification is **analytic** (`09_analytic_verification_procedure.pdf`, AV-11) rather than trajectory-based:
compute Φ, B, H, Vm and induced voltages from the released parameters and compare. This makes L3 the case where
`simulate` matters least and parameter correctness matters most.

## 10. Traps

| # | Trap | Wrong outcome | Defence |
|---|---|---|---|
| 1 | δ 1.50 vs 1.58 mm | Nominal silently replaced by as-built, or reported as a conflict | `value_kind`, never-merge rule |
| 2 | σ 0.05 vs **0.08**; μ_r 1000 vs **1200** | Legacy values | CR-MAG-006 / CR-MAG-004, tier 1 |
| 3 | Measuring turns 40 vs **50** | Old sketch wins | Coil Data Rev B, later + higher tier |
| 4 | Leakage is **parallel**, shares Vm | Total core flux into the gap — 8.7% error, compiles fine | `V-PHYS-003` |
| 5 | RMS vs peak phasor | √2 error | Explicit convention in IR |
| 6 | Coil orientation signs (+ exciting, − measuring) | Sign error in induced voltage | Declared convention |
| 7 | Both grounds required, neither in the draft diagram | Does not compile | `SA-ELEC-001`, `SA-MAG-001` |
| 8 | Saturation is **excluded** | "Improved" with nonlinear iron | Scope boundary; SF-IN-03 |
| 9 | Right-leg length is `l − a − δ`, not `l − a` | Gap counted twice in iron | Geometry table |

## 11. Acceptance

| Check | Target |
|---|---|
| Structural coverage | ≥80%, **including leakage branch and both grounds** |
| Effective parameters | μ_r=1200, σ=0.08, N_meas=50, N_exc=600, δ_nominal=1.50 mm |
| Both gap values | Retained with distinct `value_kind`; **not** reported as a conflict |
| Conflicts | μ_r, σ, measuring turns |
| Topology | Gap and leakage in parallel, rejoining before the lower yoke |
| Compile | `omc checkModel` green |
| Analytic check | Φ, B, H, Vm within tolerance of AV-11 |
| Scope | Summary states saturation/hysteresis/eddy/force are excluded |

## 12. Sources

| File | Doc | Rev | Status | Tier |
|---|---|---|---|---|
| `01_system_requirement_specification.pdf` | SRS | A | Released | 3 |
| `02_magnetic_engineering_register.xlsx` | — | — | Compiled | 4 |
| `03_reference_magnetic_circuit.png` | — | — | Reference | 8 |
| `11_partial_magnetic_architecture.puml` | — | — | Draft, incomplete | 8 |
| `04_model_definition_notes.docx` | — | C | Released | 3 |
| `06_design_review_minutes.md` | DR-MAG-03 | Final | Approved 2026-03-12 | 2 |
| `13_flux_tube_theory_note.pdf` | — | — | Theory note | 5 |
| `15_engineer_scratch_notes.txt` | — | — | **"Uncontrolled"** | 10 |
| `05_magnetics_email_thread.eml` | — | Feb 2026 | Informal — **carries CR-MAG-004/006** | 9 → **1** |
| `07_legacy_magnetic_circuit.mo` | — | 1.0 | Archived (σ=0.05) | 11 |
| `08_core_coil_datasheet.pdf` | Coil Data | B | Released | 5 |
| `09_analytic_verification_procedure.pdf` | AV-11 | — | Verification input | 6 |
| `14_lab_validation_runbook.docx` | — | — | Validation config | 6 |
| `10_quasistatic_ramp_results.csv` | — | — | Reference results | 7 |
| `12_geometry_metrology_export.json` | — | — | **As-built measurement** | 7 |
