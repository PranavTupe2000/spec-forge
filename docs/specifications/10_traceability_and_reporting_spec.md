# 10 — Traceability, Evidence Reporting and Human Summary

**Status:** Baseline · **Module:** `src/spec_forge/emit/report/`
**Implements:** PRD output layers 3 and 4 · SF-MIN-06, SF-ACC-06

---

## 1. Two deliverables, two audiences

| Layer | Artifact | Audience | Test |
|---:|---|---|---|
| **3** | `traceability.md` + `evidence.json` | Design reviewer, auditor, judge | Can every element be traced to a fragment or assumption? |
| **4** | `summary.md` | The systems engineer, in a hurry | **Can they approve or reject in under a minute?** |

The under-a-minute constraint is from the PRD and it is a hard design constraint, not an aspiration. It governs
ordering, length and what gets cut.

## 2. `summary.md` — the one-minute artifact

Fixed structure. **Honest headline first.** The engineer must learn the worst thing about the model before the
best thing.

```markdown
# TwoTankController — generated model summary

> **Coverage 87%** · 34 elements from evidence · 5 from stated assumptions · **2 open questions** · **3 conflicts resolved**
> Modelica: **COMPILES** ✓   Simulation: ran 900 s, max deviation 0.012 m vs reference
> Generated 2026-09-20 14:31 · run 01JD… · SpecForge 0.4.1

## What this system is
Two-tank liquid transfer rig under sequential control. Tank 1 (TK-101) is filled from a source
through XV-101, transferred to Tank 2 (TK-102) through XV-102, and drained through XV-103.
A PLC (PLC-101) sequences the cycle with START / STOP / SHUT operator commands.

## Structure
| Part | Tag | Type | Ports | From |
|---|---|---|---|---|
| tank1 | TK-101 | Vertical tank | inlet, outlet, level | Equipment_Schedule A3 |
…

## Key parameters
| Parameter | Value | Authority | Superseded |
|---|---|---|---|
| T1 high limit | **0.80 m** | CR-004 (2026-03-11) | 0.78 m — URS-001 Rev A, legacy .mo |
…

## ⚠ Conflicts resolved (3)
**T1 high limit** — selected **0.80 m** (CR-004, approved change, tier 1).
Rejected: 0.78 m (URS-001 Rev A, tier 3, superseded); 0.78 m (legacy model, tier 11, archived).
Rule: tier precedence.
…

## ⚠ Assumptions (5)
**Tank TK-101 has an outlet port.** No document states it; implied by interface IF-HYD-03.
Standard assumption SA-FLUID-002. Confidence 0.95.
…

## ❓ Open questions (2)
**Is the post-shutdown state IDLE or a distinct SHUTDOWN_COMPLETE?**
Why it matters: determines whether a later START begins a new fill cycle.
Gates: trans:shutdown_to_idle. Proceeded with: IDLE (DR-02 D-07).
…

## What this model does NOT cover
- Emergency stop. `shut` is a controlled drain, not an E-stop (DR-02, field notes). Out of scope.
- Valve stroke dynamics. Datasheet gives 0.8 s full-open; modelled as instantaneous.

## How to check it yourself
    omc build/omc/check_TwoTankController.mos
```

### 2.1 Rules

- **Coverage first.** The evidence/assumption split is the headline number.
- **Conflicts, assumptions and open questions are never collapsed** into "see details".
- **"What this model does NOT cover" is mandatory** and may not be empty. If the generator believes it covered
  everything, it has stopped looking — and this section is where the PRD's *"honest about its gaps"* becomes
  visible to a reader in ten seconds.
- Every claim links to its fragment id.
- Target 1–2 screens. Long tables are truncated with a pointer to `traceability.md`.

## 3. `traceability.md` — the audit artifact

Complete, not skimmable. Four sections:

1. **Sources** — every document with tier, revision, status, date, sha256, fragment count, ingest method.
2. **Element → evidence** — for each IR element, its fragments with verbatim quoted text and locator.
3. **Evidence → element** — the reverse index: which model elements each fragment produced, and which fragments
   produced nothing (a useful signal that we may have missed something).
4. **Requirements matrix** — requirement × satisfied-by × verified-by, with unsatisfied `must` requirements
   called out.

```markdown
### part:tank_1 — "tank1" (TK-101)
Archetype: fluid.tank.vertical · Confidence 0.99 · Evidence

- `frag:reg#Equipment_Schedule.A3` — 02_engineering_data_register.xlsx, sheet Equipment_Schedule, A3:L3
  > TK-101 | tank1 | Tank | Intermediate receiving tank | 1.2 | 1 | 0.9 | … | LT-101 | MDS-01
- `frag:urs001#p1.t2.r1` — 01_customer_URS.pdf, p.1, table 2, row 1
  > TK-101 | Tank 1 | tank1 / T1
- `frag:puml#L6` — 11_partial_legacy_architecture.puml, line 6
  > component "tank1\n(TK-101)" as T1

Aliases: tank1, T1, Tank 1, TK-101
```

## 4. `evidence.json`

Machine-readable form of the same content, consumed by the web UI and by tests. Schema at
`build/schema/evidence-1.0.schema.json`. Contains the full ledger (`05_evidence_precedence_spec.md` §5):
documents, claims, resolutions, conflicts, assumptions, open questions, coverage statistics.

## 5. Simulation reporting

When simulation runs:

- **Plots** — matplotlib PNG + the underlying CSV. One plot per signal group (levels, valve commands, controller
  state, and for L2 concentration vs limit).
- **Reference overlay** where a reference trace exists (`09_validation_and_repair_spec.md` §7), generated vs
  reference on shared axes.
- **Deviation table** — per signal: max abs, RMS, event-time deltas, pass/fail against the manifest tolerance.
- **Plain-language verdict** — *"Tank 1 fills to 0.80 m in 125 s and the cycle repeats every 412 s. Matches the
  reference run within 0.012 m. Controller state transitions occur within 1 s of the reference at all five
  command events."*

The verdict line is what a systems engineer actually reads. It is generated from the deviation table by
template, not by an LLM, so it cannot overstate agreement.

## 6. Run directory

Everything for one run, self-contained and diffable:

```
runs/<run_id>/
  manifest.json            inputs, versions, config, git sha, seed
  model.sfir.json          the IR — source of truth
  model.sysml              layer 2
  Model.mo                 layer 5
  COMPILE.md               the exact command judges run
  evidence.json            layer 3 (machine)
  traceability.md          layer 3 (human)
  summary.md               layer 4
  simulation/
    results.csv  plots/*.png  deviation.md
  llm/                     recorded request/response pairs for --replay
  repair.log               every repair attempt and outcome
  validation.json          every rule result
  events.jsonl             progress event stream
```

`manifest.json` records the git sha, config, model ids and seed. Without it, SF-ACC-05 (repeatability) is not
verifiable and a judge cannot reproduce a result.

## 7. Export

Single `.zip` of the run directory, plus per-artifact download. `COMPILE.md` is always included, since the repo
must ship a compiling model **with the command to compile it**.

## 8. Testing

| Test | Assertion |
|---|---|
| `test_summary_sections.py` | All mandatory sections present, including "What this model does NOT cover" |
| `test_summary_length.py` | Under the one-minute budget (word-count proxy) |
| `test_every_element_traced.py` | Every IR element appears in `traceability.md` |
| `test_evidence_json_schema.py` | Validates against the published schema |
| `test_no_orphan_claims.py` | Every claim in the ledger resolves to an element or a stated rejection |
