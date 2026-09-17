# ADR-008 — PostgreSQL from Phase 1; filesystem authoritative for artifacts

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `persistence`, `api`, `pipeline`

## Context

The stated stack includes PostgreSQL. The question was whether it belongs in Phase 1 or later, and what it owns.

## Decision

**Postgres is in from Phase 1**, and owns what must outlive a single run: projects and sources, run history, the
claim/conflict evidence ledger, tier-0 user overrides, and component bindings.

**The filesystem remains authoritative for artifact bytes.** Generated files live in `runs/<run_id>/`; the
database stores metadata, relationships, a path and a hash.

The pipeline runs with `--no-db`, writing only to the filesystem, with a warning.

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Phase-3 addition, filesystem only until then** | Overrides and bindings would have nowhere to persist, so clarifying dialogue and the reuse mechanism would be rebuilt later against a different storage model. |
| **SQLite** | Zero-install and lower demo risk, but diverges from the stated stack, and loses `jsonb`, `tsvector` full-text search over fragments, and array columns — all of which the evidence ledger uses. |
| **Store artifact bytes in Postgres** | Judges must be able to run the compile command against a file in the repo with no database running. Artifacts are also diffable, greppable and committable as files. |
| **No database** | Cross-run queries, persisted overrides and evidence search all become filesystem scans. |

## Consequences

- The database earns its place by answering questions files cannot, rather than by becoming a blob store.
- `--no-db` is a tested mode, not a theoretical one, so persistence can never block the compile gate.
- The API requires the database and reports it red on `/ready`; the CLI does not.
