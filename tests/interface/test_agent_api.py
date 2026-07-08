"""Smoke tests for /api/agents/* and /api/account/sync endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mcc.core.config import get_settings
from mcc.data.live import free_market
from mcc.interface.web.server import app
from mcc.storage.database import get_engine, init_db, reset_engine
from mcc.storage.models import Trade


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_live_cache():
    free_market.clear_cache()
    yield
    free_market.clear_cache()


def _fake_df() -> pd.DataFrame:
    idx = pd.date_range("2026-07-01", periods=30, freq="5min", tz=timezone.utc)
    closes = [100.0 + i * 0.5 for i in range(30)]
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [c + 1 for c in closes],
            "Low": [c - 1 for c in closes],
            "Close": closes,
            "Volume": [1000 + i * 10 for i in range(30)],
        },
        index=idx,
    )


@pytest.fixture
def mock_yfinance(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return _fake_df()

    class FakeYF:
        def Ticker(self, symbol):
            return FakeTicker()

    monkeypatch.setattr(free_market, "_get_yf", lambda: FakeYF())


@pytest.fixture
def memory_db(monkeypatch, tmp_path):
    reset_engine()
    get_settings.cache_clear()
    db_file = tmp_path / "agent_api_test.db"
    url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    init_db()
    yield url
    reset_engine()
    get_settings.cache_clear()


def test_agents_snapshot_endpoint(client, mock_yfinance):
    r = client.get("/api/agents/snapshot")
    assert r.status_code == 200
    body = r.json()
    assert "agents" in body
    assert body["agent_count"] == 15
    assert "Overseer" in body["agents"]
    assert "status" in body["agents"]["MarketPulse"]
    assert "metric" in body["agents"]["MarketPulse"]


def test_agents_market_pulse_endpoint(client, mock_yfinance):
    r = client.get("/api/agents/market-pulse")
    assert r.status_code == 200
    body = r.json()
    assert body["agent"] == "MarketPulse"
    assert "snapshot" in body
    assert "proxies" in body["snapshot"]
    assert "tick" in body["snapshot"]["proxies"]
    assert "heatmaps" in body
    assert "correlation" in body["heatmaps"]
    assert body["heatmaps"]["correlation"]["rows"] >= 2


def test_agents_indicators_endpoint(client, mock_yfinance):
    r = client.get("/api/agents/indicators/NQ")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "NQ"
    assert "indicators" in body
    assert body["indicators"]["values"]["close"] is not None
    assert body["indicators"]["values"]["rsi_14"] is not None


def test_agents_indicators_unknown_symbol(client):
    r = client.get("/api/agents/indicators/ZZZ")
    assert r.status_code == 404


def test_agents_journal_empty(client, memory_db):
    r = client.get("/api/agents/journal")
    assert r.status_code == 200
    body = r.json()
    assert body["agent"] == "TradeJournal"
    assert body["sync_status"] == "awaiting_sync"
    assert body["trades"] == []


def test_agents_journal_with_trades(client, memory_db, monkeypatch):
    eng = get_engine()
    monkeypatch.setattr("mcc.interface.web.agent_routes.get_engine", lambda url=None: eng)
    with Session(eng) as session:
        session.add(
            Trade(
                id="t-journal-smoke-001",
                ts_utc=datetime(2026, 7, 1, 14, 30, tzinfo=timezone.utc),
                symbol="NQ",
                side="BUY",
                qty=2,
                price=18750.25,
                pnl=312.5,
            )
        )
        session.commit()

    r = client.get("/api/agents/journal")
    assert r.status_code == 200
    body = r.json()
    assert body["sync_status"] == "live"
    assert body["count"] == 1
    assert body["trades"][0]["symbol"] == "NQ"
    assert body["trades"][0]["pnl"] == 312.5


def test_account_sync_endpoint(client):
    r = client.get("/api/account/sync")
    assert r.status_code == 200
    body = r.json()
    assert "stale" in body
    assert "equity" in body or body.get("sync_status") == "awaiting_sync"
    assert "drawdown_headroom" in body
    assert "safe_default" in body
    assert body["status"] in {"not_available", "ok", "error", "reconciliation_failed", "disabled"}