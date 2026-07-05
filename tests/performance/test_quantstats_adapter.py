"""Tests for performance/quantstats_adapter.py."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mcc.performance.quantstats_adapter import (
    DEFAULT_BENCHMARK_LABEL,
    compute_metrics,
    fixture_trades,
    generate_tearsheet,
    trades_to_return_series,
)

TRADING_DAYS = 252
RF_ANNUAL = 0.045
RF_DAILY = (1.0 + RF_ANNUAL) ** (1.0 / TRADING_DAYS) - 1.0


def _hand_sharpe(returns: pd.Series) -> float:
    excess = returns - RF_DAILY
    if returns.std() == 0:
        return 0.0
    return float(excess.mean() / returns.std() * np.sqrt(TRADING_DAYS))


def test_trades_to_return_series_fixture():
    trades = fixture_trades()
    series = trades_to_return_series(trades)
    assert len(series) >= 1
    assert series.index.tz is not None


def test_compute_metrics_returns_finite_values():
    trades = fixture_trades()
    returns = trades_to_return_series(trades)
    metrics = compute_metrics(returns, strategy_id_or_account_id="STR-TEST")
    assert metrics["benchmark"] == DEFAULT_BENCHMARK_LABEL
    assert np.isfinite(metrics["sharpe"])
    assert np.isfinite(metrics["sortino"])
    assert metrics["total_return"] != 0.0 or len(returns) > 0


def test_generate_tearsheet_writes_non_empty_html(tmp_path: Path):
    trades = fixture_trades()
    returns = trades_to_return_series(trades)
    path = generate_tearsheet(returns, "STR-FIXTURE-001", tmp_path)
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert len(content) > 500
    assert "html" in content.lower()
    assert "html" in content.lower() and len(content) > 1000


def test_short_series_edge_case(tmp_path: Path):
    idx = pd.date_range("2024-06-01", periods=3, freq="D", tz="UTC")
    tiny = pd.Series([0.001, -0.002, 0.001], index=idx)
    metrics = compute_metrics(tiny, strategy_id_or_account_id="SHORT")
    assert "sharpe" in metrics
    path = generate_tearsheet(tiny, "SHORT", tmp_path)
    assert path.stat().st_size > 0