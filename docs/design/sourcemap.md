# Index of source code for SpecForge Toolkit

## Index format is
- `<relative filepath from src>` : purpose of the source file.

## How to use this file
- Use this file to determine which source code file to load based "purpose" of the source code file
- Do not load all source code documents every time.
- Update the index whenever you add a new source code file.

---

## Status

**No source files exist yet.** The directory skeleton is in place; implementation begins at Phase 0
(`docs/implementation_plan.md`).

The table below is the **planned** allocation — where each responsibility belongs when it is written. Use it to
decide where a new file goes. **When you create a file, move its row into the Sourcemap Index below and give it
the real purpose from its Purpose comment.**

## Planned module allocation

| Path | Responsibility | Phase | Spec |
|---|---|---|---|
| `main.py` | Application entry point | 0 | ARCHITECTURE |
| `spec_forge/core/ir/` | Pydantic IR models — part, port, connection, attribute, state machine, constraint, requirement, provenance, assumption, conflict, open question, trace, document | 1 | `03` |
| `spec_forge/core/units.py` | pint registry and dimensional helpers | 1 | `03` |
| `spec_forge/core/ids.py` | Deterministic id generation | 1 | `03` §3 |
| `spec_forge/core/schema.py` | JSON Schema export for frontend and CI | 1 | `03` |
| `spec_forge/ingest/dispatch.py` | Content sniff → loader selection | 1 | `04` §3 |
| `spec_forge/ingest/loaders/` | One module per file type | 1–2 | `04` §4 |
| `spec_forge/ingest/vision.py` | Claude vision with structured output | 2 | `04` §4.9 |
| `spec_forge/ingest/aliases.py` | Alias harvesting and resolution | 2 | `04` §7 |
| `spec_forge/ingest/cache.py` | Content-addressed ingest cache | 1 | `04` §6 |
| `spec_forge/ingest/manifest.py` | Case manifest loading (test fixtures only) | 1 | `04` §8 |
| `spec_forge/evidence/tiers.py` | The 12-tier authority model | 2 | `05` §2 |
| `spec_forge/evidence/transmission.py` | Authority-of-record detection | 2 | `05` §3 |
| `spec_forge/evidence/precedence.py` | `PRE-01` resolution algorithm | 2 | `05` §4 |
| `spec_forge/evidence/conflicts.py` | Conflict construction and severity | 2 | `05` §6 |
| `spec_forge/evidence/assumptions.py` | Assumption creation, catalogue enforcement | 2 | `05` §7 |
| `spec_forge/evidence/standard_assumptions.yaml` | The catalogue — **data, not code** | 2 | `05` §7.2 |
| `spec_forge/evidence/questions.py` | Open question generation | 2 | `05` §8 |
| `spec_forge/evidence/ledger.py` | The evidence ledger | 2 | `05` §5 |
| `spec_forge/library/archetypes/*.yaml` | Typed archetypes — **data, not code** | 1–2 | `06` §3 |
| `spec_forge/library/retrieval.py` | Deterministic → lexical → semantic retrieval | 1 | `06` §5 |
| `spec_forge/library/bindings.py` | Cross-run binding reuse | 2 | `06` §7 |
| `spec_forge/extract/passes/` | Seven schema-constrained extraction passes | 1–2 | `16` §4 |
| `spec_forge/extract/merge.py` | IR assembly and merge order | 1 | `16` §4 |
| `spec_forge/extract/client.py` | Anthropic client wrapper with recording | 1 | `16` §8 |
| `spec_forge/validate/rules/` | One module per rule family | 1–2 | `09` §2 |
| `spec_forge/validate/ladder.py` | The four validation gates | 1 | `09` §1 |
| `spec_forge/validate/consistency.py` | SysML ↔ Modelica round-trip check | 3 | `09` §6 |
| `spec_forge/validate/reference.py` | Reference-trace comparison | 3 | `09` §7 |
| `spec_forge/emit/sysml/` | SysML v2 emitter and templates | 1 | `07` |
| `spec_forge/emit/modelica/` | Modelica emitter, templates, state-machine strategies | 1 | `08` |
| `spec_forge/emit/report/` | `summary.md`, `traceability.md`, plots | 3 | `10` |
| `spec_forge/toolchain/omc.py` | `omc` compile, simulate, liveness — **the gate** | 0–1 | `08` §6 |
| `spec_forge/toolchain/sysml.py` | SysML v2 toolchain wrapper | 0–1 | `07` §4 |
| `spec_forge/toolchain/doctor.py` | Environment checks | 0 | `devenv` §5 |
| `spec_forge/repair/` | Diagnosis, localisation, actions, bounded loop | 3 | `09` §5 |
| `spec_forge/pipeline/graph.py` | LangGraph graph definition | 1 | `16` §2 |
| `spec_forge/pipeline/state.py` | Pipeline state | 1 | `16` §3 |
| `spec_forge/pipeline/events.py` | Progress event bus with heartbeat | 1 | `16` §9 |
| `spec_forge/pipeline/replay.py` | Record and replay | 1 | `16` §8 |
| `spec_forge/pipeline/prompts/` | Versioned prompt files — **data, not code** | 1 | `16` §7 |
| `spec_forge/persistence/` | SQLAlchemy models, repositories, migrations | 1 | `13` |
| `spec_forge/api/` | FastAPI app, routes, SSE | 4 | `12` |
| `spec_forge/cli/main.py` | Typer CLI — `run`, `doctor`, `bench`, … | 1 | `12` §8 |

## Sourcemap Index

*(Empty. Add an entry here for every source file created, with its purpose.)*
