"""Frontend static content regression checks."""
from __future__ import annotations

from pathlib import Path

STATIC = Path(__file__).resolve().parents[2] / "src" / "mcc" / "interface" / "web" / "static"


def test_no_hardcoded_all_systems_nominal():
    index = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "ALL SYSTEMS NOMINAL" not in index


def test_required_js_modules_referenced():
    index = (STATIC / "index.html").read_text(encoding="utf-8")
    for script in ("system-state.js", "strategies-data.js", "backtest-data.js", "risk-data.js", "decision-data.js"):
        assert script in index


def test_api_routes_mounted():
    from mcc.interface.web import backtest_routes, decision_routes, risk_routes, strategy_routes

    assert strategy_routes.router.prefix == "/api/strategies"
    assert risk_routes.router.prefix == "/api/risk"
    assert decision_routes.router.prefix == "/api/decision"
    assert backtest_routes.router.prefix == "/api/backtests"