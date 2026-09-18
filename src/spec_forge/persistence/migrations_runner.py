# Purpose: runs Alembic migrations from Python, for `spec-forge db upgrade` (13_data_model_spec.md
# §4). Unlike a toolchain liveness check, a failed migration is a hard stop for this command, not a
# reportable status — MigrationError is raised, never swallowed into a "degraded" result.

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from pydantic import BaseModel

from spec_forge.core.errors import SpecForgeError

__all__ = ["MigrationError", "UpgradeResult", "run_upgrade"]

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"


class MigrationError(SpecForgeError):
    """Alembic failed to run a migration command."""


class UpgradeResult(BaseModel):
    ok: bool
    revision: str
    message: str


def _config() -> Config:
    if not ALEMBIC_INI.is_file():
        raise MigrationError(f"alembic.ini not found at {ALEMBIC_INI}")
    return Config(str(ALEMBIC_INI))


def run_upgrade(revision: str = "head") -> UpgradeResult:
    """Run `alembic upgrade <revision>`. DATABASE_URL is read by migrations/env.py directly from
    the environment (docs/devenv.md §4) — not passed here, so this stays a thin wrapper around
    Alembic's own Config resolution rather than a second source of truth for the connection URL."""
    cfg = _config()
    try:
        command.upgrade(cfg, revision)
    except Exception as exc:  # Alembic/SQLAlchemy raise a wide variety of exception types
        raise MigrationError(f"alembic upgrade {revision} failed: {exc}") from exc
    return UpgradeResult(ok=True, revision=revision, message=f"upgraded to {revision}")
