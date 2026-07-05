"""Simple realized-volatility bucket classifier (Phase 04 stub, Phase 16 boundary)."""
from __future__ import annotations

from typing import Any, Final, Literal

import numpy as np
import pandas as pd

from mcc.analytics.validation import validate_price_series, utc_now
from mcc.core.events import RegimeEvent

VolBucket = Literal["low", "normal", "high"]

# FIXTURE — tests only
FIXTURE_VOL_SYMBOL: Final[str] = "ES_FIXTURE_VOL"


def _realized_vol(prices: pd.Series, window: int) -> pd.Series:
    log_ret = np.log(prices.astype(float)).diff()
    return log_ret.rolling(window=window, min_periods=max(5, window // 2)).std()


def classify_volatility_regime(
    prices: pd.Series,
    *,
    window: int = 20,
    low_pct: float = 33.0,
    high_pct: float = 67.0,
) -> dict[str, Any]:
    """Classify the latest observation into a volatility bucket.

    Uses rolling realized vol percentiles over the in-sample history:
    ``low`` (< low_pct), ``normal``, ``high`` (>= high_pct).

    Parameters
    ----------
    prices:
        Point-in-time price series (UTC DatetimeIndex).
    window:
        Rolling window for realized volatility.
    low_pct / high_pct:
        Percentile cutoffs for tercile-style buckets.

    Returns
    -------
    dict
        Keys: ``bucket``, ``realized_vol``, ``percentile``, ``window``.
    """
    validated = validate_price_series(prices, name="vol_prices")
    vol = _realized_vol(validated, window).dropna()
    if vol.empty:
        return {
            "bucket": "normal",
            "realized_vol": 0.0,
            "percentile": 50.0,
            "window": window,
            "confidence": 0.5,
        }

    current = float(vol.iloc[-1])
    pct_rank = float(vol.rank(pct=True).iloc[-1] * 100.0)
    if pct_rank < low_pct:
        bucket: VolBucket = "low"
    elif pct_rank >= high_pct:
        bucket = "high"
    else:
        bucket = "normal"

    # Confidence: distance from nearest boundary (0.5 at boundary, 1.0 at extremes)
    if bucket == "low":
        confidence = float(np.clip(1.0 - pct_rank / low_pct, 0.5, 1.0))
    elif bucket == "high":
        confidence = float(np.clip((pct_rank - high_pct) / (100.0 - high_pct), 0.5, 1.0))
    else:
        mid = (low_pct + high_pct) / 2.0
        confidence = float(np.clip(1.0 - abs(pct_rank - mid) / (mid - low_pct), 0.5, 1.0))

    return {
        "bucket": bucket,
        "realized_vol": current,
        "percentile": pct_rank,
        "window": window,
        "confidence": confidence,
    }


def build_volatility_regime_event(
    prices: pd.Series,
    *,
    source: str = "RegimeMonitor",
    symbol: str = "UNKNOWN",
    **kw: Any,
) -> RegimeEvent:
    """Publish volatility bucket as a ``RegimeEvent`` (state = bucket label)."""
    result = classify_volatility_regime(prices)
    return RegimeEvent(
        utc_now(),
        source,
        symbol,
        str(result["bucket"]),
        float(result["confidence"]),
        regime_kind="volatility",
        realized_vol=result["realized_vol"],
        percentile=result["percentile"],
        **kw,
    )