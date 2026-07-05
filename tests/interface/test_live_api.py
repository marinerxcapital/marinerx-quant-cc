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