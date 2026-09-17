# 02 — Target User and Journeys

**Status:** Baseline · **Decision:** ADR-010 · **Required by:** PRD §4 ("State which user you chose.")

---

## 1. The user we chose

> **The systems engineer.**
> *"Convert a specification or sketch into a first-pass SysML model without starting from a blank canvas."*

### 1.1 Why this user, and what we gave up

We build for the person who owns the **system model** — not the person who owns the simulation, and not the
person who only reviews it. Consequences we accept:

| We optimise for | We deliberately do not optimise for |
|---|---|
| A structurally complete first-pass model that is faster to **correct** than to author | A physics-accurate model that needs no tuning |
| SysML v2 as the primary artifact; Modelica as the executable proof that the structure is coherent | Modelica as the primary artifact with SysML as documentation |
| Explicit assumptions and open questions the engineer can resolve and re-run | Autonomy — we do not try to remove the engineer from the loop |
| Vocabulary and tags from **the engineer's own documents** | A normalised house ontology imposed on the user |

The asymmetry that defines the product: **a wrong element that looks right costs the engineer more than a
missing element that is flagged.** Reviewing a stated gap takes seconds; discovering a silently invented port
three days later costs a design review. Every design trade-off in this repo resolves toward the flagged gap.
This is the same asymmetry the PRD encodes in §8.2: *"partially complete and honest scores above superficially
complete and quietly wrong."*

### 1.2 Anti-persona

We are **not** building for the engineer who wants a finished model with one click and no review step. If a
user will not read the assumption list, SpecForge is the wrong tool for them and will mislead them. The UI
states this at the point of output rather than hiding it.

## 2. Primary journey — "I have a folder and a deadline"

Amrita is handed a shared folder for a two-tank transfer rig: a customer URS PDF, an engineering register
spreadsheet, a design-review markdown, an email thread, a legacy `.mo` file from a colleague who has left, a
reference control diagram PNG, and a commissioning procedure. She needs a SysML v2 model for design review on
Thursday.

| # | Step | System behaviour | Spec |
|---:|---|---|---|
| 1 | Creates a project, drags the whole folder in | Every file accepted; no schema demanded; unknown types are recorded as unparsed rather than rejected | `04_ingestion_spec.md` |
| 2 | Watches ingestion | Per-file progress streams. Each file resolves to source fragments with page/sheet/cell/line locators | `04_ingestion_spec.md` §5 |
| 3 | Sees an **Evidence** view before any model exists | Documents ranked by authority with revision and status. The superseded legacy `.mo` is visibly demoted | `05_evidence_precedence_spec.md` |
| 4 | Gets a **structural draft in under 2 minutes** | Parts, ports, connections, attributes — each element shows the fragment it came from | SF-SPD-01 |
| 5 | Opens **Conflicts (3)** | *T1 high limit: 0.78 m (URS-001 Rev A, superseded) vs **0.80 m (CR-004, approved 2026-03-11)**.* Resolution stated, rationale stated, both sides retained | `05_evidence_precedence_spec.md` §6 |
| 6 | Opens **Assumptions (7)** | *"Tank TK-101 has an outlet port. No document states it; implied by the transfer connection to XV-102. Standard assumption `SA-FLUID-002`."* | `05_evidence_precedence_spec.md` §7 |
| 7 | Opens **Open questions (2)** | Questions the system refused to guess at, each blocking or non-blocking, each with the decision it gates | `05_evidence_precedence_spec.md` §8 |
| 8 | Answers one, overrides one assumption | Re-run is incremental; the traceability record updates; her answer outranks inference on re-run | SF-EXT-02, SF-EXT-06 |
| 9 | Gets **SysML v2 + Modelica**, Modelica **compiles** | Compile gate is green in the UI, with the exact `omc` command shown so she can run it herself | `08_modelica_emission_spec.md` |
| 10 | Runs simulation, compares to the reference trend CSV in her folder | Overlay plot; deviations listed rather than smoothed away | `09_validation_and_repair_spec.md` §7 |
| 11 | Exports for review | `model.sysml`, `Model.mo`, `summary.md`, `traceability.md`, `evidence.json`, plots | `10_traceability_and_reporting_spec.md` |

**Success test for this journey:** Amrita spends her time *deciding*, not *transcribing*. She should be able
to approve or reject the model in **under a minute** from `summary.md` alone (PRD output layer 4), and defend
every element in it at the review.

## 3. Secondary journeys

These are served by the same architecture. We do not add features for them.

| Journey | User | What they use | Why it already works |
|---|---|---|---|
| "Does it run?" | Simulation engineer | `Model.mo` + the compile command + simulation plots | Compile gate and repair loop are core, not optional |
| "Where did that come from?" | Design reviewer | `traceability.md`, the Evidence view, the conflict ledger | Provenance is mandatory on every element by schema |
| "I don't know SysML" | Domain newcomer | `summary.md`, the assumption list, guided clarifying questions | Emission is deterministic, so output is always structurally legal |

## 4. What the user must never experience

Requirements stated as prohibitions, because each maps to a scoring criterion.

| ID | Prohibition | Rationale |
|---|---|---|
| **SF-UX-01** | A component, port or equation appears with no traceable origin | SF-ACC-06, SF-IN-03 — fabrication |
| **SF-UX-02** | A contradiction is silently resolved, with only the winner shown | SF-IN-02 — the loser and the rule must both be visible |
| **SF-UX-03** | The pipeline runs with no progress indication | PRD §8.1 — *"Silence with no progress indication will be [penalised]."* |
| **SF-UX-04** | A failure produces a stack trace and nothing else | ADR-007 — degrade gracefully, always emit the best artifact reached plus the gap report |
| **SF-UX-05** | A number appears without its unit, or with an inferred unit not marked as inferred | SF-ACC-06; L2 and L3 make unit confusion the central trap |
| **SF-UX-06** | An implementation artefact is presented as physical reality | L2's `C_source = 100 kg/kg` is a numerical device; L2's negative `m_flow` is a port convention. Both must stay labelled as such |

`SF-UX-06` is subtle and worth stating plainly: the L2 bundle contains a parameter that is physically absurd
(a CO2 mass fraction of 100 kg/kg) and is **correct** as a numerical implementation device. A system that
"corrects" it is wrong. A system that reports it as a room concentration is also wrong. The model must carry
the distinction between *model parameter*, *as-built measurement* and *physical quantity* — which L3's design
review states as an explicit requirement (decision 10, DR-MAG-03).

## 5. Design principles, in priority order

Applied when specs conflict. Higher number never overrides lower.

1. **Honest before complete.** A stated gap beats a plausible invention.
2. **Traceable before elegant.** If we cannot say where an element came from, it does not ship.
3. **Deterministic before clever.** Anything that can be generated by template must not be generated by a model.
4. **General before case-specific.** No branch in `src/` may name a benchmark case.
5. **Compiling before featureful.** The `omc` gate never regresses to add a feature.
