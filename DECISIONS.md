# DECISIONS

Daily decision log. **One commit every day from the start date through 23 September, weekend included.**

**Format:** `D<n> | what we decided | why the alternative lost`

## Rules

- Two minutes a day. Three lines. Do not write an essay.
- **Log what you killed.** Discarded options are the entries judges pick to question.
- **Timestamps are the evidence.** Retro-added entries show in the git log and carry no weight.
- A missed day is a missed day. There is no making it up.
- At the evaluation, judges pick **three entries — their choice** — and ask what the alternative was and why it
  lost. Every entry must be defensible by **any** team member, not only its author.

---

## Log

<!--
Append below. Newest at the bottom. Example of the expected shape:

D1 | Scoped to the four supplied benchmark cases, no self-proposed problem
   | Self-proposed needed a reachable in-house stakeholder we did not have inside the week

D2 | Extraction into a typed schema + deterministic emitters, not end-to-end LLM generation
   | End-to-end generation makes SysML and Modelica diverge silently; the PRD names this as the common failure

D3 | Dropped rule-based SysML emitter for LLM generation
   | Emitter failed on 4/10 sample specs
-->

D1 | workingrules.md's docs/-edit lock does not apply to `docs/design/sourcemap.md` and `docs/design/packagedesign.md` — both are updated automatically as a routine part of adding a source file or package, no per-edit approval
   | A blanket "ask every time" gate loses because ARCHITECTURE.md requires these two files to be updated on every single new source file; that would mean a permission round-trip per file for the whole build

D2 | `spec-forge doctor` (P0.2) checks only that `ANTHROPIC_API_KEY` is set, not that the Anthropic API actually responds
   | A live liveness ping lost on cost and latency for a check run on every invocation; a bad key surfaces immediately on the first real extraction call regardless, so the ping buys nothing a presence check doesn't already cover — deliberate, not an oversight, despite ADR-002 pinning Claude as sole provider with no fallback

D3 | PRD §8's "how is agentic behaviour used" row corrected to say repair + clarification are the two agentic nodes, not extraction + conflict adjudication + repair
   | The original wording lost because it contradicted its own cited source: ADR-004 defines "agentic" strictly as a looping node and enforces exactly two (repair, clarification) via `test_agent_count.py`; extraction and conflict adjudication are single schema-constrained LLM calls, not agents

D4 | Start date for the daily decision-log rule is today, 2026-09-17 — matches the repo's actual first commit (d279f84), so no backfill is needed
   | Anchoring to "PRD date" or "kickoff meeting" lost because neither is written down anywhere as an actual date; the first commit is the only unambiguous timestamp that exists

D5 | pyproject.toml declares no third-party runtime deps yet — added incrementally per phase as each module first imports one, not the full ARCHITECTURE.md stack today
   | Pre-declaring everything now lost on the counter-argument that nothing beyond `__init__.py` exists yet to conflict; better to surface a dependency clash the day a module actually needs the package

D6 | mypy strictness (NFR-MNT-04) is scoped via `[[tool.mypy.overrides]]` to `core.*`/`emit.*`, with a non-strict-but-annotated baseline everywhere else
   | A blanket `--strict` across the whole tree lost — it would block every file outside core/emit from type-checking at all until fully strict-typed, which the spec never asked for

D7 | Data-only leaf dirs (`library/archetypes/`, `library/local/`, both `templates/` dirs, `pipeline/prompts/`) stay plain `.gitkeep`'d dirs, not `__init__.py` packages; `emit/modelica/strategies/` does get one
   | Turning data dirs into importable packages lost — sourcemap.md already calls them "data, not code," and an empty Python package there would misrepresent what's inside

D8 | Cross-cutting rule-enforcement tests (`test_layer_dependencies.py`, and future ones like it) live under `test/unit/architecture/`
   | AGENTS.md's flat `test/unit/test_no_case_specific_logic.py` example lost — that directory was already pre-scaffolded for exactly this purpose, mirroring the one-dir-per-package pattern used everywhere else in `test/unit/`

D9 | omc's compile-gate success/failure is read entirely from parsed stdout, never omc's own process exit code
   | Trusting the exit code lost — confirmed empirically it stays 0 even when `checkModel` fails outright (missing class, syntax error); a return-code check would have shipped a gate that always says green

D10 | `doctor` scores `omc` and the SysML toolchain as equally blocking (`error`), Postgres and the Anthropic key as `warn`
    | Treating all checks as equally blocking lost — A7 requires the pipeline to run without the DB, and Postgres/`.env` aren't wired up yet (Phase 0 item 5); failing doctor on them would be a false red

D11 | SysML v2 toolchain: installed conda-forge's `jupyter-sysml-kernel`, wrapped via a hand-built probe-notebook + `nbconvert --execute`
    | The "primary" `SysML-v2-Pilot-Implementation` repo lost — it turned out to be an Eclipse RCP GUI plugin with no headless CLI at all, unusable from a subprocess wrapper

D12 | `environment.bat`/`.sh` force `JAVA_HOME` to the conda env's own JDK, ahead of system Java, before running the SysML kernel
    | Leaving PATH as-is lost — the kernelspec invokes a bare `java` with no version pin of its own, silently picked up the pre-existing system Java 17, and failed with `UnsupportedClassVersionError` (needs 21+)

D13 | `spec-forge db upgrade` treats a failed migration as a hard stop (`MigrationError`, non-zero exit), not a reportable status
    | Degrade-and-continue (matching toolchain liveness checks) lost — a half-applied schema is not a state the CLI should shrug off and keep going; the command must fail loudly, not report "degraded" and proceed

D14 | CI's daily-decisions job pins `TZ: Asia/Kolkata` rather than writing timezone-conversion logic into `check_decisions_daily.py`
    | Converting each commit's recorded offset to UTC in the script lost — the runner's own clock matching the team's calendar day is simpler, and it's what a human reading `git log` would assume "today" means anyway

D15 | CI provisions the real toolchain (`omc` + the SysML kernel) so `spec-forge doctor`'s exit code genuinely gates the `test` job
    | A non-blocking `doctor` step (`continue-on-error`) lost — `doctor` already scores both toolchains as equally blocking (D10); letting CI wave that through would make the local hard gate meaningless in CI, the one place a regression should be caught before it reaches a teammate

D16 | CI's OpenModelica step pre-installs MSL via `libraries: 'Modelica 4.1.0+maint.om'`, and the SysML env vars use `$CONDA_PREFIX` directly, not `$CONDA_PREFIX/envs/sysml`
    | Assuming Windows-installer parity (MSL bundled) and assuming `$CONDA_PREFIX` meant the miniconda root both lost — apt-installed `omc` ships no MSL, and `activate-environment: sysml` already makes `$CONDA_PREFIX` the activated env's own path; only a real Actions run caught either (AI-LOG A1)
