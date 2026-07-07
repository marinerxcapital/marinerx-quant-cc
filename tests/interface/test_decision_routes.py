"""Decision API route tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from mcc.interface.web.server import app

client = TestClient(app)


def test_decision_evaluate_route(memory_db):
    r = client.post("/api/decision/evaluate", json={"symbol": "NQ"})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] in ("GO", "NO-GO", "STAND-ASIDE")
    assert "factor_scores" in body
    assert body.get("decision_id") is not None