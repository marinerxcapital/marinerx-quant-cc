"""Lightweight schema migration for SQLite and Postgres."""
from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from mcc.storage.models import Base


def _column_names(engine: Engine, table: str) -> set[str]:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def ensure_schema(engine: Engine) -> None:
    """Create tables and add missing columns on existing tables."""
    Base.metadata.create_all(engine)
    _migrate_strategies(engine)


def _migrate_strategies(engine: Engine) -> None:
    if "strategies" not in inspect(engine).get_table_names():
        return
    existing = _column_names(engine, "strategies")
    additions = {
        "name": "TEXT DEFAULT ''",
        "description": "TEXT DEFAULT ''",
        "instrument": "TEXT DEFAULT ''",
        "timeframe": "TEXT DEFAULT ''",
        "version": "INTEGER DEFAULT 1",
        "owner_agent": "TEXT DEFAULT 'ResearchLab'",
        "hypothesis": "TEXT DEFAULT ''",
        "entry_rules": "TEXT DEFAULT ''",
        "exit_rules": "TEXT DEFAULT ''",
        "risk_rules": "TEXT DEFAULT ''",
        "parameters_json": "TEXT DEFAULT '{}'",
        "tags": "TEXT DEFAULT ''",
        "latest_verdict": "TEXT DEFAULT ''",
        "latest_validation_id": "TEXT DEFAULT ''",
        "archived_at": "TIMESTAMP",
        "source": "TEXT DEFAULT 'registry'",
        "metadata_json": "TEXT DEFAULT '{}'",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    }
    with engine.begin() as conn:
        for col, typedef in additions.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE strategies ADD COLUMN {col} {typedef}"))