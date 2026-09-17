# 05 — Evidence, Precedence, Assumptions and Conflicts

**Status:** Baseline · **Decision:** ADR-005 · **Module:** `src/spec_forge/evidence/`
**Implements:** SF-IN-01, SF-IN-02, SF-IN-03, SF-ACC-06

---

## 1. Why this subsystem is the centre of the product

The PRD's hardest requirements are not about parsing or code generation:

> Missing information must be **either inferred with a stated assumption, or surfaced as a question. It must not
> be silently invented.** Contradictions must be **flagged rather than resolved arbitrarily.**

Ingestion is a solved problem. Emission is templating. **The engineering question is which source wins, and
whether the system can say why.** Every benchmark bundle is constructed around that question — and the authors
made it explicit: the supplied engineering registers contain a `Change_Log` sheet with a **"Precedence Note"**
column and a `Source_Index` sheet with a **"Reliability"** column and a **"Known Caveat"** column.

The dataset is telling us what to build. This module is the answer.

It also generalises, which is what the PRD rewards over case-specific handling: *"a specification supersedes a
draft, an approved change supersedes a released baseline, a measurement is not a design value"* is true of every
engineering organisation on earth, not of tanks and brine.

## 2. Authority tiers

Every `SourceDocument` and every extracted claim is assigned an **authority tier**. Lower number = higher
authority.

| Tier | Class | Examples in the bundles | Rationale |
|---:|---|---|---|
| **0** | **User override** | Engineer answers a question or corrects an element in the UI | The human is the authority of last resort |
| **1** | **Approved change record** | CR-004, CR-IAQ-007, CR-MAG-004/006, CR-017 | Explicitly supersedes prior values by definition |
| **2** | **Approved design-review decision** | DR-02, DR-IAQ-05, DR-MAG-03, DR-07 (status Final/Approved) | Resolves ambiguity in the released spec with authority |
| **3** | **Released controlled specification** | URS-001 Rev A, ICD-01 Rev B, CDS-02 Rev B, MOD-NT-03 | The baseline contract |
| **4** | **Compiled engineering register** (rows marked Active / Effective=Yes) | `02_*_register.xlsx` | Curated, but a secondary compilation of primary records |
| **5** | **Vendor datasheet** | valve, sensor, core/coil datasheets | Authoritative for hardware, silent on intent |
| **6** | **Commissioning / verification procedure** | TP-17, CP-23, AV-11, batch acceptance | *"Verification input, not design authority"* — the register says so itself |
| **7** | **Reference dataset / recorded trend** | `10_demo_run_900s.csv`, `11_reference_run_24h.csv` | Evidence of **fact**, not of **intent** |
| **8** | **Diagram** | reference PNG, `.puml` drafts | Strong on topology, weak on values |
| **9** | **Correspondence** | `.eml` threads | Informal — *see §3, the transmission rule* |
| **10** | **Engineer field / scratch notes** | `12_operator_shift_notes.txt`, `15_*_notes.txt` | Explicitly uncontrolled; one is literally headed *"Engineer scratchpad - uncontrolled"* |
| **11** | **Legacy code / archived model** | `07_legacy_*.mo` | Superseded by default; the files say so in their own comments |

Tier 6 is not a judgment call we invented — L1's `Change_Log` states it verbatim for TP-17: *"Verification input,
not design authority."* Tier 7 matters for the same reason: L2's field notes report an observed trend maximum of
996.52 ppm. That is a true fact about a run. It is **not** a requirement, and a system that turns it into a
setpoint has misread the document class.

## 3. The transmission rule

> **Authority attaches to the record cited, not to the medium that carries it.**

An email is tier 9. An email that says *"CR-004 is now approved. Please treat 0.80 m as the effective T1 high
limit"* is transmitting a **tier 1** record, and the claim inherits **tier 1** — with `authority_record: "CR-004"`
and the email fragment as the citation.

This single rule decides three of the four benchmarks:

| Case | Transmitted record | Claim | Would be wrong without the rule |
|---|---|---|---|
| L1 | CR-004 (approved 2026-03-11) | T1 high = 0.80 m, waits 12 s / 8 s | Email loses to URS → model uses stale 0.78 m |
| L2 | CR-IAQ-007 | Kp=6.0, bias=3.5 ACH, peak 15 people | Model keeps legacy Kp=4, peak 12 |
| L3 | CR-MAG-004 / CR-MAG-006 | mu_r=1200, sigma=0.08 | Model keeps v1.0 sigma=0.05, mu_r=1000 |
| L4 | CR-017 (approved 2026-03-05) | B6→B1, B7→B2, B7 ≤ 25 C | Model keeps superseded StateGraph routing |

**Detection.** An LLM extraction pass over each fragment returns
`{cites_record: str|null, record_status: "approved"|"proposed"|"rejected"|null, effective_date: date|null}`.
Two guards apply:

- A **proposed** record does not inherit tier 1. In L4, Marco writes *"I will raise CR-017"* on 3 Mar — that is a
  proposal. The approval arrives on 5 Mar from a different author. Only the latter transmits authority.
- A record cited as **rejected or superseded** transmits nothing. L2's *"The 1300 ppm interpretation is rejected
  for this benchmark"* must not be read as evidence *for* 1300 ppm.

## 4. Resolution algorithm

`evidence/precedence.py`, rule id `PRE-01`:

```
resolve(claims: list[Claim]) -> Resolution
  1. Drop claims whose record_status is rejected or withdrawn.          → record as dropped, keep visible
  2. Group by (subject, quantity).
  3. If one claim remains                      → selected, confidence unchanged.
  4. Sort by (authority_tier asc, effective_date desc, specificity desc).
  5. If the top two differ in tier             → select top.  rule = PRE-01-tier
  6. Else if they differ in effective_date     → select later. rule = PRE-01-tier-then-date
  7. Else if one is more specific
     (scoped to a state/part/config)           → select it.    rule = PRE-01-specificity
  8. Else                                      → UNRESOLVED.   raise blocking Conflict.
  9. Always: emit a Conflict record retaining every losing position.
```

Step 9 is not optional even when resolution is obvious. SF-IN-02 requires contradictions to be **flagged**, and a
resolved conflict is still a conflict the reviewer must be able to see. A quietly-correct answer and a quietly-
wrong answer are indistinguishable to the user; only the visible rationale separates them.

### 4.1 Never merge across `value_kind`

Two claims are only in conflict if they describe **the same kind of thing**. L3 makes this the central trap:

- air gap δ = **1.50 mm** — `nominal_design`, drawing MC-101
- air gap δ = **1.58 mm** — `as_built_measurement`, metrology note on the physical shim stack

These are **not** a contradiction. DR-MAG-03 decision 5 says so explicitly, and the engineer's email says *"Please
do NOT silently replace the 1.50 mm nominal gap"*. The correct output carries **both**, typed differently: the
nominal value parameterises the analytic benchmark, the as-built value parameterises a separate validation
configuration. Grouping in step 2 is therefore keyed by `(subject, quantity, value_kind)`.

The same applies to L4: `StandardWater` is an **integration baseline** for topology and sequence verification;
`WaterNaCl` is the **intended physical medium**. Not a conflict — two configurations.

## 5. The evidence ledger

`evidence/ledger.py` maintains, per run:

- every `SourceDocument` with its tier, revision, status and effective date;
- every extracted `Claim` with subject, value, `value_kind`, citing fragments and tier;
- the resolution outcome and rule applied for each claim group;
- a **coverage report**: which requirements, parts and attributes have evidence, and which rest on assumptions.

Persisted to `runs/<run_id>/evidence.json` and to Postgres (`13_data_model_spec.md`). Rendered as the Evidence
view (`11_web_application_spec.md` §5) — the systems engineer's first stop, available **before** a model exists,
because deciding which documents are authoritative is itself engineering work.

## 6. Conflicts

Shape in `03_system_ir_spec.md` §7.

| Severity | When | Effect |
|---|---|---|
| `info` | Resolved by a clear tier or date difference | Reported; pipeline continues |
| `warn` | Resolved by specificity, or the winning margin is one tier | Reported prominently; continues |
| `blocking` | Unresolved, or the subject is safety-relevant (interlock, permissive, limit) | **Halts emission**; becomes an `OpenQuestion` |

Safety-relevant subjects always escalate. A contradiction about a cosmetic label is an `info`; a contradiction
about whether two valves may be open simultaneously is not something to resolve by sort order.

### 6.1 Conflicts the benchmarks require us to produce

A run that reports **zero** conflicts on any of these has failed, regardless of what else it produced.

| Case | Conflict | Winner | Rule |
|---|---|---|---|
| L1 | T1 high: 0.78 (URS-001 A, T3) vs 0.78 (legacy .mo, T11) vs **0.80 (CR-004, T1)** | 0.80 m | `PRE-01-tier` |
| L1 | Post-transfer wait: 10 s (URS A) vs **12 s (CR-004)**; inter-cycle 10 s vs **8 s** | 12 s / 8 s | `PRE-01-tier` |
| L2 | CO2 limit: "1000 ppm above outdoor ≈ 1300" (email, T9, **rejected**) vs **1000 ppm absolute (DR-IAQ-05, T2)** | 1000 absolute | dropped at step 1 + `PRE-01-tier` |
| L2 | Kp = 4, peak 12 (legacy .mo, T11) vs **Kp = 6.0, bias 3.5, peak 15 (CR-IAQ-007, T1)** | CR values | `PRE-01-tier` |
| L3 | mu_r: 1000 (CoreCatalog_A) vs **1200 (CR-MAG-004)**; sigma: 0.05 (v1.0) vs **0.08 (CR-MAG-006)** | 1200 / 0.08 | `PRE-01-tier` |
| L3 | Measuring coil turns: 40 (old sketch) vs **50 (Coil Data Rev B)** | 50 | `PRE-01-tier-then-date` |
| L4 | Return routing: legacy StateGraph (B7→B1, B6→B2) vs **CR-017 (B6→B1, B7→B2)** | CR-017 | `PRE-01-tier` |
| L4 | B7 cooling: 20 C (handwritten sheet, T10) vs **25 C (CR-017, T1)** | 25 C | `PRE-01-tier` |

**Not conflicts** — must *not* appear as such: L3 gap 1.50 vs 1.58 mm (different `value_kind`); L4
StandardWater vs WaterNaCl (different configuration); L2 `C_source = 100 kg/kg` (a `numerical_device`, not a
competing concentration).

Regression-tested per case in `test/unit/evidence/test_expected_conflicts.py` against
`test/testdata/expected/<case>/conflicts.yaml`.

## 7. Assumptions

An assumption is a **declared, reviewable inference** used where evidence is absent. Shape in
`03_system_ir_spec.md` §7.

### 7.1 Categories

| Category | Meaning | Example |
|---|---|---|
| `standard_engineering` | A named convention from the standard-assumption catalogue | A tank has an outlet |
| `library_default` | A default supplied by the component archetype | On/off valve fails closed |
| `inferred_from_topology` | Required to make a stated connection coherent | An unnamed port implied by an Interface Matrix row |
| `unit_normalisation` | A unit was not stated and was inferred from quantity and magnitude | A bare `0.05` in a level column read as metres |
| `numerical_necessity` | Required for the model to initialise or solve | A junction volume inserted between isolating valves |

### 7.2 Standard assumption catalogue

Versioned YAML at `src/spec_forge/evidence/standard_assumptions.yaml`, each entry with a stable id, statement,
applicability condition and rationale. **An assumption may only be created from a catalogue entry or a library
default.** Free-form assumption invention is prohibited — otherwise "declared assumption" becomes an
unfalsifiable excuse for fabrication, and SF-IN-03 is satisfied in letter while being violated in substance.

Seed entries: `SA-FLUID-001` a tank has at least one inlet and one outlet · `SA-FLUID-002` an outlet implied by
a downstream connection · `SA-CTRL-001` discrete process valves fail closed on loss of power · `SA-CTRL-002`
level comparisons use inclusive thresholds · `SA-ELEC-001` an electrical network requires exactly one ground ·
`SA-MAG-001` a magnetic network requires exactly one magnetic ground · `SA-NUM-001` a junction volume is
required where multiple isolating pressure-drop components could leave states undefined.

`SA-ELEC-001` and `SA-MAG-001` are not academic: L3's design review makes both grounds an explicit requirement
(decision 8) while the draft `.puml` note records that neither is exposed. The assumption catalogue is how a
requirement stated in one document repairs an omission in another.

### 7.3 Rules

- Every assumption is `reviewable: true` and appears in `summary.md` and the UI.
- An assumption **never** overrides evidence. If evidence later appears, the assumption is retracted and the
  retraction is recorded.
- Assumptions carry confidence; `< 0.7` additionally raises a non-blocking `OpenQuestion`.
- **Prohibited:** assuming a *component* into existence. Assumptions may add ports, units, defaults and
  parameters to parts that evidence established. A part with no evidential basis is a fabrication
  (SF-IN-03), and `V-TRACE-002` enforces this.

## 8. Open questions

Generated when: a conflict is unresolved or safety-relevant; a required attribute has no candidate; a diagram
region was unreadable (`04_ingestion_spec.md` §4.9); a `.puml`/legacy note declares a known omission; or an
assumption's confidence is below threshold.

Each states **why it matters** and **what it gates** — a question the engineer cannot act on is noise. Blocking
questions halt emission; non-blocking questions proceed under a default that is itself a registered assumption,
so the two PRD paths (*infer with a stated assumption* / *surface as a question*) stay distinct and auditable.

In the SaaS surface these become the clarifying dialogue (SF-EXT-02): targeted questions with candidate answers
drawn from the losing conflict positions, so answering is a click rather than an essay. An answer is recorded at
tier 0 and persists across re-runs.

## 9. Reporting

`evidence/report.py` renders the ledger into `traceability.md` and the assumption/conflict sections of
`summary.md` (`10_traceability_and_reporting_spec.md`). Required content: every conflict with all positions and
the rule applied; every assumption with rationale and category; every open question with what it gates; and the
coverage statistics — **what fraction of model elements rest on evidence versus assumption**.

That last number is the honest headline of the whole product, and it belongs at the top of the summary rather
than buried. An engineer deciding whether to trust a generated model wants it before anything else.
