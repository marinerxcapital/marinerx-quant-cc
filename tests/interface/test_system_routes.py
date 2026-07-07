"""Tests for system truth endpoints (Phase 2)."""
from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from mcc.core.config import get_settings
from mcc.data.live import free_market
from mcc.interface.web.server import app
from mcc.storage.database import init_db, reset_engine


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_live_cache():
    free_market.clear_cache()
    yield
    free_market.clear_cache()


@pytest.fixture
def mock_yfinance(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            idx = pd.date_range("2026-07-01", periods=10, freq="5min", tz="UTC")
            closes = [100.0 + i for i in range(10)]
            return pd.DataFrame(
                {
                    "Open": closes,
                    "High": [c + 1 for c in closes],
                    "Low": [c - 1 for c in closes],
                    "Close": closes,
                    "Volume": [1000] * 10,
                },
                index=idx,
            )

    class FakeYF:
        def Ticker(self, symbol):
            return FakeTicker()

    monkeypatch.setattr(free_market, "_get_yf", lambda: FakeYF())


@pytest.fixture
def memory_db(monkeypatch, tmp_path):
    reset_engine()
    get_settings.cache_clear()
    db_file = tmp_path / "system_routes_test.db"
    url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("APP_ENV", "local")
    init_db()
    yield
    reset_engine()
    get_settings.cache_clear()


def test_version_endpoint(client):
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "MarinerX Labs Research System"
    assert "version" in body
    assert "environment" in body


def test_config_check_endpoint(client, memory_db):
    r = client.get("/config-check")
    assert r.status_code == 200
    body = r.json()
    assert "checks" in body
    assert body["ok"] is True
    names = {c["name"] for c in body["checks"]}
    assert "DATABASE_URL" in names
    for check in body["checks"]:
        assert check["presence"] in ("PRESENT", "MISSING")
        assert check["level"] in ("REQUIRED", "OPTIONAL")


def test_system_state_endpoint(client, memory_db, mock_yfinance):
    free_market.get_market_snapshot()
    r = client.get("/api/system-state")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("NOMINAL", "STALE", "DEGRADED", "LOCKED")
    assert "agents" in body
    assert body["agents"]["count"] == 15
    assert body["header_metrics"]["day_pnl"] is None
    assert body["status_detail"]["live_execution_enabled"] is False


def test_data_freshness_endpoint(client, mock_yfinance):
    free_market.get_market_snapshot()
    r = client.get("/api/data-freshness")
    assert r.status_code == 200
    body = r.json()
    assert "sources" in body
    assert "market_data" in body["sources"]
    market = body["sources"]["market_data"]
    assert market["status"] in ("fresh", "stale", "missing")
    assert "max_age_seconds" in market


def test_db_health_endpoint(client, memory_db):
    r = client.get("/api/db-health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded", "error")
    assert "tables_present" in body
    assert "tier1_column_checks" in body
    assert "sample_queries" in body
    assert body["tier1_column_checks"]["strategies"]["exists"] is True
    assert body["sample_queries"]["strategies"]["ok"] is True


def test_stale_market_data_flags_degraded(client, memory_db, monkeypatch):
    import time

    free_market.clear_cache()
    free_market._cache["snapshot"] = free_market._CacheEntry(  # type: ignore[attr-defined]
        ts=time.time() - 9999,
        data={"symbols": []},
    )
    r = client.get("/api/system-state")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("STALE", "DEGRADED")