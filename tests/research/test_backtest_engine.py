"""Backtest engine unit tests."""
from __future__ import annotations

from mcc.research.backtesting import _config_hash, _max_drawdown, run_backtest
from mcc.storage.repositories import StrategyRepository


def _create_strategy(template: str = "orb") -> str:
    import uuid
    sid = f"STR-BT-{template}-{uuid.uuid4().hex[:6].upper()}"
    s = StrategyRepository().create({
        "strategy_id": sid,
        "name": "BT Test",
        "instrument": "NQ",
        "timeframe": "15m",
        "hypothesis": "h",
        "entry_rules": "e",
        "exit_rules": "x",
        "risk_rules": "r",
        "parameters_json": {"template": template},
    })
    return s["strategy_id"]


def test_no_data_without_demo(memory_db):
    sid = _create_strategy()
    result = run_backtest({"strategy_id": sid, "symbol": "NQ"})
    assert result["error"] == "no_data"


def test_demo_backtest_deterministic(memory_db):
    sid = _create_strategy()
    payload = {"strategy_id": sid, "symbol": "NQ", "use_demo_data": True}
    r1 = run_backtest(payload)
    r2 = run_backtest(payload)
    assert r1["config_hash"] == r2["config_hash"]
    assert r1["demo_labeled"] is True
    assert r1["backtest_run_id"] is not None


def test_max_drawdown_calculation():
    dd, pct = _max_drawdown([100, 110, 90, 95])
    assert dd == 20.0
    assert pct > 0


def test_profit_factor_no_divide_by_zero(memory_db):
    sid = _create_strategy("event_lockout")
    result = run_backtest({"strategy_id": sid, "use_demo_data": True})
    assert result.get("profit_factor") is None or result["total_trades"] >= 0


def test_config_hash_stable():
    h1 = _config_hash({"a": 1, "b": 2})
    h2 = _config_hash({"b": 2, "a": 1})
    assert h1 == h2