"""Assemble MarketPulse snapshot from breadth + free-market layers."""
from __future__ import annotations

from typing import Any

from mcc.data.live.free_market import INSTRUMENT_META, get_bars, get_internals_proxy
from mcc.heatmaps.correlation import build_correlation_frame
from mcc.heatmaps.volatility import build_volatility_frame
from mcc.internals.breadth import compute_breadth_from_proxies
from mcc.microstructure.volume_profile import build_volume_profile


def build_live_snapshot(symbol: str = "NQ") -> dict[str, Any]:
    """Build a render-ready MarketPulse snapshot from live free-market feeds."""
    proxy = get_internals_proxy()
    proxies = proxy.get("proxies") or {}
    state = compute_breadth_from_proxies(proxies, breadth_score=proxy.get("breadth_score"))

    heatmaps: dict[str, Any] = {}
    symbols = list(INSTRUMENT_META.keys())
    corr = build_correlation_frame(symbols, get_bars)
    vol = build_volatility_frame(symbols, get_bars)
    if corr:
        heatmaps["correlation"] = corr.to_dict()
    if vol:
        heatmaps["volatility"] = vol.to_dict()

    bars = get_bars(symbol).get("bars") or []
    volume_profiles: dict[str, Any] = {}
    profile = build_volume_profile(bars)
    if profile:
        volume_profiles[symbol] = profile

    regime = proxy.get("regime") or state.regime.upper().replace("_", "-")
    return {
        **state.to_dict(),
        "proxies": proxies,
        "vix": proxy.get("vix"),
        "regime": regime,
        "regime_confidence": proxy.get("regime_confidence"),
        "breadth_score": proxy.get("breadth_score") or state.breadth_score,
        "disclaimer": proxy.get("disclaimer"),
        "source": proxy.get("source", "yfinance_proxy"),
        "sparklines": proxy.get("sparklines") or {},
        "heatmaps": heatmaps,
        "volume_profiles": volume_profiles,
        "series": {
            "tick": [state.tick],
            "trin": [state.trin],
            "add": [state.add],
            "breadth": [state.breadth_score],
        },
        "as_of": proxy.get("as_of"),
        "buffer_len": 1,
    }