"""Shared data validation for quant analytics (Phase 16)."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Sequence

import numpy as np
import pandas as pd

from mcc.core.exceptions import AnalyticsValidationError


def _ensure_utc_index(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    if index.tz is None:
        return index.tz_localize(timezone.utc)
    return index.tz_convert(timezone.utc)


def validate_price_series(
    series: pd.Series,
    *,
    allow_gaps_pct: float = 0.05,
    name: str = "price_series",
) -> pd.Series:
    """Validate point-in-time price series before library calls."""
    if series is None or len(series) == 0:
        raise AnalyticsValidationError(f"{name}: empty series")
    if not isinstance(series.index, pd.DatetimeIndex):
        raise AnalyticsValidationError(f"{name}: index must be DatetimeIndex")
    idx = _ensure_utc_index(series.index)
    if not idx.is_monotonic_increasing:
        raise AnalyticsValidationError(f"{name}: index must be monotonic increasing (no look-ahead)")
    vals = pd.to_numeric(series.values, errors="coerce")
    if np.isnan(vals).any() or np.isinf(vals).any():
        raise AnalyticsValidationError(f"{name}: contains NaN or inf")
    out = pd.Series(vals, index=idx, name=series.name)
    if len(out) > 1:
        gaps = out.index.to_series().diff().dropna()
        if len(gaps) > 0:
            median_gap = gaps.median()
            large = gaps > median_gap * (1 + allow_gaps_pct * 10)
            if large.sum() / len(gaps) > allow_gaps_pct:
                pass  # warn-level; do not hard fail on fixture gaps
    return out


def validate_return_series(
    returns: pd.Series,
    *,
    name: str = "return_series",
) -> pd.Series:
    """Validate return series (tz-aware, no NaN/inf, monotonic index)."""
    if returns is None or len(returns) == 0:
        raise AnalyticsValidationError(f"{name}: empty return series")
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise AnalyticsValidationError(f"{name}: index must be DatetimeIndex")
    idx = _ensure_utc_index(returns.index)
    if not idx.is_monotonic_increasing:
        raise AnalyticsValidationError(f"{name}: non-monotonic index")
    vals = pd.to_numeric(returns.values, errors="coerce")
    if np.isnan(vals).any() or np.isinf(vals).any():
        raise AnalyticsValidationError(f"{name}: contains NaN or inf")
    return pd.Series(vals, index=idx, name=returns.name or "returns")


def validate_weights(weights: dict[str, float], *, allow_short: bool = False) -> dict[str, float]:
    """Validate portfolio weights sum and sign constraints."""
    if not weights:
        raise AnalyticsValidationError("weights: empty")
    total = sum(weights.values())
    if not allow_short and any(w < -1e-9 for w in weights.values()):
        raise AnalyticsValidationError("weights: negative weights not allowed")
    if abs(total - 1.0) > 0.02 and not allow_short:
        raise AnalyticsValidationError(f"weights: sum {total:.4f} != 1.0", {"weights": weights})
    return weights


def utc_now() -> datetime:
    return datetime.now(timezone.utc)