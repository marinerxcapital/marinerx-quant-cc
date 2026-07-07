"""Pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tradeify_sync.config import Settings
from tradeify_sync.storage.db import get_engine, init_db, session_scope


@pytest.fixture
def project_root() -> Path:
    return ROOT


@pytest.fixture
def settings(project_root: Path, tmp_path: Path) -> Settings:
    """Settings with isolated database."""
    s = Settings.load(config_path=project_root / "config.yaml")
    s.project_root = project_root
    s.storage.sqlite_path = str(tmp_path / "test.db")
    return s


@pytest.fixture
def db_session(settings: Settings) -> Session:
    """In-memory-like isolated sqlite session."""
    db_path = settings.resolve(settings.storage.sqlite_path)
    init_db(settings, db_path)
    with session_scope(settings, db_path) as session:
        yield session
        session.commit()


@pytest.fixture
def accounts_html(project_root: Path) -> str:
    return (project_root / "tests" / "fixtures" / "accounts.html").read_text(encoding="utf-8")


@pytest.fixture
def trades_html(project_root: Path) -> str:
    return (project_root / "tests" / "fixtures" / "trades.html").read_text(encoding="utf-8")