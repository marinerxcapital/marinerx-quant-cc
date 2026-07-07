"""Database engine and initialization — SQLite locally, Postgres in production."""
from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from mcc.core.config import get_settings
from mcc.storage.models import Base

_engine: Engine | None = None


def _register_all_tables() -> None:
    """Import optional table modules so SQLAlchemy metadata is complete."""
    import marinerx_tradeify.persistence  # noqa: F401


def get_engine(url: str | None = None) -> Engine:
    global _engine
    if _engine is not None and url is None:
        return _engine

    settings = get_settings()
    db_url = url or settings.sqlalchemy_url
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


def reset_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None
    from mcc.storage.session import reset_session_factory

    reset_session_factory()