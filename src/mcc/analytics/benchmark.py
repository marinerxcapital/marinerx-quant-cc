"""Shared benchmark resolution for QuantStats and future comparison needs (Phase 16)."""
from __future__ import annotations

from typing import Final

import pandas as pd

from mcc.analytics.validation import validate_return_series

DEFAULT_BENCHMARK_LABEL: Final[str] = "flat_rate_4.5pct"
DEFAULT_RISK_FREE_ANNUAL: Final[float] = 0.045
TRADING_DAYS_PER_YEAR: Final[int] = 252


def resolve_flat_rate_benchmark(
    returns: pd.Series,
    *,
    annual_rate: float = DEFAULT_RISK_FREE_ANNUAL,
    label: str = DEFAULT_BENCHMARK_LABEL,
) -> tuple[pd.Series, str]:
    """Return a flat risk-free daily benchmark aligned to ``returns`` and its label."""
    daily = (1.0 + annual_rate) ** (1.0 / TRADING_DAYS_PER_YEAR) - 1.0
    bench = pd.Series(daily, index=returns.index, name="benchmark")
    return validate_return_series(bench, name="flat_benchmark"), label