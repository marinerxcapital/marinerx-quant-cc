"""Risk command service tests."""
from __future__ import annotations

from mcc.risk.command import (
    activate_kill_switch,
    check_order,
    clear_kill_switch,
    get_risk_state,
    update_risk_settings,
)


def test_risk_state_defaults(memory_db):
    state = get_risk_state()
    assert state["kill_switch_active"] is False
    assert state["live_execution_enabled"] is False


def test_kill_switch(memory_db):
    activate_kill_switch()
    assert get_risk_state()["kill_switch_active"] is True
    clear_kill_switch()
    assert get_risk_state()["kill_switch_active"] is False


def test_order_rejected_on_kill_switch(memory_db):
    activate_kill_switch()
    result = check_order({"symbol": "NQ", "side": "BUY", "quantity": 1})
    assert result["result"] == "REJECTED"
    clear_kill_switch()


def test_order_rejected_daily_loss(memory_db):
    update_risk_settings({"current_day_pnl": -2000, "daily_loss_limit": 1500})
    result = check_order({"symbol": "NQ", "side": "BUY", "quantity": 1})
    assert result["result"] == "REJECTED"


def test_order_reduce_size(memory_db):
    update_risk_settings({"max_contracts_per_symbol": 2, "current_day_pnl": 0})
    result = check_order({"symbol": "NQ", "side": "BUY", "quantity": 5})
    assert result["result"] == "REDUCE_SIZE"
    assert result["suggested_quantity"] == 2


def test_live_execution_rejected(memory_db):
    result = check_order({"symbol": "NQ", "side": "BUY", "quantity": 1, "execution_mode": "live"})
    assert result["result"] == "REJECTED"