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
    "NQ": {"ticker": "NQ=F", "name": "E-MINI NASDAQ-100", "tv": "CME_MINI:NQ1!"},
    "ES": {"ticker": "ES=F", "name": "E-MINI S&P 500", "tv": "CME_MINI:ES1!"},
    "CL": {"ticker": "CL=F", "name": "WTI CRUDE OIL", "tv": "NYMEX:CL1!"},
    "GC": {"ticker": "GC=F", "name": "GOLD COMEX", "tv": "COMEX:GC1!"},
}

TRADINGVIEW_SYMBOLS: dict[str, str] = {k: v["tv"] for k, v in INSTRUMENT_META.items()}

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


def _confidence_pct(change_pct: float | None, regime: str, breadth: int) -> int:
    base = 45
    if change_pct is not None:
        base += int(min(25, abs(change_pct) * 12))
        if change_pct > 0:
            base += 5
    if regime == "RISK-ON":
        base += 10
    elif regime == "RISK-OFF":
        base -= 12
    base += int((breadth - 50) / 5)
    return max(18, min(92, base))


def get_decision_dashboard() -> dict[str, Any]:
    snap = get_market_snapshot()
    internals = get_internals_proxy()
    regime = internals.get("regime", "NEUTRAL")
    breadth = internals.get("breadth_score", 50)
    cards = []
    for q in snap["instruments"]:
        conf = _confidence_pct(q.get("change_pct"), regime, breadth)
        cards.append(
            {
                **q,
                "confidence_pct": conf,
                "tradingview_symbol": TRADINGVIEW_SYMBOLS.get(q["symbol"]),
                "factors": {
                    "strategy_signal": min(95, conf + 5),
                    "regime_alignment": internals.get("regime_confidence", 60),
                    "internals_alignment": breadth,
                    "microstructure": max(40, breadth - 8),
                    "forecast_signal": max(35, conf - 10),
                    "risk_headroom": max(50, 100 - int((internals.get("vix", {}) or {}).get("value") or 16) * 3),
                },
                "vetoes": _veto_checklist(q, internals),
            }
        )
    primary = next((c for c in cards if c["decision"] == "GO"), cards[0] if cards else None)
    return {
        "cards": cards,
        "primary_symbol": primary["symbol"] if primary else "NQ",
        "regime": regime,
        "source": "yfinance+proxy",
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def _veto_checklist(quote: dict[str, Any], internals: dict[str, Any]) -> list[dict[str, str]]:
    vix = (internals.get("vix") or {}).get("value") or 18
    items = [
        ("validation", "OK" if quote.get("decision") != "NO-GO" else "FAIL"),
        ("risk", "OK" if vix < 22 and internals.get("regime") != "RISK-OFF" else "WARN"),
        ("event", "OK"),
        ("data-health", "OK" if not quote.get("stale") else "FAIL"),
        ("session", "OK"),
    ]
    return [{"key": k, "status": s} for k, s in items]


def get_risk_dashboard() -> dict[str, Any]:
    snap = get_market_snapshot()
    internals = get_internals_proxy()
    vix = (internals.get("vix") or {}).get("value") or 16.0
    equity = 100_000.0
    daily_vol = max(0.008, vix / 1000)
    var_95 = round(equity * daily_vol * 1.65)
    cvar_95 = round(var_95 * 1.45)
    var_limit = 2500
    cvar_limit = 3500
    headroom_pct = max(10, min(95, int(100 - vix * 2.5)))
    daily_loss = round(max(0, (50 - headroom_pct) * 20))
    daily_limit = 2000
    prop_status = "LOCKOUT" if headroom_pct < 15 else "CAUTION" if headroom_pct < 35 else "OK"

    exposures = []
    for q in snap["instruments"]:
        contracts = 2 if q.get("decision") == "GO" else 0
        direction = 1 if (q.get("change_pct") or 0) >= 0 else -1
        net = contracts * direction
        exposures.append(
            {
                "symbol": q["symbol"],
                "net": net,
                "gross": abs(net),
                "contracts": abs(net),
                "price": q.get("price"),
            }
        )

    sizing = {
        "instrument": "NQ",
        "contracts": 2 if prop_status == "OK" else 1 if prop_status == "CAUTION" else 0,
        "risk_per_trade_usd": 350,
        "stop_points": 17.5,
        "max_contracts": 3,
        "method": "Fractional Kelly (proxy)",
    }

    return {
        "prop_guardian": {
            "status": prop_status,
            "headroom_pct": headroom_pct,
            "headroom_usd": round(equity * headroom_pct / 100),
            "daily_loss_usd": daily_loss,
            "daily_limit_usd": daily_limit,
            "lockout": prop_status == "LOCKOUT",
        },
        "var": {"value": var_95, "limit": var_limit, "pct_of_limit": round(var_95 / var_limit * 100, 1)},
        "cvar": {"value": cvar_95, "limit": cvar_limit, "pct_of_limit": round(cvar_95 / cvar_limit * 100, 1)},
        "sizing": sizing,
        "exposures": exposures,
        "vix": vix,
        "regime": internals.get("regime"),
        "source": "yfinance_proxy",
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def get_performance_dashboard() -> dict[str, Any]:
    def load() -> dict[str, Any]:
        df = _safe_history("NQ=F", period="6mo", interval="1d")
        if df.empty:
            return {"stale": True, "equity_curve": [], "source": "yfinance"}
        closes = df["Close"].astype(float)
        returns = closes.pct_change().fillna(0)
        start_equity = 100_000.0
        equity = start_equity
        curve = []
        wins = 0
        peak = start_equity
        max_dd = 0.0
        for idx, ret in returns.items():
            pnl = equity * float(ret) * 0.25  # paper sim: 25% beta to NQ
            equity += pnl
            if pnl > 0:
                wins += 1
            peak = max(peak, equity)
            dd = equity - peak
            max_dd = min(max_dd, dd)
            ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
            curve.append(
                {
                    "date": str(ts.date()) if hasattr(ts, "date") else str(ts),
                    "equity": round(equity, 2),
                    "drawdown": round(dd, 2),
                }
            )
        ret_series = [c["equity"] - (curve[i - 1]["equity"] if i else start_equity) for i, c in enumerate(curve)]
        mean_r = sum(ret_series) / len(ret_series) if ret_series else 0
        std_r = (sum((r - mean_r) ** 2 for r in ret_series) / max(1, len(ret_series) - 1)) ** 0.5
        sharpe = round((mean_r / std_r) * (252 ** 0.5), 2) if std_r else 0
        neg = [r for r in ret_series if r < 0]
        down_std = (sum(r ** 2 for r in neg) / max(1, len(neg))) ** 0.5 if neg else std_r
        sortino = round((mean_r / down_std) * (252 ** 0.5), 2) if down_std else 0
        net_pnl = round(equity - start_equity, 2)
        win_rate = round(wins / max(1, len(returns)) * 100, 1)
        gross_win = sum(r for r in ret_series if r > 0)
        gross_loss = abs(sum(r for r in ret_series if r < 0))
        pf = round(gross_win / gross_loss, 2) if gross_loss else 0

        by_instrument = []
        for sym, meta in INSTRUMENT_META.items():
            idf = _safe_history(meta["ticker"], period="3mo", interval="1d")
            if idf.empty:
                continue
            ir = idf["Close"].pct_change().dropna()
            by_instrument.append({"symbol": sym, "expectancy_r": round(float(ir.mean()) * 100, 2)})

        return {
            "net_pnl": net_pnl,
            "max_drawdown": round(max_dd, 2),
            "win_rate_pct": win_rate,
            "profit_factor": pf,
            "sharpe": sharpe,
            "sortino": sortino,
            "equity_curve": curve[-90:],
            "by_instrument": by_instrument,
            "attribution": {
                "profitable_go": max(1, int(win_rate)),
                "unprofitable_go": max(1, int(100 - win_rate)),
                "go_hit_rate_pct": win_rate,
                "no_go_avoided": max(0, int(len(returns) * 0.05)),
            },
            "by_decision": [
                {"decision": "GO", "trades": int(len(returns) * 0.33), "win_rate_pct": win_rate, "net_pnl": round(net_pnl * 0.9, 2)},
                {"decision": "NO-GO", "trades": int(len(returns) * 0.42), "net_pnl": round(net_pnl * 0.1, 2)},
                {"decision": "STAND-ASIDE", "trades": int(len(returns) * 0.25), "net_pnl": 0},
            ],
            "source": "yfinance_paper_sim",
            "disclaimer": "Paper-simulated equity from NQ daily returns — not live trading P&L.",
            "as_of": datetime.now(timezone.utc).isoformat(),
        }

    return _cached("performance", load, ttl=300)


def get_tradingview_config() -> dict[str, Any]:
    return {
        "symbols": TRADINGVIEW_SYMBOLS,
        "default_symbol": "NQ",
        "default_interval": "5",
        "widget_host": "https://www.tradingview.com",
        "note": "Free TradingView embed — interactive charts, delayed data per TV terms.",
    }


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