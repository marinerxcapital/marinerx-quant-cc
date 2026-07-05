"""REST endpoints for live dashboard data (free/delayed sources)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from mcc.data.live.free_market import (
    INSTRUMENT_META,
    get_bars,
    get_internals_proxy,
    get_market_snapshot,
    get_regime_snapshot,
)

router = APIRouter(prefix="/api/live", tags=["live-data"])


@router.get("/snapshot")
def live_snapshot() -> dict[str, Any]:
    return get_market_snapshot()


@router.get("/bars/{symbol}")
def live_bars(symbol: str, interval: str = "5m", period: str = "5d") -> dict[str, Any]:
    sym = symbol.upper()
    if sym not in INSTRUMENT_META:
        raise HTTPException(status_code=404, detail=f"Unknown symbol: {sym}")
    return get_bars(sym, interval=interval, period=period)


@router.get("/internals")
def live_internals() -> dict[str, Any]:
    return get_internals_proxy()


@router.get("/regime")
def live_regime() -> dict[str, Any]:
    return get_regime_snapshot()


@router.get("/sources")
def live_sources() -> dict[str, Any]:
    return {
        "primary": "yfinance (Yahoo Finance, free, delayed)",
        "optional": "ALPHA_VANTAGE_API_KEY env for supplemental quotes",
        "internals_note": "TICK/TRIN/ADD on dashboard are computed proxies, not NYSE feed",
        "symbols": list(INSTRUMENT_META.keys()),
    }