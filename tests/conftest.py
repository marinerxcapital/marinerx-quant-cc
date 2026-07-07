"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

from mcc.core.config import get_settings
from mcc.storage.database import init_db, reset_engine


@pytest.fixture
def memory_db(monkeypatch, tmp_path):
    reset_engine()
    get_settings.cache_clear()
    db_file = tmp_path / "test.db"
    url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("APP_ENV", "local")
    init_db(url)
    yield url
    reset_engine()
    get_settings.cache_clear()