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

*No entries yet. Add the first as soon as an override occurs.*
