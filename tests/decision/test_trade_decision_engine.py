"""Trade decision engine tests."""
from __future__ import annotations

import pytest

from mcc.decision.engine import evaluate_decision
from mcc.risk.command import activate_kill_switch, clear_kill_switch, update_risk_settings
from mcc.storage.repositories import StrategyRepository


@pytest.fixture(autouse=True)
def fresh_market_data(memory_db, monkeypatch):
    monkeypatch.setattr(
        "mcc.decision.engine.build_data_freshness",
        lambda: {
            "sources": {"market_data": {"status": "fresh"}},
            "any_stale": False,
            "critical_stale": False,
        },
    )
    update_risk_settings({"current_day_pnl": 0, "daily_loss_limit": 1500, "drawdown": 0})


def _create_strategy(status: str = "GREEN") -> str:
    import uuid
    sid = f"STR-DEC-{status}-{uuid.uuid4().hex[:6].upper()}"
    s = StrategyRepository().create({
        "strategy_id": sid,
        "name": "Decision Test",
        "instrument": "NQ",
        "timeframe": "15m",
        "hypothesis": "h",
        "entry_rules": "e",
        "exit_rules": "x",
        "risk_rules": "r",
        "status": status,
    })
    return s["strategy_id"]


def test_kill_switch_veto(memory_db, monkeypatch):
    activate_kill_switch()
    result = evaluate_decision({"symbol": "NQ"})
    assert result["decision"] == "NO-GO"
    assert "kill_switch_active" in result["vetoes"]
    clear_kill_switch()


def test_no_strategy_stand_aside(memory_db):
    result = evaluate_decision({"symbol": "NQ"})
    assert result["decision"] == "STAND-ASIDE"
    assert "no_validated_strategy" in result["vetoes"]


def test_strategy_red_veto(memory_db):
    sid = _create_strategy("RED")
    result = evaluate_decision({"symbol": "NQ", "strategy_id": sid})
    assert result["decision"] == "NO-GO"
    assert "strategy_red" in result["vetoes"]


def test_event_lockout_stand_aside(memory_db):
    sid = _create_strategy("GREEN")
    result = evaluate_decision({"symbol": "NQ", "strategy_id": sid, "event_lockout": True})
    assert result["decision"] == "STAND-ASIDE"


def test_daily_loss_veto(memory_db):
    sid = _create_strategy("GREEN")
    update_risk_settings({"current_day_pnl": -2000, "daily_loss_limit": 1500})
    result = evaluate_decision({"symbol": "NQ", "strategy_id": sid})
    assert result["decision"] == "NO-GO"
    assert "daily_loss_limit_hit" in result["vetoes"]


def test_decision_persists(memory_db):
    sid = _create_strategy("GREEN")
    update_risk_settings({"current_day_pnl": 0, "daily_loss_limit": 1500})
    result = evaluate_decision({"symbol": "NQ", "strategy_id": sid, "event_lockout": False})
    assert result.get("decision_id") is not None


def test_factor_scores_present(memory_db):
    sid = _create_strategy("GREEN")
    result = evaluate_decision({"symbol": "NQ", "strategy_id": sid})
    assert "strategy_validation" in result["factor_scores"]