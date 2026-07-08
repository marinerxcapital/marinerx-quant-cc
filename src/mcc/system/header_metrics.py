"""Header KPI metrics — Tradeify sync DB and connector cache only (no fabricated P&L)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcc.data.accounts.tradeify_reader import read_account_state, resolve_tradeify_db_path


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _from_tradeify_reader() -> dict[str, Any] | None:
    path = resolve_tradeify_db_path()
    if path is None:
        return None
    state = read_account_state(path)
    if state.get("error") in ("db_not_found", "no_accounts"):
        return None
    if state.get("error"):
        return None

    day_pnl = _float_or_none(state.get("daily_pnl"))
    week_pnl = _float_or_none(state.get("week_pnl"))
    headroom = _float_or_none(state.get("drawdown_headroom"))
    equity = _float_or_none(state.get("equity") or state.get("balance"))
    balance = _float_or_none(state.get("balance"))

    if equity is None and headroom is None and day_pnl is None:
        return None

    return {
        "day_pnl": day_pnl,
        "week_pnl": week_pnl,
        "drawdown_headroom": headroom,
        "equity": equity,
        "balance": balance,
        "account_id": state.get("account"),
        "observed_at": state.get("last_synced_utc"),
        "stale": bool(state.get("stale", True)),
        "source": "tradeify_sync_db",
        "labeled": True,
    }


def _from_sync_service() -> dict[str, Any] | None:
    try:
        from marinerx_tradeify.sync_service import get_sync_service

        latest = get_sync_service().get_latest()
    except Exception:
        return None

    if not latest or latest.get("status") == "not_available":
        return None

    snap = latest.get("snapshot") or {}
    equity = _float_or_none(snap.get("balance") if snap.get("balance") is not None else snap.get("equity"))
    headroom = _float_or_none(snap.get("drawdown_headroom"))
    if headroom is None and snap.get("balance") is not None and snap.get("eod_drawdown_floor") is not None:
        headroom = float(snap["balance"]) - float(snap["eod_drawdown_floor"])

    day_pnl = _float_or_none(snap.get("realized_day_pnl"))
    week_pnl = _float_or_none(snap.get("week_pnl") or snap.get("realized_week_pnl"))

    if equity is None and headroom is None and day_pnl is None:
        return None

    observed = latest.get("observed_at")
    age: int | None = None
    if observed:
        try:
            ts = datetime.fromisoformat(str(observed).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age = max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
        except (TypeError, ValueError):
            age = None

    stale = age is not None and age > 300

    return {
        "day_pnl": day_pnl,
        "week_pnl": week_pnl,
        "drawdown_headroom": headroom,
        "equity": equity,
        "balance": _float_or_none(snap.get("balance")),
        "account_id": latest.get("account_id_hash"),
        "observed_at": observed,
        "stale": stale,
        "source": "marinerx_tradeify",
        "labeled": True,
    }


def _from_account_sync_agent() -> dict[str, Any] | None:
    try:
        from mcc.agents.snapshots import AgentSnapshotRegistry

        info = AgentSnapshotRegistry.get("AccountSync", {})
        last = info.get("last_state") or {}
        if not last or last.get("error"):
            return None
        equity = _float_or_none(last.get("equity") or last.get("balance"))
        headroom = _float_or_none(last.get("drawdown_headroom"))
        day_pnl = _float_or_none(last.get("daily_pnl"))
        if equity is None and headroom is None and day_pnl is None:
            return None
        return {
            "day_pnl": day_pnl,
            "week_pnl": None,
            "drawdown_headroom": headroom,
            "equity": equity,
            "balance": _float_or_none(last.get("balance")),
            "account_id": last.get("account"),
            "observed_at": last.get("last_synced_utc"),
            "stale": bool(last.get("stale", True)),
            "source": "account_sync_agent",
            "labeled": True,
        }
    except Exception:
        return None


def build_header_metrics() -> dict[str, Any]:
    """Resolve header KPIs from real sync sources; never invent P&L."""
    empty: dict[str, Any] = {
        "day_pnl": None,
        "week_pnl": None,
        "drawdown_headroom": None,
        "equity": None,
        "balance": None,
        "account_id": None,
        "observed_at": None,
        "stale": True,
        "source": "awaiting_sync",
        "labeled": True,
    }

    for loader in (_from_tradeify_reader, _from_sync_service, _from_account_sync_agent):
        data = loader()
        if data:
            has_value = any(
                data.get(k) is not None
                for k in ("day_pnl", "week_pnl", "drawdown_headroom", "equity", "balance")
            )
            if has_value:
                return {**empty, **data, "source": data.get("source", "live")}

    db_hint = os.environ.get("TRADEIFY_SYNC_DB_PATH") or "tradeify-sync/data/tradeify_sync.db"
    return {**empty, "message": f"No account snapshot — run tradeify sync ({db_hint})"}