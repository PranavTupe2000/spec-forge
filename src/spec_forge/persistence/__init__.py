# Purpose: owns the SQLAlchemy models, repositories and Alembic migrations for cross-run queries,
# persisted overrides and binding reuse (ADR-008). The filesystem, not this package, remains
# authoritative for artifact bytes.
