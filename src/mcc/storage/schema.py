"""Lightweight schema migration for SQLite and Postgres."""
from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.schema import Column

from mcc.storage.models import Base

# Tables backing Tier 1 APIs (strategies, risk, journal, instruments, orders, etc.)
TIER1_TABLES: tuple[str, ...] = (
    "strategies",
    "strategy_versions",
    "instruments",
    "market_bars",
    "regime_snapshots",
    "backtest_runs",
    "validation_results",
    "trade_decisions",
    "orders",
    "journal_entries",
    "performance_daily",
    "risk_settings",
    "risk_events",
    "reports",
)


def _column_names(engine: Engine, table: str) -> set[str]:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def _literal_default(column: Column) -> str | None:
    if column.server_default is not None:
        compiled = column.server_default.arg
        if hasattr(compiled, "text"):
            return str(compiled.text)
        return str(compiled)

    default = column.default
    if default is None:
        return None
    if not hasattr(default, "arg"):
        return None

    value = default.arg
    if callable(value):
        return None

    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return None


def _column_ddl(column: Column, engine: Engine) -> str:
    dialect = engine.dialect
    col_type = column.type.compile(dialect=dialect)

    if isinstance(column.type, Boolean):
        col_type = "INTEGER" if dialect.name == "sqlite" else "BOOLEAN"
    elif isinstance(column.type, String):
        col_type = "TEXT" if dialect.name == "sqlite" else col_type
    elif isinstance(column.type, Text):
        col_type = "TEXT"
    elif isinstance(column.type, Integer):
        col_type = "INTEGER"
    elif isinstance(column.type, Float):
        col_type = "REAL" if dialect.name == "sqlite" else col_type
    elif isinstance(column.type, DateTime):
        col_type = "TIMESTAMP"

    parts = [col_type]
    default_sql = _literal_default(column)
    if default_sql is not None:
        parts.append(f"DEFAULT {default_sql}")
    elif column.nullable is False:
        if isinstance(column.type, (String, Text)):
            parts.append("DEFAULT ''")
        elif isinstance(column.type, Integer):
            parts.append("DEFAULT 0")
        elif isinstance(column.type, Float):
            parts.append("DEFAULT 0.0")
        elif isinstance(column.type, Boolean):
            parts.append("DEFAULT 0")

    return " ".join(parts)


def _migrate_table(engine: Engine, table_name: str) -> list[str]:
    """Add missing columns on an existing table. Returns columns added."""
    if table_name not in Base.metadata.tables:
        return []

    table = Base.metadata.tables[table_name]
    existing = _column_names(engine, table_name)
    if not existing:
        return []

    added: list[str] = []
    with engine.begin() as conn:
        for column in table.columns:
            if column.name in existing:
                continue
            ddl = _column_ddl(column, engine)
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column.name} {ddl}"))
            added.append(column.name)
    return added


def _migrate_tier1_tables(engine: Engine) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    for table_name in TIER1_TABLES:
        added = _migrate_table(engine, table_name)
        if added:
            results[table_name] = added
    return results


def ensure_schema(engine: Engine) -> None:
    """Create tables and add missing columns on existing Tier 1 tables."""
    Base.metadata.create_all(engine)
    _migrate_tier1_tables(engine)