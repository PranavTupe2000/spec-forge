# 12 — API Specification

**Status:** Baseline · **Module:** `src/spec_forge/api/` · **Stack:** FastAPI + Pydantic v2 + SQLAlchemy 2.x

---

## 1. Principles

- **Thin.** The API orchestrates and serves; it contains no extraction, precedence or emission logic. Every
  endpoint delegates to `pipeline/` (ADR-009).
- **Typed.** Request and response models are the same Pydantic models used inside the pipeline. OpenAPI is
  generated, and the frontend's TypeScript types are generated from it — one definition, three consumers.
- **Async.** Pipeline runs are background tasks; clients poll or subscribe to SSE.
- **Idempotent where it matters.** `POST /runs` accepts an `Idempotency-Key`.

Base path `/api/v1`. Errors use RFC 7807 `application/problem+json`.

## 2. Resources

| Resource | Meaning |
|---|---|
| `Project` | A workspace with sources, runs and persisted component bindings |
| `Source` | An uploaded file with ingest status |
| `Run` | One pipeline execution producing a versioned artifact set |
| `Artifact` | A file produced by a run |
| `Question` | An open question awaiting an answer |
| `Override` | A tier-0 user decision |

## 3. Endpoints

### Projects and sources

```
GET    /projects
POST   /projects                      {name, description}
GET    /projects/{id}
DELETE /projects/{id}

POST   /projects/{id}/sources         multipart upload, repeatable
GET    /projects/{id}/sources
GET    /sources/{id}
GET    /sources/{id}/fragments?limit&offset
GET    /sources/{id}/content          raw bytes, for the fragment viewer
GET    /sources/{id}/render?page&dpi  page render for PDFs and images
DELETE /sources/{id}
```

### Runs

```
POST   /projects/{id}/runs            {stages?, config?, replay_run_id?, seed?}  -> 202 {run_id}
GET    /runs/{id}
GET    /runs/{id}/events              SSE
POST   /runs/{id}/cancel
GET    /runs/{id}/ir                  the SFIR document
GET    /runs/{id}/evidence            the evidence ledger
GET    /runs/{id}/validation          all rule results
GET    /runs/{id}/artifacts
GET    /runs/{id}/artifacts/{name}
GET    /runs/{id}/export              zip of the run directory
GET    /runs/{id}/compile             {status, command, stdout, stderr, attempts}
GET    /runs/{id}/simulation          {status, signals, plots, deviation}
GET    /runs/{id}/diff/{other_id}     structural diff between two runs
```

### Questions and overrides

```
GET    /runs/{id}/questions
POST   /questions/{id}/answer         {answer, rationale?}       -> tier-0 override
POST   /runs/{id}/overrides           {json_patch, rationale}    -> re-validate + re-emit
GET    /projects/{id}/overrides       persisted across runs
```

### System

```
GET    /health        liveness
GET    /ready         readiness: db, omc, sysml toolchain, llm reachability
GET    /version       app version, git sha, schema versions, MSL version
```

`GET /ready` checks `omc --version` and the SysML toolchain. This is how *"bring the toolchain working"* becomes
observable rather than assumed — the demo operator opens `/ready` before the slot starts and sees green or red.

## 4. Run lifecycle

```
queued → ingesting → resolving_evidence → extracting → validating_ir
       → emitting_sysml → emitting_modelica → compiling → repairing?
       → simulating → reporting → completed
                                ↘ degraded   (partial output + gap report)
                                ↘ failed     (nothing emitted — should be rare)
                                ↘ cancelled
```

`degraded` is a **success-shaped** terminal state: artifacts exist, the gap is stated, HTTP 200. It is distinct
from `failed` precisely so a partial-but-honest result is not presented as an error (ADR-007).

## 5. Progress events (SSE)

`GET /runs/{id}/events`, `text/event-stream`, `Last-Event-ID` supported for resume.

```
event: stage_started
data: {"run_id":"01JD…","stage":"ingesting","ts":"…","seq":12}

event: progress
data: {"stage":"ingesting","message":"01_customer_URS.pdf (2/12)","pct":16,"seq":13}

event: diagnostic
data: {"severity":"warn","rule":"V-TOPO-005","message":"Part 'ambient1' has no connections","seq":41}

event: stage_completed
data: {"stage":"compiling","status":"ok","duration_ms":8412,"seq":88}

event: run_completed
data: {"status":"completed","artifacts":[…],"seq":91}
```

**Contract:** no more than **2 seconds** between events during an active run; the orchestrator emits a heartbeat
otherwise (SF-UX-03). `seq` is monotonic so a reconnecting client can replay without gaps.

## 6. Errors

```json
{
  "type": "https://specforge.dev/problems/blocking-question",
  "title": "Run halted on a blocking open question",
  "status": 409,
  "detail": "Cannot proceed: interlock conflict between V2 and V3 is unresolved.",
  "instance": "/runs/01JD…",
  "question_id": "oq:v2_v3_interlock",
  "partial_artifacts": ["model.sfir.json", "evidence.json", "summary.md"]
}
```

`partial_artifacts` is always populated where partial output exists. An error response that strands the user
with nothing violates SF-UX-04.

## 7. Auth and limits

Single-tenant demo: a static API key via `X-API-Key`, disabled by default for local use. Uploads capped at
50 MB per file and 200 MB per project. Rate limiting is applied to LLM-backed endpoints only. Real multi-tenant
auth is out of scope (`11_web_application_spec.md` §10).

## 8. CLI parity

Every capability is reachable without the API. The CLI is the reference client, and the pair is tested for
equivalence.

```
spec-forge run <path-or-case> [--stages …] [--replay RUN] [--seed N] [--no-manifest] [--out DIR]
spec-forge ingest <path>            spec-forge evidence <run>
spec-forge emit sysml|modelica <run>
spec-forge compile <run>            spec-forge simulate <run>
spec-forge bench [--cases L1,L2,L3,L4] [--repeat N]
spec-forge doctor                   # toolchain + env check, same probes as /ready
```

`spec-forge doctor` is the day-one command from the briefing's first instruction, and `bench --repeat 2` is the
repeatability harness for SF-ACC-05.

## 9. Testing

| Test | Assertion |
|---|---|
| `test_openapi_stable.py` | OpenAPI schema matches the committed snapshot |
| `test_sse_heartbeat.py` | No gap over 2 s during an active run |
| `test_degraded_returns_200.py` | A degraded run returns 200 with artifacts |
| `test_cli_api_parity.py` | CLI and API produce identical artifacts for the same input |
| `test_ready_detects_missing_omc.py` | `/ready` reports red when `omc` is absent |
