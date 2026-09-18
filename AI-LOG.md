# AI-LOG

Where we overrode, corrected or discarded AI output — what we did instead, and why.

**Minimum two documented cases. Both are examined live**, for ten minutes, at the evaluation.

## What belongs here

Using AI is expected — Claude, ChatGPT, Copilot, whatever works. What is scored is **judgment in using it**:
where we delegated, where we overrode the output, where we threw it away.

| Scores well | Scores near zero |
|---|---|
| Three approaches generated, two killed for stated reasons | "We asked Claude, it worked." |
| Plausible-looking Modelica that would not compile | A log with no rejections in it |
| Invented library components you caught and replaced | Hiding AI use entirely |
| SysML that parsed but did not mean anything | Overrides you cannot explain when asked |

> **The most valuable entries are the ones where the model was confidently wrong.** Those are the ones judges
> will pick.

Passing AI-generated process history off as our own reasoning is not acceptable.

## Rules

- **Write the entry when it happens**, not on the 23rd. A reconstructed log reads like one.
- Record the wrong output verbatim. "It got the units wrong" is not evidence; the actual wrong output is.
- Say what we did instead, and why that was better.
- Anyone on the team must be able to walk any entry.

## Entry template

```markdown
### A<n> — <one-line title>

**Date:** YYYY-MM-DD · **Where:** module / pipeline stage · **Model:** claude-opus-5 / claude-sonnet-5

**What we asked for**
<the task, and why we delegated it>

**What it produced**
<verbatim output or a faithful excerpt — the wrong part, not a paraphrase>

**Why it was wrong**
<the specific defect, and how we found it: a test, the compiler, a review, a run>

**What we did instead**
<the replacement, and why it was better>

**What changed in the build**
<the code, test, prompt or spec that changed as a result — this is the Test-and-Iterate evidence>
```

---

## Entries

<!--
Candidate sources, based on where we expect the model to be confidently wrong:

- test_modelica_bindings.py catching an invented MSL component
- omc rejecting plausible-looking Modelica, and what the repair loop did
- V-UNIT-001 catching SysML that parsed but carried no units
- An extraction pass taking the stale legacy value over the approved change record
- A vision pass reporting a diagram element that is not in the drawing

Write each one the day it happens.
-->

### A1 — CI workflow was confidently wrong in two ways only a real run caught

**Date:** 2026-09-18 · **Where:** `.github/workflows/ci.yml` (Phase 0 item 7) · **Model:** claude-sonnet-5

**What we asked for**
GitHub Actions CI that provisions the real `omc` and SysML v2 toolchain (not mocked), so
`spec-forge doctor`'s exit code genuinely gates the job — matching how `doctor` already treats both
as equally blocking (D10). Delegated because it's a large, mechanical provisioning task following
documented, standard actions. Flagged up front, before any run, as unverifiable from this session:
no way to trigger or observe a real GitHub Actions run without pushing.

**What it produced**
Two confidently-wrong fragments, both plausible, both actionlint-clean:

```yaml
- name: Install OpenModelica
  uses: OpenModelica/setup-openmodelica@v1.0
  with:
    version: "stable"
    architecture: "64"
    packages: |
      'omc'
```
— no `libraries:` input, silently assuming MSL would already be present.

```bash
echo "$CONDA_PREFIX/envs/sysml/bin" >> "$GITHUB_PATH"
echo "JAVA_HOME=$CONDA_PREFIX/envs/sysml" >> "$GITHUB_ENV"
```
— assuming `$CONDA_PREFIX` was the miniconda root, appended after `activate-environment: sysml`.

**Why it was wrong**
Caught only by the first real Actions run (35325813950) — `actionlint` checks YAML/expression syntax,
not the runtime semantics of third-party actions, so it passed clean on both mistakes.

1. Unlike the Windows installer, `apt install omc` does not bundle the Modelica Standard Library.
   `test_check_compiles_hand_written_smoke_model` failed outright:
   `AssertionError: expected a clean compile, got diagnostics: [...'Failed to load package Modelica
   (default) using MODELICAPATH /home/runner/.openmodelica/libraries/.']`
2. `$CONDA_PREFIX` after `activate-environment: sysml` is already the activated env's own path —
   `$CONDA_PREFIX/envs/sysml/bin` was a doubly-nested path that doesn't exist. This one didn't error
   loudly: `jupyter` just never resolved, so all three real-SysML-kernel tests silently skipped at
   collection (`3 skipped` in the pytest summary) instead of failing. Found by noticing the skip
   count didn't match the 0-skipped local baseline and reasoning through conda's activation
   semantics, not from a direct error message.

**What we did instead**
Added `libraries: |` / `'Modelica 4.1.0+maint.om'` to the OpenModelica step — the exact version
string came from `omc`'s own error message ("You can install the requested package using...
installPackage(Modelica, \"4.1.0+maint.om\"...)"), not a guess. Changed
`$CONDA_PREFIX/envs/sysml/bin` → `$CONDA_PREFIX/bin` and `JAVA_HOME=$CONDA_PREFIX/envs/sysml` →
`JAVA_HOME=$CONDA_PREFIX`.

**What changed in the build**
`.github/workflows/ci.yml` (commit `d5ba586`), re-verified by pushing and watching a second real
run (35327513845) go fully green across both jobs — including `pytest`, `spec-forge db upgrade` and
`spec-forge doctor`, none of which had ever passed on a real runner before. `DECISIONS.md` D16.
