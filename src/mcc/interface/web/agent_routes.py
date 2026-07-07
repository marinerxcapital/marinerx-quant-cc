"""REST endpoints for agent-backed dashboard data (supervisor + DB + Tradeify)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from mcc.data.live.free_market import (
    INSTRUMENT_META,
    get_bars,
    get_internals_proxy,
    get_regime_snapshot,
)
from mcc.storage.database import get_engine
from mcc.storage.models import DecisionLog, ReportMetadata, Strategy, Trade
from marinerx_tradeify.sync_service import get_sync_service

router = APIRouter(prefix="/api", tags=["agent-data"])

STALE_WARN_SEC = 60
STALE_BLOCK_SEC = 180


def _get_supervisor() -> Any:
    from mcc.interface.web import server

    sup = server._SUP
    if sup is None:
        from mcc.runtime.bootstrap import create_supervisor

        sup = create_supervisor(replay=True)
    return sup


def _status_badge(status: str | None) -> str:
    if status == "working":
        return "green"
    if status == "error":
        return "red"
    if status in {"stopped", "blocked"}:
        return "red"
    if status in {"idle", "noop"}:
        return "neutral"
    return "blue"


def _status_label(status: str | None) -> str:
    mapping = {
        "working": "Running",
        "idle": "Idle",
        "stopped": "Stopped",
        "error": "Error",
    }
    return mapping.get(status or "", (status or "unknown").title())


def _age_seconds(iso_ts: str | None) -> int | None:
    if not iso_ts:
        return None
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
    except (TypeError, ValueError):
        return None


def _stale_flag(iso_ts: str | None) -> bool:
    age = _age_seconds(iso_ts)
    if age is None:
        return True
    return age > STALE_WARN_SEC


def _count_trades() -> int:
    try:
        with get_engine().connect() as conn:
            return int(conn.execute(select(func.count()).select_from(Trade)).scalar() or 0)
    except Exception:
        return 0


def _fetch_trades(limit: int = 50) -> list[dict[str, Any]]:
    try:
        with Session(get_engine()) as session:
            trades = session.scalars(
                select(Trade).order_by(desc(Trade.ts_utc)).limit(max(1, min(limit, 200)))
            ).all()
        out: list[dict[str, Any]] = []
        for trade in trades:
            ts = trade.ts_utc
            if ts and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            ts_iso = ts.isoformat() if ts else None
            out.append(
                {
                    "id": trade.id,
                    "ts_utc": ts_iso,
                    "date": ts.date().isoformat() if ts else None,
                    "time": ts.strftime("%H:%M:%S") if ts else None,
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "qty": trade.qty,
                    "price": trade.price,
                    "pnl": trade.pnl,
                    "setup_tag": "—",
                    "strategy_id": "—",
                    "regime": "—",
                    "decision": "GO" if (trade.pnl or 0) >= 0 else "NO-GO",
                }
            )
        return out
    except Exception:
        return []


def _fetch_strategies() -> list[dict[str, Any]]:
    try:
        with Session(get_engine()) as session:
            strategies = session.scalars(select(Strategy)).all()
        return [{"id": s.id, "status": s.status} for s in strategies]
    except Exception:
        return []


def _fetch_decision_logs(limit: int = 20) -> list[dict[str, Any]]:
    try:
        with Session(get_engine()) as session:
            logs = session.scalars(
                select(DecisionLog).order_by(desc(DecisionLog.ts_utc)).limit(max(1, min(limit, 100)))
            ).all()
        out: list[dict[str, Any]] = []
        for log in logs:
            ts = log.ts_utc
            if ts and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            out.append(
                {
                    "symbol": log.symbol,
                    "decision": log.decision,
                    "reason": log.reason,
                    "vetoes": log.vetoes,
                    "ts_utc": ts.isoformat() if ts else None,
                }
            )
        return out
    except Exception:
        return []


def _fetch_reports(limit: int = 20) -> list[dict[str, Any]]:
    try:
        with Session(get_engine()) as session:
            reports = session.scalars(
                select(ReportMetadata).order_by(desc(ReportMetadata.ts_utc)).limit(max(1, min(limit, 100)))
            ).all()
        out: list[dict[str, Any]] = []
        for rep in reports:
            ts = rep.ts_utc
            if ts and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            out.append(
                {
                    "id": rep.id,
                    "report_type": rep.report_type,
                    "object_key": rep.object_key,
                    "storage_backend": rep.storage_backend,
                    "size_bytes": rep.size_bytes,
                    "ts_utc": ts.isoformat() if ts else None,
                }
            )
        return out
    except Exception:
        return []


def _agent_metric(name: str, info: dict[str, Any], trade_count: int, internals: dict[str, Any]) -> str:
    status = info.get("status", "unknown")
    task = info.get("task") or ""
    if name == "MarketPulse":
        tick = (internals.get("proxies") or {}).get("tick")
        return f"Events/min {abs(int(tick or 0)):,}" if tick is not None else "Awaiting sync"
    if name == "TradeJournal":
        return f"Today Trades {trade_count}" if trade_count else "Awaiting sync"
    if name == "IndicatorEngine":
        return "Indicators live" if status == "working" else "Awaiting sync"
    if name == "RegimeMonitor":
        regime = internals.get("regime", "NEUTRAL")
        return f"Regime {regime}"
    if name == "ValidationEngine":
        return task or "Awaiting sync"
    if name == "ReportPublisher":
        return "Blocked" if status == "stopped" else (task or "Awaiting sync")
    if task:
        return task
    return "Awaiting sync" if status == "idle" else _status_label(status)


def _ema(values: list[float], span: int) -> float | None:
    if not values:
        return None
    alpha = 2 / (span + 1)
    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1 - alpha) * ema
    return round(ema, 4)


def _sma(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    chunk = values[-window:]
    return round(sum(chunk) / len(chunk), 4)


def _rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _macd(values: list[float]) -> dict[str, float | None]:
    if len(values) < 26:
        return {"macd": None, "signal": None, "histogram": None}
    ema12 = _ema(values, 12)
    ema26 = _ema(values, 26)
    if ema12 is None or ema26 is None:
        return {"macd": None, "signal": None, "histogram": None}
    macd_line = round(ema12 - ema26, 4)
    # signal line approximation from last macd samples
    macd_samples = []
    for i in range(26, len(values) + 1):
        chunk = values[:i]
        e12 = _ema(chunk, 12)
        e26 = _ema(chunk, 26)
        if e12 is not None and e26 is not None:
            macd_samples.append(e12 - e26)
    signal = _ema(macd_samples, 9) if macd_samples else None
    hist = round(macd_line - signal, 4) if signal is not None else None
    return {"macd": macd_line, "signal": signal, "histogram": hist}


def _compute_indicators(bars_data: dict[str, Any]) -> dict[str, Any]:
    bars = bars_data.get("bars") or []
    closes = [float(b["close"]) for b in bars if b.get("close") is not None]
    if not closes:
        return {"sync_status": "awaiting_sync", "values": {}}
    last = closes[-1]
    return {
        "sync_status": "live",
        "values": {
            "close": round(last, 2),
            "sma_20": _sma(closes, 20),
            "ema_50": _ema(closes, 50),
            "rsi_14": _rsi(closes, 14),
            "macd": _macd(closes),
            "sma20_series": bars_data.get("sma20"),
        },
        "bar_count": len(closes),
    }


@router.get("/agents/snapshot")
def agents_snapshot() -> dict[str, Any]:
    sup = _get_supervisor()
    snap = sup.snapshot()
    trade_count = _count_trades()
    internals = get_internals_proxy()

    agents: dict[str, dict[str, Any]] = {}
    for name, info in snap.agents.items():
        status = info.get("status", "unknown")
        agents[name] = {
            "status": status,
            "task": info.get("task"),
            "label": _status_label(status),
            "badge": _status_badge(status),
            "metric": _agent_metric(name, info, trade_count, internals),
        }

    return {
        "agents": agents,
        "kill_active": snap.kill_active,
        "ts": snap.ts_utc.isoformat(),
        "agent_count": len(agents),
        "strategies": _fetch_strategies(),
        "decision_logs": _fetch_decision_logs(10),
        "reports": _fetch_reports(10),
    }


@router.get("/agents/market-pulse")
def market_pulse() -> dict[str, Any]:
    sup = _get_supervisor()
    agent_info = sup.snapshot().agents.get("MarketPulse", {})
    pulse = get_internals_proxy()
    return {
        "agent": "MarketPulse",
        "status": agent_info.get("status", "unknown"),
        "task": agent_info.get("task"),
        "snapshot": pulse,
        "sync_status": "live" if pulse.get("as_of") and not _stale_flag(pulse.get("as_of")) else "awaiting_sync",
        "as_of": pulse.get("as_of"),
    }


@router.get("/agents/indicators/{symbol}")
def indicators(symbol: str) -> dict[str, Any]:
    sym = symbol.upper()
    if sym not in INSTRUMENT_META:
        raise HTTPException(status_code=404, detail=f"Unknown symbol: {sym}")

    bars_data = get_bars(sym)
    indicator_values = _compute_indicators(bars_data)
    regime_data = get_regime_snapshot()
    regime = next((r for r in regime_data.get("regimes", []) if r.get("symbol") == sym), None)
    agent_info = _get_supervisor().snapshot().agents.get("IndicatorEngine", {})

    return {
        "symbol": sym,
        "agent": "IndicatorEngine",
        "status": agent_info.get("status"),
        "task": agent_info.get("task"),
        "indicators": indicator_values,
        "regime": regime,
        "bars_count": len(bars_data.get("bars") or []),
        "as_of": bars_data.get("as_of"),
        "source": bars_data.get("source", "yfinance"),
    }


@router.get("/agents/journal")
def journal(limit: int = 50) -> dict[str, Any]:
    trades = _fetch_trades(limit)
    agent_info = _get_supervisor().snapshot().agents.get("TradeJournal", {})
    return {
        "agent": "TradeJournal",
        "status": agent_info.get("status"),
        "task": agent_info.get("task"),
        "trades": trades,
        "count": len(trades),
        "sync_status": "live" if trades else "awaiting_sync",
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/account/sync")
def account_sync() -> dict[str, Any]:
    svc = get_sync_service()
    latest = svc.get_latest()
    observed_at = latest.get("observed_at")
    age_sec = _age_seconds(observed_at)
    stale = _stale_flag(observed_at)
    stale_block = age_sec is not None and age_sec > STALE_BLOCK_SEC

    snap = latest.get("snapshot") or {}
    equity = snap.get("balance") if snap.get("balance") is not None else snap.get("equity")
    drawdown = snap.get("drawdown")
    headroom = snap.get("drawdown_headroom")
    if headroom is None and snap.get("balance") is not None and snap.get("eod_drawdown_floor") is not None:
        headroom = float(snap["balance"]) - float(snap["eod_drawdown_floor"])

    day_pnl = snap.get("realized_day_pnl")
    week_pnl = snap.get("week_pnl") or snap.get("realized_week_pnl")

    reconciliation = latest.get("reconciliation") or {}
    return {
        "status": latest.get("status", "not_available"),
        "stale": stale,
        "stale_block": stale_block,
        "age_seconds": age_sec,
        "observed_at": observed_at,
        "equity": equity,
        "drawdown": drawdown,
        "drawdown_headroom": headroom,
        "day_pnl": day_pnl,
        "week_pnl": week_pnl,
        "safe_default": latest.get("safe_default", "BLOCK_NEW_TRADES"),
        "reconciliation_ok": reconciliation.get("ok"),
        "block_trades": reconciliation.get("block_trades", True),
        "message": latest.get("message"),
        "sync_status": "live" if not stale and equity is not None else "awaiting_sync",
    }