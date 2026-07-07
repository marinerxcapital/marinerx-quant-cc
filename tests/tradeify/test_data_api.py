from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from mcc.interface.web.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_rules_endpoint(client):
    r = client.get("/api/tradeify/150k/rules")
    assert r.status_code == 200
    body = r.json()
    assert body["evaluation"]["profit_target"] == 9000


def test_data_status_endpoint(client):
    r = client.get("/api/tradeify/150k/data/status")
    assert r.status_code == 200
    body = r.json()
    assert "live_orders_enabled" in body
    assert body["live_orders_enabled"] is False


def test_data_health_endpoint(client):
    r = client.get("/api/tradeify/150k/data/health")
    assert r.status_code == 200
    body = r.json()
    assert body["safe_default"] == "BLOCK_NEW_TRADES"
    assert body["live_orders_enabled"] is False


def test_data_latest_without_sync(client):
    r = client.get("/api/tradeify/150k/data/latest")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") in ("not_available", "cached", "error", "ok")


def test_validate_session_disabled_dashboard(client, monkeypatch):
    monkeypatch.setenv("MARINERX_TRADEIFY_DASHBOARD_ENABLED", "false")
    import marinerx_tradeify.sync_service as sync_mod

    sync_mod._service = None
    r = client.post("/api/tradeify/150k/data/validate-session")
    assert r.status_code == 200
    assert r.json()["status"] == "disabled"


def test_sync_blocks_without_tradovate_credentials(client, monkeypatch):
    monkeypatch.setenv("MARINERX_TRADOVATE_ENABLED", "true")
    monkeypatch.delenv("TRADOVATE_CID", raising=False)
    monkeypatch.delenv("TRADOVATE_SECRET", raising=False)
    monkeypatch.delenv("TRADOVATE_USERNAME", raising=False)
    monkeypatch.delenv("TRADOVATE_PASSWORD", raising=False)
    import marinerx_tradeify.sync_service as sync_mod

    sync_mod._service = None
    r = client.post("/api/tradeify/150k/data/sync")
    assert r.status_code == 200
    body = r.json()
    assert body["safe_default"] == "BLOCK_NEW_TRADES"