# SpecForge Toolkit Development Environment Setup

> **Day one, not day four.** The briefing is explicit: *"Tool friction, not modelling, is what sinks teams in
> this domain"*, and *"a compiler that will not start is a compile failure."* Finish this document before
> writing pipeline code.

Use this checklist for onboarding a new developer.

1. Review the tech stack in `docs/design/ARCHITECTURE.md`.
2. Verify required tools are installed (compiler/interpreter/build tools/dependencies).
3. If anything is missing:
    - Ask whether it is already installed and where.
    - If not installed, guide setup of required software and packages.
4. Create `environment.bat` (Windows) or `environment.sh` (Unix) in the project root.
5. Ensure the environment file:
    - Adds required tool paths (e.g. compiler, build tool, testing tools).
    - Sets required environment variables.
    - Defines repository paths (root, source, test).
    - Includes any stack-specific best practices.
6. Do not commit the environment file; add it to version control ignore rules.

---

## 1. Required tools

| Tool | Version | Purpose | Verify |
|---|---|---|---|
| **Python** | 3.11+ | Backend | `python --version` |
| **uv** | latest | Python package manager | `uv --version` |
| **OpenModelica** | 1.22+ | **The compile gate** | `omc --version` |
| **SysML v2 toolchain** | pilot | SysML validation | see §3 |
| **Node.js** | 20+ | Frontend | `node --version` |
| **Docker Desktop** | latest | PostgreSQL | `docker --version` |
| **Git** | latest | Everything | `git --version` |
| **Java** | 17+ | SysML v2 toolchain, PlantUML | `java -version` |

Development and the live demo are on **Windows 11**. Keep every path `pathlib`-based and never assume a POSIX
shell (NFR-PORT-01).

## 2. OpenModelica — the critical dependency

Install from <https://openmodelica.org/download/>. The **Modelica Standard Library** ships with it.

**Windows.** The installer normally adds `omc` to `PATH`. If not, add `C:\Program Files\OpenModelica1.2x.x\bin`
and set `OPENMODELICA_HOME` to the install root. Never hardcode the path in source (NFR-PORT-03).

Verify the toolchain actually works, not just that the binary exists:

```bash
omc --version

# Full smoke test — run from the repo root
cat > /tmp/smoke.mo <<'MO'
model Smoke
  Real x(start = 0);
equation
  der(x) = 1;
end Smoke;
MO

cat > /tmp/smoke.mos <<'MOS'
loadModel(Modelica); getErrorString();
loadFile("/tmp/smoke.mo"); getErrorString();
checkModel(Smoke); getErrorString();
MOS

omc /tmp/smoke.mos
```

Expect `checkModel` to report the model checked with no errors. **If this does not work, stop and fix it before
anything else.**

## 3. SysML v2 toolchain

Install the pilot implementation from
<https://github.com/Systems-Modeling/SysML-v2-Release>. Requires Java 17+.

Either the Jupyter kernel or the API server is acceptable; `toolchain/sysml.py` wraps whichever is configured
via `SYSML_TOOL_CMD`. Verify by parsing a trivial model:

```sysml
package Smoke {
    part def Tank;
    part tank1 : Tank;
}
```

## 4. Project setup

```bash
git clone <repo-url>
cd spec-forge

# Python environment and dependencies
uv sync

# Environment variables
cp .env.example .env
#   ANTHROPIC_API_KEY=sk-ant-...
#   DATABASE_URL=postgresql+psycopg://specforge:specforge@localhost:5432/specforge
#   OPENMODELICA_HOME=...            (only if omc is not on PATH)
#   SYSML_TOOL_CMD=...

# PostgreSQL
docker compose up -d postgres
uv run spec-forge db upgrade

# Frontend
cd frontend && npm install && cd ..
```

**Never commit `.env`.** API keys come from the environment only, and are never logged or written into run
manifests (NFR-SEC-02).

## 5. Verify the environment

```bash
uv run spec-forge doctor
```

Checks Python version, `uv`, **`omc` liveness**, SysML toolchain, Postgres connectivity, `ANTHROPIC_API_KEY`
presence, MSL availability, and write access to `runs/` and `build/`.

**All green before you write code.** This same command runs in CI and is the first item on the pre-demo
checklist.

## 6. Run the pipeline

```bash
# One benchmark case, end to end
uv run spec-forge run test/testdata/benchmarks/L1_two_tank

# Compile the generated model — the command judges run
omc build/omc/check_TwoTankController.mos

# Full benchmark suite
uv run spec-forge bench

# Replay a previous run with no network calls
uv run spec-forge run --replay <run_id>
```

## 7. Development commands

```bash
uv run pytest                      # tests
uv run pytest --live               # include tests that call the API
uv run ruff check . && uv run ruff format .
uv run mypy src/spec_forge/core src/spec_forge/emit

uv run uvicorn spec_forge.api.app:app --reload   # API on :8000
cd frontend && npm run dev                        # UI on :5173
```

## 8. Environment file

Create `environment.bat` (Windows) or `environment.sh` (Unix) at the project root. **Do not commit it** — it is
in `.gitignore`.

`environment.bat`:

```bat
@echo off
set PROJECT_ROOT=%~dp0
set PYTHONPATH=%PROJECT_ROOT%src
set SPECFORGE_TEST_DATA=%PROJECT_ROOT%test\testdata
if not defined OPENMODELICA_HOME set OPENMODELICA_HOME=C:\Program Files\OpenModelica1.22.0-64bit
set PATH=%OPENMODELICA_HOME%\bin;%PATH%
echo Environment configured for SpecForge at %PROJECT_ROOT%
```

`environment.sh`:

```bash
#!/usr/bin/env bash
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PROJECT_ROOT/src"
export SPECFORGE_TEST_DATA="$PROJECT_ROOT/test/testdata"
export PATH="${OPENMODELICA_HOME:-/usr/bin}/bin:$PATH"
echo "Environment configured for SpecForge at $PROJECT_ROOT"
```

Chain it before commands, per `.agents/workingrules.md`:

```powershell
.\environment.bat && uv run pytest
```

```bash
source ./environment.sh && uv run pytest
```

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `omc: command not found` | Not on `PATH` | Add `%OPENMODELICA_HOME%\bin`; re-run `doctor` |
| `checkModel` fails on MSL classes | MSL not loaded | Ensure `loadModel(Modelica)` precedes `loadFile` |
| Postgres connection refused | Container not running | `docker compose up -d postgres` |
| `spec-forge` not found | Environment not synced | `uv sync`, then use `uv run spec-forge` |
| Anthropic 401 | Key missing or stale | Check `.env`; never commit it |
| PDF yields no text | Image-only PDF | Expected — the vision fallback handles it (`04_ingestion_spec.md` §4.1) |
| Tests slow or flaky | Hitting the live API | Default is recorded fixtures; drop `--live` |
