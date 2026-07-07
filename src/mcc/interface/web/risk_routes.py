"""Risk Command API routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mcc.risk.command import (
    activate_kill_switch,
    check_order,
    clear_kill_switch,
    get_risk_state,
    update_risk_settings,
)

router = APIRouter(prefix="/api/risk", tags=["risk"])


class RiskSettingsUpdate(BaseModel):
    daily_loss_limit: float | None = None
    weekly_loss_limit: float | None = None
    max_drawdown_limit: float | None = None
    risk_per_trade_pct: float | None = None
    max_contracts_per_symbol: int | None = None
    max_open_positions: int | None = None
    lockout_after_loss_count: int | None = None
    paper_trading_enabled: bool | None = None
    live_execution_enabled: bool | None = None
    current_day_pnl: float | None = None
    current_week_pnl: float | None = None
    drawdown: float | None = None


class OrderCheckRequest(BaseModel):
    symbol: str
    side: str
    quantity: int
    order_type: str = "MARKET"
    limit_price: float | None = None
    stop_price: float | None = None
    strategy_id: str = ""
    account_id: str | None = None
    linked_decision_id: int | None = None
    execution_mode: str = "paper"


@router.get("/state")
def risk_state() -> dict[str, Any]:
    return get_risk_state()


@router.post("/settings")
def risk_settings(body: RiskSettingsUpdate) -> dict[str, Any]:
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return update_risk_settings(data)


@router.post("/kill-switch")
def kill_switch_on() -> dict[str, Any]:
    return activate_kill_switch()


@router.post("/clear-kill-switch")
def kill_switch_off() -> dict[str, Any]:
    return clear_kill_switch()


@router.post("/check-order")
def order_check(body: OrderCheckRequest) -> dict[str, Any]:
    return check_order(body.model_dump())