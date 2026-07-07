"""Risk command service — kill switch, settings, order checks."""
from __future__ import annotations

from typing import Any

from mcc.core.config import get_settings
from mcc.storage.repositories import RiskRepository

_repo = RiskRepository()


def get_risk_state() -> dict[str, Any]:
    settings = get_settings()
    state = _repo.get_settings()
    state["active_limits"] = {
        "daily_loss_limit": state["daily_loss_limit"],
        "weekly_loss_limit": state["weekly_loss_limit"],
        "max_drawdown_limit": state["max_drawdown_limit"],
        "max_contracts_per_symbol": state["max_contracts_per_symbol"],
        "max_open_positions": state["max_open_positions"],
    }
    state["paper_trading_enabled"] = state.get("paper_trading_enabled", True)
    state["live_execution_enabled"] = settings.enable_live_execution and state.get("live_execution_enabled", False)
    return state


def update_risk_settings(data: dict[str, Any]) -> dict[str, Any]:
    if "live_execution_enabled" in data and data["live_execution_enabled"]:
        settings = get_settings()
        if not settings.enable_live_execution:
            data = {**data, "live_execution_enabled": False}
    result = _repo.update_settings(data)
    _repo.record_event("RISK_SETTINGS_UPDATED", "Risk settings updated", risk_state=result)
    return get_risk_state()


def activate_kill_switch() -> dict[str, Any]:
    _repo.set_kill_switch(True)
    return get_risk_state()


def clear_kill_switch() -> dict[str, Any]:
    _repo.set_kill_switch(False)
    return get_risk_state()


def check_order(payload: dict[str, Any]) -> dict[str, Any]:
    state = get_risk_state()
    symbol = (payload.get("symbol") or "").strip().upper()
    side = (payload.get("side") or "").strip().upper()
    quantity = int(payload.get("quantity") or 0)
    is_live = payload.get("execution_mode") == "live"

    if not symbol:
        return _reject("invalid/missing symbol", state)
    if side not in ("BUY", "SELL"):
        return _reject("invalid order side", state)
    if state["kill_switch_active"]:
        return _reject("kill switch active", state)
    if is_live and not state["live_execution_enabled"]:
        return _reject("live order requested while live execution disabled", state)
    if state["current_day_pnl"] <= -state["daily_loss_limit"]:
        _repo.record_event("DAILY_LIMIT_HIT", "Daily loss limit hit", risk_state=state)
        return _reject("daily loss limit hit", state)
    if state["current_week_pnl"] <= -state["weekly_loss_limit"]:
        return _reject("weekly loss limit hit", state)
    if abs(state["drawdown"]) >= state["max_drawdown_limit"]:
        _repo.record_event("DRAWDOWN_LIMIT_HIT", "Max drawdown exceeded", risk_state=state)
        return _reject("max drawdown exceeded", state)
    if quantity > state["max_contracts_per_symbol"]:
        suggested = state["max_contracts_per_symbol"]
        if suggested > 0:
            event_id = _repo.record_event(
                "ORDER_REDUCED",
                f"Quantity reduced from {quantity} to {suggested}",
                symbol=symbol,
                risk_state=state,
            )
            return {
                "result": "REDUCE_SIZE",
                "reason": "quantity exceeds max_contracts_per_symbol",
                "risk_event_id": event_id,
                "risk_state_snapshot": state,
                "suggested_quantity": suggested,
            }
        return _reject("quantity exceeds max_contracts_per_symbol", state)

    event_id = _repo.record_event("ORDER_APPROVED", f"Order approved: {side} {quantity} {symbol}", symbol=symbol, risk_state=state)
    return {
        "result": "APPROVED",
        "reason": "within risk limits",
        "risk_event_id": event_id,
        "risk_state_snapshot": state,
    }


def _reject(reason: str, state: dict[str, Any]) -> dict[str, Any]:
    event_id = _repo.record_event("ORDER_REJECTED", reason, risk_state=state, severity="warning")
    return {
        "result": "REJECTED",
        "reason": reason,
        "risk_event_id": event_id,
        "risk_state_snapshot": state,
    }