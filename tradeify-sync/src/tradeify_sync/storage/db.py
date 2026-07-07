"""Database engine and session management."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from tradeify_sync.config import Settings, get_settings
from tradeify_sync.storage.schema import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _enable_wal(dbapi_conn: object, _connection_record: object) -> None:
    cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def get_engine(settings: Settings | None = None, db_path: Path | None = None) -> Engine:
    """Create or return the SQLAlchemy engine with WAL mode."""
    global _engine, _SessionLocal
    if _engine is not None and db_path is None:
        return _engine

    cfg = settings or get_settings()
    path = db_path or cfg.resolve(cfg.storage.sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{path.as_posix()}"
    engine = create_engine(url, echo=False, future=True)
    event.listen(engine, "connect", _enable_wal)
    if db_path is None:
        _engine = engine
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine


def init_db(settings: Settings | None = None, db_path: Path | None = None) -> Engine:
    """Create all tables."""
    engine = get_engine(settings, db_path)
    Base.metadata.create_all(engine)
    return engine


@contextmanager
def session_scope(settings: Settings | None = None, db_path: Path | None = None) -> Generator[Session]:
    """Provide a transactional scope around a series of operations."""
    if db_path is not None:
        engine = get_engine(settings, db_path)
        factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        session = factory()
    else:
        get_engine(settings)
        assert _SessionLocal is not None
        session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()