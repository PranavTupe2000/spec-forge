# Purpose: tests for the Alembic migration runner. Failure wrapping is unit-tested with Alembic's
# own command mocked out; the critical test actually runs `alembic upgrade head` against the real
# docker-compose postgres:16 container, skipped with a clear reason if unreachable.

from __future__ import annotations

import socket
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from spec_forge.core.errors import SpecForgeError
from spec_forge.persistence import migrations_runner

DATABASE_URL = "postgresql+psycopg://specforge:specforge@localhost:5432/specforge"


def _postgres_reachable() -> bool:
    parsed = urlsplit(DATABASE_URL)
    assert parsed.hostname is not None
    assert parsed.port is not None
    try:
        with socket.create_connection((parsed.hostname, parsed.port), timeout=2):
            return True
    except OSError:
        return False


requires_real_postgres = pytest.mark.skipif(
    not _postgres_reachable(),
    reason="postgres:16 not reachable on localhost:5432 — `docker compose up -d postgres` first",
)


def test_migration_error_is_specforge_error() -> None:
    assert issubclass(migrations_runner.MigrationError, SpecForgeError)


def test_run_upgrade_wraps_alembic_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(cfg: object, revision: str) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(migrations_runner.command, "upgrade", _boom)
    with pytest.raises(migrations_runner.MigrationError, match="boom"):
        migrations_runner.run_upgrade("head")


def test_run_upgrade_raises_when_alembic_ini_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(migrations_runner, "ALEMBIC_INI", tmp_path / "does_not_exist.ini")
    with pytest.raises(migrations_runner.MigrationError):
        migrations_runner.run_upgrade("head")


@requires_real_postgres
def test_run_upgrade_applies_the_real_baseline_migration(monkeypatch: pytest.MonkeyPatch) -> None:
    import psycopg

    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)

    result = migrations_runner.run_upgrade("head")

    assert result.ok is True
    assert result.revision == "head"

    libpq_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(libpq_url, autocommit=True) as conn:
        row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
    assert row is not None
