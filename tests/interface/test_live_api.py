"""Tests for /api/live endpoints with mocked yfinance."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from mcc.data.live import free_market
from mcc.interface.web.server import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_cache():
    free_market.clear_cache()
    yield
    free_market.clear_cache()


def _fake_df() -> pd.DataFrame:
    idx = pd.date_range("2026-07-01", periods=5, freq="5min", tz=timezone.utc)
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 101.5, 103.0],
            "High": [101.0, 102.0, 103.0, 102.5, 104.0],
            "Low": [99.5, 100.5, 101.5, 101.0, 102.5],
            "Close": [100.5, 101.5, 102.5, 102.0, 103.5],
            "Volume": [1000, 1100, 1200, 1150, 1300],
        },
        index=idx,
    )


def test_live_snapshot_endpoint(client, monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return _fake_df()

    class FakeYF:
        def Ticker(self, symbol):
            return FakeTicker()

    monkeypatch.setattr(free_market, "_get_yf", lambda: FakeYF())
    r = client.get("/api/live/snapshot")
    assert r.status_code == 200
    body = r.json()
    assert "instruments" in body
    assert len(body["instruments"]) == 4
    nq = next(i for i in body["instruments"] if i["symbol"] == "NQ")
    assert nq["price"] == 103.5
    assert nq["source"] == "yfinance"


def test_live_bars_endpoint(client, monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return _fake_df()

    class FakeYF:
        def Ticker(self, symbol):
            return FakeTicker()

    monkeypatch.setattr(free_market, "_get_yf", lambda: FakeYF())
    r = client.get("/api/live/bars/NQ")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "NQ"
    assert len(body["bars"]) == 5
    assert body["bars"][-1]["close"] == 103.5


def test_live_bars_unknown_symbol(client):
    r = client.get("/api/live/bars/ZZZ")
    assert r.status_code == 404


def test_live_internals_endpoint(client, monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return _fake_df()

    class FakeYF:
        def Ticker(self, symbol):
            return FakeTicker()

    monkeypatch.setattr(free_market, "_get_yf", lambda: FakeYF())
    r = client.get("/api/live/internals")
    assert r.status_code == 200
    body = r.json()
    assert "proxies" in body
    assert "tick" in body["proxies"]
    assert body["source"] == "yfinance_proxy"


def test_live_sources_endpoint(client):
    r = client.get("/api/live/sources")
    assert r.status_code == 200
    assert "yfinance" in r.json()["primary"]


def test_live_decision_endpoint(client, monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return _fake_df()

    class FakeYF:
        def Ticker(self, symbol):
            return FakeTicker()

    monkeypatch.setattr(free_market, "_get_yf", lambda: FakeYF())
    r = client.get("/api/live/decision")
    assert r.status_code == 200
    body = r.json()
    assert "cards" in body
    assert len(body["cards"]) == 4
    assert body["primary_symbol"] in {"NQ", "ES", "CL", "GC"}
    assert "confidence_pct" in body["cards"][0]
    assert "vetoes" in body["cards"][0]


def test_live_risk_endpoint(client, monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return _fake_df()

    class FakeYF:
        def Ticker(self, symbol):
            return FakeTicker()

    monkeypatch.setattr(free_market, "_get_yf", lambda: FakeYF())
    r = client.get("/api/live/risk")
    assert r.status_code == 200
    body = r.json()
    assert "prop_guardian" in body
    assert "var" in body
    assert "cvar" in body
    assert "exposures" in body
    assert len(body["exposures"]) == 4


def test_live_performance_endpoint(client, monkeypatch):
    idx = pd.date_range("2026-01-01", periods=30, freq="1D", tz=timezone.utc)

    def make_df():
        return pd.DataFrame(
            {
                "Open": [100.0 + i for i in range(30)],
                "High": [101.0 + i for i in range(30)],
                "Low": [99.0 + i for i in range(30)],
                "Close": [100.5 + i * 0.5 for i in range(30)],
                "Volume": [1000] * 30,
            },
            index=idx,
        )

    class FakeTicker:
        def history(self, **kwargs):
            return make_df()

    class FakeYF:
        def Ticker(self, symbol):
            return FakeTicker()

    monkeypatch.setattr(free_market, "_get_yf", lambda: FakeYF())
    r = client.get("/api/live/performance")
    assert r.status_code == 200
    body = r.json()
    assert "equity_curve" in body
    assert len(body["equity_curve"]) > 0
    assert "sharpe" in body
    assert "disclaimer" in body


def test_live_tradingview_endpoint(client):
    r = client.get("/api/live/tradingview")
    assert r.status_code == 200
    body = r.json()
    assert body["default_symbol"] == "NQ"
    assert "NQ" in body["symbols"]
    assert body["symbols"]["NQ"] == "CME_MINI:NQ1!"