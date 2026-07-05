"""Free/delayed market data for dashboard UI (no API key required).

Sources:
- Yahoo Finance via yfinance (futures proxies NQ=F, ES=F, CL=F, GC=F, ^VIX)
- Optional Alpha Vantage supplement when ALPHA_VANTAGE_API_KEY is set

Internals (TICK/TRIN/ADD) are *proxies* derived from index/futures momentum — not
exchange-sourced NYSE internals. Labeled as such in API responses.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd

# Lazy import — yfinance is optional at import time for tests
_yf = None

INSTRUMENT_META: dict[str, dict[str, str]] = {
    "NQ": {"ticker": "NQ=F", "name": "E-MINI NASDAQ-100"},
    "ES": {"ticker": "ES=F", "name": "E-MINI S&P 500"},
    "CL": {"ticker": "CL=F", "name": "WTI CRUDE OIL"},
    "GC": {"ticker": "GC=F", "name": "GOLD COMEX"},
}

VIX_TICKER = "^VIX"
SPY_TICKER = "SPY"

CACHE_TTL_SEC = 60


@dataclass
class _CacheEntry:
    ts: float
    data: Any


_cache: dict[str, _CacheEntry] = {}


def _get_yf():
    global _yf
    if _yf is None:
        import yfinance as yf_mod

        _yf = yf_mod
    return _yf


def _cached(key: str, loader: Any, ttl: float = CACHE_TTL_SEC) -> Any:
    now = time.time()
    entry = _cache.get(key)
    if entry and (now - entry.ts) < ttl:
        return entry.data
    data = loader()
    _cache[key] = _CacheEntry(ts=now, data=data)
    return data


def _safe_history(ticker: str, period: str = "5d", interval: str = "5m") -> pd.DataFrame:
    yf = _get_yf()
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            return pd.DataFrame()
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()


def _quote_from_history(ticker: str, symbol: str, display_name: str) -> dict[str, Any]:
    df = _safe_history(ticker, period="5d", interval="5m")
    if df.empty:
        return {
            "symbol": symbol,
            "name": display_name,
            "price": None,
            "change": None,
            "change_pct": None,
            "decision": "STAND-ASIDE",
            "reason": "Market data temporarily unavailable.",
            "source": "yfinance",
            "stale": True,
        }

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
    price = float(last["Close"])
    prev_close = float(prev["Close"])
    change = price - prev_close
    change_pct = (change / prev_close * 100.0) if prev_close else 0.0
    decision, reason = _heuristic_decision(change_pct, symbol)

    return {
        "symbol": symbol,
        "name": display_name,
        "price": round(price, 2),
        "open": round(float(last["Open"]), 2),
        "high": round(float(last["High"]), 2),
        "low": round(float(last["Low"]), 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "decision": decision,
        "reason": reason,
        "source": "yfinance",
        "stale": False,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def _heuristic_decision(change_pct: float, symbol: str) -> tuple[str, str]:
    """Display-only GO/NO-GO from momentum — not the production DecisionEngine."""
    if change_pct >= 0.35:
        return "GO", f"{symbol} momentum positive ({change_pct:+.2f}%); breadth proxy supportive."
    if change_pct <= -0.25:
        return "NO-GO", f"{symbol} momentum negative ({change_pct:+.2f}%); risk/reward poor."
    return "STAND-ASIDE", f"{symbol} range-bound ({change_pct:+.2f}%); await clearer edge."


def get_market_snapshot() -> dict[str, Any]:
    def load() -> dict[str, Any]:
        instruments = []
        for sym, meta in INSTRUMENT_META.items():
            instruments.append(_quote_from_history(meta["ticker"], sym, meta["name"]))
        return {
            "instruments": instruments,
            "source": "yfinance",
            "disclaimer": "Delayed quotes. Decisions shown are momentum heuristics, not live execution signals.",
            "as_of": datetime.now(timezone.utc).isoformat(),
        }

    return _cached("snapshot", load)


def get_bars(symbol: str, interval: str = "5m", period: str = "5d") -> dict[str, Any]:
    sym = symbol.upper()
    meta = INSTRUMENT_META.get(sym)
    if not meta:
        return {"symbol": sym, "bars": [], "error": "unknown symbol"}

    key = f"bars:{sym}:{interval}:{period}"

    def load() -> dict[str, Any]:
        df = _safe_history(meta["ticker"], period=period, interval=interval)
        if df.empty:
            return {"symbol": sym, "bars": [], "source": "yfinance", "stale": True}
        bars = []
        for idx, row in df.iterrows():
            ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
            if getattr(ts, "tzinfo", None) is None:
                ts = ts.replace(tzinfo=timezone.utc)
            bars.append(
                {
                    "ts": ts.isoformat(),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row.get("Volume", 0) or 0),
                }
            )
        closes = [b["close"] for b in bars]
        sma20 = _rolling_sma(closes, 20)
        return {
            "symbol": sym,
            "interval": interval,
            "period": period,
            "bars": bars,
            "sma20": sma20,
            "source": "yfinance",
            "as_of": datetime.now(timezone.utc).isoformat(),
        }

    return _cached(key, load)


def _rolling_sma(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(values)):
        if i + 1 < window:
            out.append(None)
        else:
            chunk = values[i + 1 - window : i + 1]
            out.append(round(sum(chunk) / window, 2))
    return out


def get_internals_proxy() -> dict[str, Any]:
    """Proxy internals from free tickers — not exchange-native TICK/TRIN."""

    def load() -> dict[str, Any]:
        snap = get_market_snapshot()
        quotes = {q["symbol"]: q for q in snap["instruments"] if q.get("price")}

        vix_df = _safe_history(VIX_TICKER, period="5d", interval="1d")
        vix = float(vix_df.iloc[-1]["Close"]) if not vix_df.empty else None
        vix_prev = float(vix_df.iloc[-2]["Close"]) if len(vix_df) > 1 else vix

        nq_pct = quotes.get("NQ", {}).get("change_pct") or 0.0
        es_pct = quotes.get("ES", {}).get("change_pct") or 0.0
        cl_pct = quotes.get("CL", {}).get("change_pct") or 0.0
        gc_pct = quotes.get("GC", {}).get("change_pct") or 0.0

        # Proxies scaled for dashboard display
        tick_proxy = round((nq_pct - es_pct) * 120 + nq_pct * 40, 0)
        trin_proxy = round(max(0.4, min(2.0, 1.0 - (nq_pct + es_pct) / 4)), 2)
        add_proxy = round(sum(p for p in [nq_pct, es_pct, cl_pct, gc_pct] if p > 0) * 200, 0)
        vold_proxy = round(1.0 + max(nq_pct, es_pct) / 2, 1)

        pos_count = sum(1 for p in [nq_pct, es_pct, cl_pct, gc_pct] if p > 0)
        breadth_score = round(pos_count / 4 * 100)
        regime = "RISK-ON" if breadth_score >= 60 and (vix or 20) < 18 else "RISK-OFF" if breadth_score < 40 else "NEUTRAL"

        vix_term = []
        if not vix_df.empty:
            for i, row in vix_df.tail(6).iterrows():
                vix_term.append({"label": str(i.date()), "value": round(float(row["Close"]), 2)})

        return {
            "source": "yfinance_proxy",
            "disclaimer": "TICK/TRIN/ADD are momentum proxies, not exchange internals.",
            "as_of": datetime.now(timezone.utc).isoformat(),
            "vix": {
                "value": round(vix, 2) if vix else None,
                "change": round((vix - vix_prev), 2) if vix and vix_prev else None,
            },
            "proxies": {
                "tick": int(tick_proxy),
                "trin": trin_proxy,
                "add": int(add_proxy),
                "vold": f"{vold_proxy}:1",
            },
            "breadth_score": breadth_score,
            "regime": regime,
            "regime_confidence": min(95, 50 + breadth_score // 2),
            "vix_term": vix_term,
            "sparklines": _sparkline_series(),
        }

    return _cached("internals", load)


def _sparkline_series() -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    mapping = {
        "tick": ("NQ=F", "Close"),
        "trin": ("ES=F", "Close"),
        "add": ("SPY", "Close"),
        "vold": ("CL=F", "Volume"),
        "vix": (VIX_TICKER, "Close"),
    }
    for key, (ticker, col) in mapping.items():
        df = _safe_history(ticker, period="5d", interval="30m")
        if df.empty or col not in df.columns:
            out[key] = []
        else:
            series = df[col].tail(20).astype(float).tolist()
            out[key] = [round(v, 2) for v in series]
    return out


def get_regime_snapshot() -> dict[str, Any]:
    snap = get_market_snapshot()
    regimes = []
    for q in snap["instruments"]:
        sym = q["symbol"]
        pct = abs(q.get("change_pct") or 0)
        vol = "HIGH" if pct > 0.8 else "NORMAL" if pct > 0.3 else "LOW"
        trend = "TRENDING" if abs(q.get("change_pct") or 0) > 0.4 else "RANGING"
        conf = min(90, 50 + int(pct * 20))
        regimes.append(
            {
                "symbol": sym,
                "volatility": vol,
                "trend": trend,
                "confidence_pct": conf,
                "change_pct": q.get("change_pct"),
            }
        )
    return {"regimes": regimes, "source": "yfinance", "as_of": datetime.now(timezone.utc).isoformat()}


def clear_cache() -> None:
    _cache.clear()


def optional_alpha_vantage_quote(symbol: str) -> dict[str, Any] | None:
    """Optional boost when user sets free Alpha Vantage key (5 calls/min)."""
    key = os.environ.get("ALPHA_VANTAGE_API_KEY", "").strip()
    if not key:
        return None
    # Best-effort only; yfinance remains primary
    try:
        import httpx

        meta = INSTRUMENT_META.get(symbol.upper())
        if not meta:
            return None
        url = "https://www.alphavantage.co/query"
        params = {"function": "GLOBAL_QUOTE", "symbol": meta["ticker"], "apikey": key}
        with httpx.Client(timeout=10.0) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            payload = r.json()
        q = payload.get("Global Quote") or {}
        if not q:
            return None
        return {"symbol": symbol, "source": "alpha_vantage", "raw": q}
    except Exception:
        return None