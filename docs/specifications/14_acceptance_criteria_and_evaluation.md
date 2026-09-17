# 14 — Acceptance Criteria and Evaluation Readiness

**Status:** Baseline · **Sources:** PRD §8, §11 · Participant Briefing (scoring, submission, evaluation)
**Purpose:** the definition of done, and the checklist we run before the demo slot.

---

## 1. Definition of done

A phase is done when its acceptance tests pass **in CI**, not when the code exists. Every criterion below has an
automated test; `spec-forge bench` is the single command that runs the lot.

## 2. Speed (PRD §8.1)

| ID | Stage | Target | Test |
|---|---|---|---|
| SF-SPD-01 | First structural draft from text | < 2 min | `test_speed_first_draft.py` |
| SF-SPD-02 | Full pipeline to compiling Modelica, one case | < 10 min | `test_speed_full_pipeline.py` per case |
| SF-SPD-03 | Live demo end to end | Within the slot, normal laptop | Rehearsal, §8 |

Measured wall-clock on a normal laptop with standard API access. Timings recorded per run in `manifest.json` and
trended by `spec-forge bench`.

> Latency from genuine reasoning or self-correction is acceptable. **Silence is not.** SF-UX-03 (≤2 s between
> progress events) is therefore an acceptance criterion in its own right, tested by `test_sse_heartbeat.py`.

## 3. Accuracy (PRD §8.2)

| ID | Dimension | Target | Test |
|---|---|---|---|
| SF-ACC-01 | Structural correctness | **≥80% element coverage on L1 and L2** vs the reference element set | `test_structural_coverage.py` |
| SF-ACC-02 | **Compilability** | `omc checkModel` passes. **Hard gate.** | `test_compiles_*.py` |
| SF-ACC-03 | Simulatability | L1 and L2 run and produce plausible trajectories | `test_simulate_l1_l2.py` |
| SF-ACC-04 | Behavioural correctness | Required states reachable; forbidden combinations prevented | `test_behaviour_*.py` (`V-BEH-002`, `V-BEH-004`) |
| SF-ACC-05 | Repeatability | Same input twice → **structurally equivalent** model | `spec-forge bench --repeat 2` |
| SF-ACC-06 | Honesty | Every element traces to a fragment or declared assumption | `V-TRACE-001` in CI |

### 3.1 Measuring structural coverage

Per case, `test/testdata/expected/<case>/elements.yaml` lists the reference parts, ports and connections with
their accepted aliases. Coverage is computed after alias-aware matching:

```
coverage = |matched reference elements| / |reference elements|
precision = |matched generated elements| / |generated elements|
```

Both are reported. Precision matters as much as coverage here: inventing extra parts would inflate a
coverage-only score while violating SF-IN-03, so a fabricated element is penalised twice — once by precision and
once by `V-TRACE-001` refusing to emit it.

### 3.2 Repeatability

Structural equivalence = identical part/port/connection multiset after canonical renaming. **Naming variation is
acceptable; topology variation is not.** Failures print the structural diff.

## 4. Scope (PRD §8.3)

| ID | Criterion | Evidence |
|---|---|---|
| SF-SCP-01 | **No case-specific logic in `src/`** | `test_no_case_specific_logic.py` greps for case identifiers, tags and bundle filenames in source; the allowlist is `library/` data and `test/` |
| SF-SCP-02 | Every case runs without its manifest | `--no-manifest` run in CI |
| SF-SCP-03 | Depth over breadth per modality | Vision path tested on all four reference diagrams |

SF-SCP-01 is the mechanical form of *"If your pipeline contains logic that only fires for the two-tank problem,
say so, because judges will look."* We would rather the test fail loudly in CI than have a judge find it. If a
case-specific shortcut ever becomes necessary, the test is updated **and the exception is declared in
`DECISIONS.md`** — visible, not hidden.

## 5. Honesty criteria — the PRD's differentiator

> A model that is partially complete and honest about its gaps scores above one that is superficially complete
> and quietly wrong. **This is deliberate.**

| Criterion | Test |
|---|---|
| Every element traceable | `V-TRACE-001`, blocking |
| No assumed components | `V-TRACE-002`, blocking |
| Assumptions from the catalogue only | `V-TRACE-003`, blocking |
| Contradictions flagged with all positions retained | `test_expected_conflicts.py` per case |
| Missing information inferred-with-assumption **or** surfaced as a question, never invented | `test_no_silent_defaults.py` |
| Summary states what the model does **not** cover | `test_summary_sections.py` |

`test_expected_conflicts.py` asserts the specific conflicts listed in `05_evidence_precedence_spec.md` §6.1 are
found, **and** that the non-conflicts (L3's nominal-vs-as-built gap, L4's medium variants) are *not* reported as
conflicts. Both directions are failures.

## 6. Submission readiness — the four things

| # | Item | Location | Check |
|---|---|---|---|
| 1 | Git repository with setup instructions | repo root, `README.md`, `docs/devenv.md` | `test_readme_setup_works.py` on a clean clone |
| 2 | `DECISIONS.md` | repo root | **One commit per day, every day, through 23 Sep.** Verified by `scripts/check_decisions_daily.py` in CI |
| 3 | `AI-LOG.md` | repo root | **≥2 documented override cases.** Verified by `scripts/check_ai_log.py` |
| 4 | 8 slides + live demo | `docs/submission/` | Rehearsed, §8 |
| — | **A compiling Modelica model + the command** | `runs/*/Model.mo`, `COMPILE.md` | `test_compile_command_present.py` |

The daily-commit check runs in CI from day one because the briefing is explicit that retro-added entries show in
the git log and carry no weight. A failing check on the morning of day 3 is recoverable; discovering the gap on
the 23rd is not.

## 7. Evaluation preparation

### 7.1 Demo and compile check (10 min) — judges supply the spec

This is the highest-risk segment. Preparation:

- **`spec-forge doctor` green before the slot**, and `/ready` green in the browser.
- A **paste-a-spec** path in the UI and `spec-forge run --text` in the CLI. The judge-supplied spec will be
  prose, not a bundle — the text path must be the smoothest one, not an afterthought.
- The `omc` command visible on screen; the judge can run it themselves.
- **Fallback ladder, decided in advance:** live run → `--replay` of a rehearsed case with the network down →
  pre-generated artifacts opened from disk. Which fallback we are on is stated out loud, not concealed.
- Degradation is a feature to show, not an embarrassment: if the judge's spec is underspecified, the open
  questions and assumption list are exactly what the product is for.

### 7.2 Decision walk (10 min)

Judges pick **three `DECISIONS.md` entries — their choice** — and ask what the alternative was and why it lost.
Every entry must therefore be defensible by any team member. Entries name the alternative and the reason it was
rejected, as the briefing's format requires.

### 7.3 Individual probes (10 min) — the Method cap

**Each of the four answers on a part they did not build.** If only one member can explain the design, Method
caps at 27/45.

Mitigation is structural, and it is why the spec set is written the way it is:

- one spec per subsystem, readable standalone;
- a weekly rotation where each member walks another member's subsystem;
- `docs/design/ARCHITECTURE.md` and the ADR set are shared reading, not the author's private notes.

### 7.4 AI collaboration (10 min)

Walk through two override cases from `AI-LOG.md`. The best candidates are recorded as they happen:

- an invented MSL component caught by `test_modelica_bindings.py`;
- plausible Modelica that failed `omc`, and what the repair loop did about it;
- SysML that parsed but carried no units, caught by `V-UNIT-001`;
- an extraction that took the stale legacy value over the approved change record, and the precedence rule that
  fixed it.

## 8. Pre-demo checklist

Run the day before and again the morning of.

```
[ ] spec-forge doctor                      → all green
[ ] omc --version                          → prints
[ ] spec-forge bench --cases L1,L2,L3,L4   → compile gate green on all four
[ ] spec-forge bench --repeat 2            → structurally equivalent
[ ] docker compose up && /ready            → green
[ ] Playwright smoke                       → passes
[ ] --replay of each case with network off → produces artifacts
[ ] DECISIONS.md committed today
[ ] AI-LOG.md has ≥2 cases
[ ] 8 slides final
[ ] Each member can walk one subsystem they did not build
[ ] Laptop: charger, no OS updates pending, screen mirroring tested
```
