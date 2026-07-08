"""MarketPulse heatmap frames use Phase 03 schema."""
from __future__ import annotations

import pandas as pd
import pytest

from mcc.data.live import free_market
from mcc.heatmaps.correlation import build_correlation_frame
from mcc.heatmaps.volatility import build_volatility_frame
from mcc.market_pulse.snapshot import build_live_snapshot


@pytest.fixture(autouse=True)
def _clear_cache():
    free_market.clear_cache()
    yield
    free_market.clear_cache()


@pytest.fixture
def mock_yfinance(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            idx = pd.date_range("2026-07-01", periods=30, freq="5min", tz="UTC")
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

    class FakeYF:
        def Ticker(self, symbol):
            return FakeTicker()

    monkeypatch.setattr(free_market, "_get_yf", lambda: FakeYF())


def test_correlation_frame_schema(mock_yfinance):
    frame = build_correlation_frame(["NQ", "ES"], free_market.get_bars)
    assert frame is not None
    d = frame.to_dict()
    assert d["rows"] == d["cols"] == 2
    assert len(d["z"]) == 2
    assert d["z"][0][0] == 1.0
    assert "x_labels" in d and "y_labels" in d and "ts" in d


def test_volatility_frame_schema(mock_yfinance):
    frame = build_volatility_frame(["NQ", "ES"], free_market.get_bars)
    assert frame is not None
    d = frame.to_dict()
    assert d["rows"] >= 1
    assert d["cols"] == 4
    assert len(d["z"][0]) == 4


def test_build_live_snapshot_includes_heatmaps(mock_yfinance):
    snap = build_live_snapshot("NQ")
    assert snap.get("proxies")
    assert "tick" in snap["proxies"]
    assert "heatmaps" in snap
    assert "correlation" in snap["heatmaps"]
    assert "volatility" in snap["heatmaps"]
    assert snap["heatmaps"]["correlation"]["rows"] >= 2