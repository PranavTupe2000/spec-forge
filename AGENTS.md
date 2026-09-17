# Instructions for Coding Agents for SpecForge Toolkit

## About SpecForge Toolkit
SpecForge Toolkit turns messy engineering inputs — prose specs, sketches, datasheets, requirement tables — into structured, trustworthy system models. It generates a single source-of-truth representation that drives both a SysML v2 model and a compiling, simulatable Modelica model, keeping them in sync. Every generated element is traced back to its source input or flagged as an assumption, so engineers can review and trust it in minutes, not days.

## Working Rules
Read and strictly follow the working rules defined in `.agents/workingrules.md`

## Path Rules
- All paths in this `AGENTS.md` are resolved relative to the directory containing `AGENTS.md`.
- Skill files (SKILL.md) resolve paths relative to their own directory.
- Scripts referenced inside a skill must use SKILL.md file relative paths (e.g., `scripts/resize.py`).
- Skills are self‑contained: scripts should normally live inside the `<skill>/scripts` directory.

## Project Folder Map
In case folder does not exist, Create the neccessary folder as needed.
Create subfolders as needed when folder is marked with $SUBFOLDERS_AS_NEEDED.

- `.agents/` : Coding Agent configuration files. Including the SKILL files. $SUBFOLDERS_AS_NEEDED
- `docs/`: project documentation
- `docs/devenv.md` : instructions to setup the development environment for the new developer
- `docs/specifications/`: requirements and specs
- `docs/specifications/specindex.md`: index of specification documents
- `docs/specifications/benchmarks/` : per-case analysis of the four supplied benchmark problems (L1–L4).
- `docs/design/`: architecture and design decisions
- `docs/design/ARCHITECTURE.md`: architecture rules and constraints
- `docs/design/ADR.md`: architecture decision records — index
- `docs/design/adr/` : the individual Architecture Decision Records.
- `docs/design/packagedesign.md` : package/module design and dependency diagrams (mermaid.js).
- `docs/design/sourcemap.md` : list of source files and their purpose.
- `docs/implementation_plan.md` : Phase wise implementation plan of this project.
- `docs/submission/` : the 8 submission slides and demo material. $SUBFOLDERS_AS_NEEDED
- `build/` : built tool configuration files and any temporary files generated during the compilation and build process. $SUBFOLDERS_AS_NEEDED
- `src/`: application code
- `src/spec_forge/` : main application source code. **Underscore, not hyphen — a hyphen is not a legal Python package name. See ADR-014.** $SUBFOLDERS_AS_NEEDED
- `frontend/` : React SaaS client. Depends on the API contract only, never on Python modules. $SUBFOLDERS_AS_NEEDED
- `runs/` : per-run generated artifacts (IR, SysML, Modelica, evidence, reports, plots). Gitignored except retained demo runs.
- `test` : information, plans, test source code, test data etc.
- `test/plans` : test plans are stored in this folder. $SUBFOLDERS_AS_NEEDED
- `test/unit` : unit tests source code. $SUBFOLDERS_AS_NEEDED
- `test/testdata` : all neccessary test data required for unit or integration tests. $SUBFOLDERS_AS_NEEDED
- `test/testdata/benchmarks/` : the four supplied benchmark bundles (L1–L4), each with a `manifest.yaml`.
- `test/testdata/expected/` : expected elements, conflicts and parameters per benchmark case.

## Submission artifacts — do not delete or rewrite without instruction
- `DECISIONS.md` : the daily decision log. One entry per day, format `D<n> | what we decided | why the alternative lost`. Judges pick three entries at random and ask about them.
- `AI-LOG.md` : documented cases where AI output was overridden, corrected or discarded. Minimum two.

Both are scored submission artifacts. Append to them; never reconstruct them retrospectively.

## Required Reading Before Making Any Changes
- Read Coding Agent configuration files from `.agents`
- Read SKILL files as needed from `.agents/skills`.
- Read your memories from `.agents/memory` folder
- Read `docs/implementation_plan.md` to understant the planned roadmap and timeline
- Read `docs/specifications/specindex.md`, then all relevant specification files as needed.
- Follow `docs/design/ARCHITECTURE.md`.
- Follow decisions in `docs/design/ADR.md`.

### Minimum reading for any code change
1. `docs/specifications/00_product_brief.md` — the constraints that override everything else.
2. `docs/specifications/03_system_ir_spec.md` — every module is defined in terms of the IR.
3. `docs/design/ARCHITECTURE.md` — the layer rules and the eight architecture rules (A1–A8).
4. The specification for the subsystem you are changing, per `specindex.md`.

## Architecture rules that must never be violated
These are restated from `docs/design/ARCHITECTURE.md` because breaking one invalidates the design rather than
introducing a bug. Each has a test.

- **A1** Emitters read only a validated IR — never raw files, fragments or LLM output.
- **A2** Emitters never infer. A missing value is an upstream defect, not a template default.
- **A3** No LLM call in `emit/` or `validate/`.
- **A4** **No case-specific logic in `src/`.** No benchmark name, tag or bundle filename may appear in source.
- **A5** Repairs patch the IR, never the emitted text.
- **A6** Every IR entity carries provenance, or it cannot serialise.
- **A7** The pipeline runs without the API, the frontend, or the database.
- **A8** Domain knowledge lives in `library/` data, never in control flow.

If a task appears to require breaking one of these, stop and ask. Do not work around it.
