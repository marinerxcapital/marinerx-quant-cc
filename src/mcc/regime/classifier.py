"""Regime classifier — volatility and trend state."""
from __future__ import annotations

from typing import Any

from mcc.storage.repositories import MarketBarRepository, RegimeRepository

_bar_repo = MarketBarRepository()
_regime_repo = RegimeRepository()


def classify_regime(symbol: str, timeframe: str = "15m") -> dict[str, Any]:
    bars = _bar_repo.get_bars(symbol, timeframe, limit=50)
    if len(bars) < 5:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "volatility_regime": "NORMAL",
            "trend_state": "TRANSITION",
            "confidence": 0.3,
            "rationale": "Insufficient bar data — degraded classification.",
            "degraded": True,
        }

    closes = [b["close"] for b in bars]
    ranges = [b["high"] - b["low"] for b in bars]
    avg_range = sum(ranges) / len(ranges)
    slope = (closes[-1] - closes[0]) / len(closes)
    vol_pct = min(100, avg_range / closes[-1] * 10000)

    vol_regime = "NORMAL"
    if vol_pct > 15:
        vol_regime = "HIGH"
    elif vol_pct < 5:
        vol_regime = "LOW"

    trend = "RANGING"
    if abs(slope) > avg_range * 0.3:
        trend = "TRENDING"
    elif abs(slope) < avg_range * 0.1:
        trend = "RANGING"
    else:
        trend = "TRANSITION"

    result = {
        "symbol": symbol,
        "timeframe": timeframe,
        "volatility_regime": vol_regime,
        "trend_state": trend,
        "confidence": round(min(0.95, 0.5 + len(bars) / 100), 2),
        "rationale": f"ATR proxy={avg_range:.2f}, slope={slope:.2f}, vol_pct={vol_pct:.1f}",
        "realized_vol_percentile": round(vol_pct, 2),
        "atr_percentile": round(avg_range, 2),
        "ma_slope": round(slope, 4),
    }
    saved = _regime_repo.save(result)
    result["last_updated"] = saved.get("last_updated")
    return result