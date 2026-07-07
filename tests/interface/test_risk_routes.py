"""Risk API route tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from mcc.interface.web.server import app

client = TestClient(app)


def test_risk_routes(memory_db):
    r = client.get("/api/risk/state")
    assert r.status_code == 200
    assert "kill_switch_active" in r.json()

    r = client.post("/api/risk/kill-switch")
    assert r.status_code == 200
    assert r.json()["kill_switch_active"] is True

    r = client.post("/api/risk/clear-kill-switch")
    assert r.json()["kill_switch_active"] is False

    r = client.post("/api/risk/check-order", json={"symbol": "NQ", "side": "BUY", "quantity": 1})
    assert r.status_code == 200
    assert r.json()["result"] in ("APPROVED", "REJECTED", "REDUCE_SIZE")