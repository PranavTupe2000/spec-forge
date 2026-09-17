# 11 — Web Application Specification

**Status:** Baseline · **Decision:** ADR-009 · **Module:** `frontend/`
**Stack:** React + Vite + TypeScript, React Router, ShadCN/ui + Tailwind, React Three Fiber + Three.js

---

## 1. Purpose and the constraint on it

The PRD prefers SaaS, and design thinking is explicitly scored: *"Who the product is for, how ambiguity is
surfaced to the user, and whether an engineer would actually trust and use it."* The UI is where ambiguity
becomes visible, so it carries real scoring weight rather than being decoration.

**Constraint (ADR-009):** the web app is a **client of the pipeline, never a participant in it.** Every artifact
is produced by the CLI-runnable core. If the frontend fails entirely, `spec-forge run <case>` still produces
every deliverable and the compile gate still passes. This is deliberate: the live demo's 10 minutes include a
compile check, and no UI defect may be able to cost us that gate.

## 2. Information architecture

```
/                          Projects
/projects/:id              Project — runs, sources, settings
/projects/:id/ingest       Upload and ingestion progress
/runs/:runId               Run overview  ← the primary screen
/runs/:runId/evidence      Evidence ledger and precedence
/runs/:runId/model         Model explorer (tree + graph + 3D)
/runs/:runId/questions     Clarifying dialogue
/runs/:runId/artifacts     SysML / Modelica / summary / downloads
/runs/:runId/simulation    Plots and reference comparison
```

## 3. Run overview — the primary screen

Mirrors `summary.md` §2 and leads with the same honest headline.

- **Status strip** — pipeline stages with live state: Ingest → Evidence → Extract → Validate → Emit → Compile →
  Simulate. Compile shows a **prominent green/red gate** with the `omc` command and a copy button.
- **Coverage card** — evidence vs assumption split as the largest number on the page.
- **Three attention cards** — Conflicts, Assumptions, Open questions, each with count and one-click drill-down.
  These are given the same visual weight as the model itself; the point of the product is that they are not
  footnotes.
- **Model preview** — part/port/connection counts, top-level tree.
- **Artifacts** — download buttons, per-file.

## 4. Progress streaming

Server-Sent Events (`12_api_spec.md` §5). Every stage emits start/progress/complete events with a message and
percentage; per-file progress during ingestion; per-attempt progress during repair.

> *"Latency that comes from genuine multi-step reasoning or self-correction is acceptable and will not be
> penalised on its own. **Silence with no progress indication will be.**"*

Requirement **SF-UX-03**: no pipeline stage may run more than **2 seconds** without emitting an event. Enforced
by a watchdog in the orchestrator that emits a heartbeat, so a slow LLM call still shows life.

## 5. Evidence view

The screen that distinguishes this product. Available **as soon as ingestion completes**, before a model exists,
because deciding which documents are authoritative is itself engineering work the tool should show its working on.

- **Document table** — ranked by authority tier, with revision, status, date, reliability, fragment count.
  Superseded and archived documents are visibly demoted rather than hidden, so the user can see that the legacy
  `.mo` was considered and outranked.
- **Claim inspector** — pick an attribute, see every candidate value with its authority, date and citation, the
  rule applied, and which won.
- **Conflict cards** — all positions side by side, the winner marked, the rule named, an **Override** action that
  writes a tier-0 user decision.
- **Fragment viewer** — verbatim source text with locator; for PDFs and images, the page render with the bbox
  highlighted.

## 6. Model explorer

Three synchronised views over one selection model. Selecting an element anywhere selects it everywhere,
including its source fragments.

| View | Library | Shows |
|---|---|---|
| **Tree** | ShadCN | Part hierarchy, ports, attributes, provenance badge per row |
| **Graph** | React Flow | Parts as nodes, connections as typed edges, colour-coded by medium |
| **3D** | React Three Fiber | Spatial layout where the input provides coordinates |

### 6.1 Scope limit on the 3D view

R3F renders a **schematic block layout**, not CAD geometry. It is used where the inputs actually contain spatial
data — L4's `12_layout_coordinates.json` and L2's `12_bim_room_export.json` — and falls back to an auto-laid-out
schematic otherwise.

Stated plainly because scope judgment is scored: a 3D view that invents geometry the documents do not contain
would violate SF-IN-03 as surely as an invented component. The 3D view therefore renders **placement**, never
**shape**, and labels itself as schematic.

### 6.2 Provenance affordance

Every element in every view carries a provenance badge — `evidence` / `assumption` / `derived` / `user` — with
its confidence. Hovering shows the citation; clicking opens the fragment. **An element with no provenance cannot
render, because it cannot exist** (`V-TRACE-001`).

## 7. Clarifying dialogue (SF-EXT-02)

Open questions become a focused queue, ordered blocking-first:

- the question, why it matters, and what it gates;
- candidate answers pre-filled from losing conflict positions, so answering is usually one click;
- a free-text option;
- "proceed with the stated default" — always visible, always explicit about what the default is.

Answers are stored at **tier 0** and persist across re-runs of the project (`13_data_model_spec.md`), so the
engineer answers each question once, not once per run.

## 8. Round-trip editing (SF-EXT-06)

Editable: attribute values, part and port names, archetype binding, connection endpoints, assumption
accept/reject. Each edit becomes a JSON Patch at tier 0, triggers incremental re-validation and re-emission, and
appears in the traceability record as a user override with author and timestamp. Edit history is visible and
revertible — a correction must never silently become indistinguishable from extracted evidence.

## 9. Non-functional

| Requirement | Target |
|---|---|
| First paint | < 1.5 s |
| Reconnect after SSE drop | Automatic, resume from last event id |
| Dark mode | Supported (ShadCN theming) |
| Responsive | Usable at 1280 px and above; mobile out of scope |
| Accessibility | Keyboard navigable; status conveyed by text and icon, never colour alone |

The colour rule matters for the compile gate specifically: green/red is the most important signal on the page
and must also read as "COMPILES ✓" / "FAILED ✗" in text.

## 10. Out of scope

Real-time multi-user collaboration · authentication beyond a single-tenant demo user · mobile · in-browser
Modelica editing · CAD import.

## 11. Testing

| Test | Assertion |
|---|---|
| `test_no_pipeline_logic_in_frontend` | No extraction, precedence or emission logic exists in `frontend/` |
| Vitest component tests | Conflict card, assumption list, provenance badge render correctly |
| Playwright smoke | Upload L1 bundle → run → compile gate green → download artifacts |
| `test_cli_without_frontend` | Full pipeline succeeds with the frontend absent |
