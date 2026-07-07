"""Backtest API route tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from mcc.interface.web.server import app

client = TestClient(app)


def test_backtest_route(memory_db):
    r = client.post("/api/strategies", json={
        "name": "BT", "instrument": "NQ", "timeframe": "15m",
        "hypothesis": "h", "entry_rules": "e", "exit_rules": "x", "risk_rules": "r",
    })
    sid = r.json()["strategy_id"]
    r = client.post("/api/backtests/run", json={"strategy_id": sid, "use_demo_data": True})
    assert r.status_code == 200
    body = r.json()
    assert "config_hash" in body
    assert body["backtest_run_id"] is not None

    r = client.post("/api/backtests/run", json={"strategy_id": "MISSING"})
    assert r.status_code == 404