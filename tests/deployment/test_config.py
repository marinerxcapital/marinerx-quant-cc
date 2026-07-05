import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from mcc.core.config import MCCSettings, get_settings, reset_settings_cache


@pytest.fixture(autouse=True)
def _reset_config_cache(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("ENABLE_LIVE_EXECUTION", "false")
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_enable_live_execution_defaults_false():
    settings = MCCSettings(_env_file=None)
    assert settings.enable_live_execution is False


def test_invalid_live_execution_treated_as_false(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_EXECUTION", "maybe")
    settings = MCCSettings(_env_file=None)
    assert settings.enable_live_execution is False


def test_sqlite_url_when_no_database_url():
    settings = MCCSettings(_env_file=None, DATA_DIR="./tmp_test_data")
    assert settings.sqlalchemy_url.startswith("sqlite:///")


def test_production_requires_database_url(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    settings = MCCSettings(_env_file=None)
    with pytest.raises(Exception):
        _ = settings.sqlalchemy_url