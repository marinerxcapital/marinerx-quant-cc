"""Strategy Registry API tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from mcc.interface.web.server import app

client = TestClient(app)

PAYLOAD = {
    "name": "NQ ORB",
    "instrument": "NQ",
    "timeframe": "15m",
    "hypothesis": "ORB edge",
    "entry_rules": "break high",
    "exit_rules": "target",
    "risk_rules": "350",
}


def test_strategy_crud_flow(memory_db):
    r = client.get("/api/strategies")
    assert r.status_code == 200
    assert r.json()["count"] == 0

    r = client.post("/api/strategies", json=PAYLOAD)
    assert r.status_code == 200
    sid = r.json()["strategy_id"]

    r = client.get(f"/api/strategies/{sid}")
    assert r.status_code == 200
    assert r.json()["name"] == "NQ ORB"

    r = client.patch(f"/api/strategies/{sid}", json={"status": "GREEN"})
    assert r.status_code == 200

    r = client.post(f"/api/strategies/{sid}/archive")
    assert r.status_code == 200
    assert r.json()["status"] == "ARCHIVED"

    r = client.get("/api/strategies/missing-id")
    assert r.status_code == 404

    r = client.patch("/api/strategies/missing-id", json={"name": "x"})
    assert r.status_code == 404


def test_invalid_status(memory_db):
    r = client.post("/api/strategies", json=PAYLOAD)
    sid = r.json()["strategy_id"]
    r = client.patch(f"/api/strategies/{sid}", json={"status": "INVALID"})
    assert r.status_code == 422