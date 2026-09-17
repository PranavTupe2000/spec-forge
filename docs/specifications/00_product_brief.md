# 00 — Product Brief and Hackathon Constraints

**Status:** Baseline · **Source:** AI-in-Engineering Hackathon Participant Briefing (13 slides) + PRD v0.1 (16 Sep 2026)
**Owner:** whole team · **Audience:** every coding agent and team member before touching code

This document is the non-negotiable frame. Everything else in `docs/` serves it. If a decision elsewhere
conflicts with this file, this file wins and the other document is wrong.

---

## 1. What we are building

**SpecForge** accepts mixed, unstructured, contradictory engineering inputs and produces a structured
system model expressed as **SysML v2 textual** plus a corresponding **executable Modelica model that
compiles and simulates**, with every generated element traced back to the input fragment or declared
assumption that justifies it.

The one-line framing from the briefing:

> Spec (natural language) → AI generate → SysML v2 (structure) → AI transform → Modelica (behaviour) → **Compiles (verified live)**

## 2. Hard constraints

| Constraint | Value | Consequence for us |
|---|---|---|
| Hard stop | **Wed 23 Sep 2026, 23:59** | Repos are snapshotted. Last commit. No extensions. |
| Evaluation | **Thu 24 – Fri 25 Sep**, 45 min per team | Fixed structure, see §5. |
| Effort budget | **12–15 focused hours per person**, 4 people, alongside regular work | ~50–60 team-hours total. |
| Compile gate | **The generated Modelica must compile**, checked live on a **judge-supplied spec** | Binary. No amount of explanation substitutes. |
| Toolchain | SysML v2 open-source toolchain; Modelica via **OpenModelica, verified with `omc`**; MSL encouraged | Set up day one. Tool friction sinks teams. |
| Daily commit | `DECISIONS.md` committed **every single day** from start date through 23 Sep, weekends included | A missed day is a missed day. Retro-added entries carry no weight. |

## 3. Scoring — 100 points + 5 stretch

| Bucket | Points | What earns it |
|---|---:|---|
| **Method** | **45** | Empathize 10 · Define 10 · Ideate 8 · Prototype discipline 7 · Test and Iterate 10 |
| **AI Collaboration** | **10** | Delegation judgment, rejection quality |
| **Outcome** | **45** | Functional depth, engineering soundness, domain correctness, scope judgment |
| Stretch bonus | +5 | Validated simulation results, traceable SysML→Modelica transformation, verification or parameter sweeps, round-trip consistency checks |

**55 points are for how we worked, 45 for what we built.** Both weigh the same because the next problem
will be different.

### 3.1 The Method gate

> If the individual probes show only **one member can explain the design**, Method is capped at **27 of 45**
> — whatever the artifacts look like.

This is an architectural requirement, not a soft suggestion. It is why the module boundaries in
`docs/design/ARCHITECTURE.md` are drawn so each stage is independently explainable, and why each
specification in this folder is written to be read standalone.

### 3.2 Method sub-criteria, verbatim intent

- **Empathize (10)** — You spoke to a domain expert and **something changed**: scope cut, problem reframed, assumption killed. *No visible delta, no marks.*
- **Define (10)** — The problem you ended with is sharper than the one you started with, and you can say what sharpened it.
- **Ideate (8)** — Real alternatives generated and **rejected for stated reasons**. One idea carried straight to build scores near zero.
- **Prototype discipline (7)** — Incremental commits, working slices early. Evidence you built to learn, not to finish.
- **Test and Iterate (10)** — Tested against something real — expert review, compile failures, adversarial specs — **and the results changed the build**.

> Failures documented honestly score higher than a clean story.

## 4. Submission — four things, nothing else is read

1. **Git repository** — created day one, everything lives here, with setup instructions.
2. **`DECISIONS.md`** — one commit a day, three lines, two minutes. Format: `D<n> | what we decided | why the alternative lost`.
3. **`AI-LOG.md`** — **minimum two documented cases** where we overrode, corrected or discarded AI output: what we did instead, and why. Both are examined live.
4. **8 slides maximum**, plus a live demo at the evaluation.

> The repo **must contain at least one generated Modelica model that compiles, together with the command to
> compile it. Judges run that command.**

No written report. See `14_acceptance_criteria_and_evaluation.md` for how each maps to our artifacts.

### 4.1 What scores well vs near zero in `AI-LOG.md`

| Scores well | Scores near zero |
|---|---|
| Three approaches generated, two killed for stated reasons | "We asked Claude, it worked." |
| Plausible-looking Modelica that would not compile | A log with no rejections in it |
| Invented library components you caught and replaced | Hiding AI use entirely |
| SysML that parsed but did not mean anything | Overrides you cannot explain when asked |

> The most valuable entries are the ones where the model was **confidently wrong**. Those are the ones judges will pick.

Using AI is **expected**. What is scored is judgment in using it. What is **not acceptable** is passing
AI-generated process history off as our own reasoning.

## 5. The evaluation — 45 minutes, fixed structure

| Minutes | Segment | What happens |
|---:|---|---|
| 5 | Judges read | Silent review of repo and commit sheet. We set up the demo. **No presenting.** |
| 10 | **Demo and compile check** | Live, uninterrupted. **Generate from a judge-supplied spec and run the compiler.** |
| 10 | **Decision walk** | Judges pick **three entries from `DECISIONS.md` — their choice** — and ask what the alternative was and why it lost. |
| 10 | Individual probes | **Each of the four** answers on a part of the work they did not build. |
| 10 | AI collaboration | Walk through our two override cases. |

- **Bring the toolchain working.** Setup comes out of our demo slot, and a compiler that will not start is a compile failure.
- **The repo is read cold, in five minutes.** A sprawling log is worse than a short one.

## 6. Fair play

- **Evidence beats narrative.** Every repo is snapshotted at the hard stop and a commit sheet generated — commits per day, lines changed, whether the log was actually committed. A process story that does not match the trail **scores zero on Method. Not partial credit.**
- **Judges may be your experts.** Each judge declares which teams interviewed them, and their Empathize score for those teams is dropped. Interviewing a judge confers no advantage.
- **Self-proposed problems** are accepted or rejected as submitted. *(Not applicable — we are on the supplied System Modelling track.)*

> The honest version of a messy week scores better than a clean invented one.

## 7. Prizes

First / Second / Third on total score. Two independent awards: **Best Process** (highest Method score in the
field) and **Boldest Exploration** (the team that travelled furthest from where it started).

## 8. Our committed scope

Recorded here because §5 will ask us to defend it. Full rationale in `docs/design/adr/`.

| Decision | Choice | ADR |
|---|---|---|
| Benchmark coverage | **All four levels, equal effort** | ADR-011 |
| Product surface | **Full SaaS** — FastAPI + React/ShadCN/R3F on top of a CLI-runnable core | ADR-009 |
| Input modalities | Text/documents + structured engineering artifacts + **images via vision** | ADR-003 |
| Target user | **Systems engineer** (PRD §4 requires us to state one) | ADR-010 |
| LLM | **Claude, Anthropic API** | ADR-002 |
| Persistence | **PostgreSQL from Phase 1** | ADR-008 |
| Phasing | **Strictly sequential**, per `.agents/workingrules.md` | ADR-012 |

## 9. The seven things the briefing told us to do

1. Set up the toolchain on day one — not day four. → Phase 0
2. Commit `DECISIONS.md` every single day. → daily ritual, non-negotiable
3. Talk to an expert early, and let it change something. → Empathize evidence
4. Kill your worse ideas in writing. → `DECISIONS.md` "why the alternative lost"
5. Scope to a subsystem you can actually finish. → Phase gating
6. **Make it compile.** → `omc` gate wired in Phase 1, never allowed to regress
7. Show us where the AI was wrong. → `AI-LOG.md`, maintained continuously, not on the 23rd
