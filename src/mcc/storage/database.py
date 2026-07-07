"""Database engine and initialization — SQLite locally, Postgres in production."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from mcc.core.config import get_settings
from mcc.storage.models import Base
from mcc.storage.schema import TIER1_TABLES

_engine: Engine | None = None


def _register_all_tables() -> None:
    """Import optional table modules so SQLAlchemy metadata is complete."""
    import marinerx_tradeify.persistence  # noqa: F401


def _ensure_sqlite_parent_dir(db_url: str) -> None:
    if not db_url.startswith("sqlite:///"):
        return
    path_part = db_url[len("sqlite:///") :]
    if not path_part or path_part == ":memory:":
        return
    Path(path_part).parent.mkdir(parents=True, exist_ok=True)


def get_engine(url: str | None = None) -> Engine:
    global _engine
    if _engine is not None and url is None:
        return _engine

    settings = get_settings()
    settings.ensure_directories()
    db_url = url or settings.sqlalchemy_url
    _ensure_sqlite_parent_dir(db_url)
    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    else:
        engine_kwargs["pool_size"] = settings.database_pool_size
        engine_kwargs["max_overflow"] = settings.database_max_overflow

    _register_all_tables()
    eng = create_engine(db_url, connect_args=connect_args, **engine_kwargs)
    from mcc.storage.schema import ensure_schema

    ensure_schema(eng)

    _engine = eng
    return eng


def init_db(url: str | None = None) -> Engine:
    """Idempotent schema initialization."""
    return get_engine(url)


def check_database_connectivity(url: str | None = None) -> dict[str, Any]:
    eng = get_engine(url) if url else get_engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        backend = "postgres" if str(eng.url).startswith("postgresql") else "sqlite"
        return {"status": "ok", "backend": backend, "url_scheme": eng.url.drivername}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def build_db_health() -> dict[str, Any]:
    """Lightweight schema/query diagnostic — no secrets."""
    eng = get_engine()
    backend = "postgres" if str(eng.url).startswith("postgresql") else "sqlite"
    insp = inspect(eng)
    existing_tables = set(insp.get_table_names())

    column_checks: dict[str, dict[str, Any]] = {}
    for table_name in TIER1_TABLES:
        if table_name not in Base.metadata.tables:
            continue
        expected = {c.name for c in Base.metadata.tables[table_name].columns}
        if table_name in existing_tables:
            actual = {c["name"] for c in insp.get_columns(table_name)}
            column_checks[table_name] = {
                "exists": True,
                "missing_columns": sorted(expected - actual),
                "column_count": len(actual),
            }
        else:
            column_checks[table_name] = {
                "exists": False,
                "missing_columns": sorted(expected),
                "column_count": 0,
            }

    probes = {
        "strategies": "SELECT COUNT(*) AS n FROM strategies",
        "risk_settings": "SELECT COUNT(*) AS n FROM risk_settings",
        "journal_entries": "SELECT COUNT(*) AS n FROM journal_entries",
        "instruments": "SELECT COUNT(*) AS n FROM instruments",
        "orders": "SELECT COUNT(*) AS n FROM orders",
    }
    sample_queries: dict[str, dict[str, Any]] = {}
    with eng.connect() as conn:
        for name, sql in probes.items():
            if name not in existing_tables:
                sample_queries[name] = {"ok": False, "error": "table_missing"}
                continue
            try:
                count = conn.execute(text(sql)).scalar()
                sample_queries[name] = {"ok": True, "count": int(count or 0)}
            except Exception as exc:
                sample_queries[name] = {"ok": False, "error": str(exc)}

    missing_any = any(c.get("missing_columns") for c in column_checks.values())
    failed_queries = [k for k, v in sample_queries.items() if not v.get("ok")]
    status = "ok"
    if failed_queries or missing_any:
        status = "degraded" if not failed_queries else "error"

    return {
        "status": status,
        "backend": backend,
        "tables_present": sorted(existing_tables),
        "tier1_column_checks": column_checks,
        "sample_queries": sample_queries,
    }


def reset_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None
    from mcc.storage.session import reset_session_factory

    reset_session_factory()