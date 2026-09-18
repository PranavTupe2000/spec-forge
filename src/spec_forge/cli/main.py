# Purpose: the Typer CLI entry point (pyproject.toml's `spec-forge` script). Only `doctor` and
# `db upgrade` exist so far — `run`, `ingest`, `bench` and friends need `pipeline/`, a later phase.
# `spec-forge doctor` runs the same probes 12_api_spec.md §8 assigns to the API's `/ready`
# endpoint, so the toolchain's real state is observable before a demo, not assumed.

from __future__ import annotations

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from spec_forge.persistence import migrations_runner
from spec_forge.toolchain import doctor as doctor_module

app = typer.Typer(help="SpecForge Toolkit CLI.")

_SEVERITY_STYLE = {"ok": "green", "warn": "yellow", "error": "red"}


@app.callback()
def _callback() -> None:
    # Typer collapses a Typer() app into its bare single command when only one is registered
    # (confirmed here: `spec-forge doctor` failed with "unexpected extra argument(s) (doctor)"
    # without this). An explicit callback keeps `doctor` addressable as a named subcommand, which
    # matters the moment a second command (`run`, `bench`, ...) is added in a later phase.
    pass


@app.command()
def doctor() -> None:
    """Report Python/uv/omc/SysML/Postgres/Anthropic-key/runs/build status (docs/devenv.md §5)."""
    report = doctor_module.run_checks()

    # box.ASCII (not Rich's default Unicode line-drawing) so this table survives a legacy Windows
    # console codepage (cp1252) without a UnicodeEncodeError — confirmed to actually happen here.
    table = Table(title="spec-forge doctor", box=box.ASCII)
    table.add_column("check")
    table.add_column("status")
    table.add_column("detail")
    for check in report.checks:
        style = _SEVERITY_STYLE[check.severity]
        table.add_row(check.name, f"[{style}]{check.severity}[/{style}]", check.message)

    Console().print(table)
    raise typer.Exit(code=report.exit_code)


db_app = typer.Typer(help="Database migrations (13_data_model_spec.md §4).")
app.add_typer(db_app, name="db")


@db_app.callback()
def _db_callback() -> None:
    # Same single-command collapse this file's top-level callback works around — db_app has
    # exactly one command (upgrade) registered today.
    pass


@db_app.command("upgrade")
def db_upgrade(revision: str = typer.Argument("head")) -> None:
    """Run Alembic migrations up to REVISION (default: head; docs/devenv.md §4)."""
    try:
        result = migrations_runner.run_upgrade(revision)
    except migrations_runner.MigrationError as exc:
        typer.echo(f"Migration failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(result.message)


if __name__ == "__main__":
    app()
