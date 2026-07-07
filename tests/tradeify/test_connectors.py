from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from marinerx_tradeify.connectors.base import BrokerAccountMetrics, TradeifyDashboardMetrics
from marinerx_tradeify.connectors.normalizer import check_stale, merge_with_reconciliation, reconcile
from marinerx_tradeify.connectors.tradeify_dashboard_connector import parse_dashboard_html
from marinerx_tradeify.connectors.tradovate_connector import (
    TradovateAuthError,
    TradovateConfig,
    TradovateConfigurationError,
    TradovateConnector,
)


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "tradeify_dashboard.html"


def test_tradovate_missing_credentials_blocks():
    cfg = TradovateConfig(cid=None, secret=None, username=None, password=None)
    with pytest.raises(TradovateConfigurationError):
        cfg.validate_credentials()


@pytest.mark.asyncio
async def test_tradovate_auth_failure(monkeypatch):
    cfg = TradovateConfig(
        cid="1",
        secret="sec",
        username="user",
        password="pass",
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    conn = TradovateConnector(cfg, client=client)
    with pytest.raises(TradovateAuthError):
        await conn.authenticate()
    await conn.close()


@pytest.mark.asyncio
async def test_tradovate_balance_parsing():
    cfg = TradovateConfig(cid="1", secret="s", username="u", password="p")

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/accesstokenrequest"):
            return httpx.Response(200, json={"accessToken": "tok"})
        if request.url.path.endswith("/account/list"):
            return httpx.Response(200, json=[{"id": 99, "name": "Tradeify 150K"}])
        if request.url.path.endswith("/cashBalance/list"):
            return httpx.Response(
                200,
                json=[{"accountId": 99, "amount": 154000.0, "realizedPnL": 320.0, "openPnL": 50.0}],
            )
        if request.url.path.endswith("/position/list"):
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    conn = TradovateConnector(cfg, client=client)
    metrics = await conn.build_broker_metrics(99)
    assert metrics.balance == 154000.0
    assert metrics.realized_day_pnl == 320.0
    await conn.close()


def test_dashboard_html_fixture_parsing():
    html = FIXTURE.read_text(encoding="utf-8")
    rows = parse_dashboard_html(html, "150K")
    assert len(rows) == 1
    row = rows[0]
    assert "150K" in row["account_label"]
    assert row["current_balance"] == pytest.approx(154320.50)
    assert row["realized_day_pnl"] == pytest.approx(420.0)
    assert row["winning_days"] == 3


def test_reconciliation_passes_within_tolerance():
    now = datetime.now(timezone.utc)
    broker = BrokerAccountMetrics(
        source="tradovate_api",
        account_name="T",
        account_id_hash="abc",
        balance=154000.0,
        net_liq=154000.0,
        cash_balance=154000.0,
        realized_day_pnl=420.0,
        unrealized_pnl=0.0,
        open_trade_risk=0.0,
        eod_drawdown_floor=150100.0,
        observed_at=now,
    )
    dashboard = TradeifyDashboardMetrics(
        source="tradeify_dashboard",
        account_label="150K",
        phase="FUNDED_FLEX",
        account_size=150000,
        current_balance=154010.0,
        realized_day_pnl=425.0,
        total_profit=4320.0,
        max_drawdown_limit=4500.0,
        drawdown_floor=150100.0,
        winning_days=3,
        payout_eligible=True,
        next_payout_cap=5000.0,
        last_payout_status=None,
        consistency_current_pct=28.0,
        observed_at=now,
    )
    rec = reconcile(broker, dashboard)
    assert rec.ok is True
    assert rec.block_trades is False


def test_reconciliation_blocks_on_large_mismatch():
    now = datetime.now(timezone.utc)
    broker = BrokerAccountMetrics(
        source="tradovate_api",
        account_name="T",
        account_id_hash="abc",
        balance=154000.0,
        net_liq=154000.0,
        cash_balance=154000.0,
        realized_day_pnl=420.0,
        unrealized_pnl=0.0,
        open_trade_risk=0.0,
        eod_drawdown_floor=150100.0,
        observed_at=now,
    )
    dashboard = TradeifyDashboardMetrics(
        source="tradeify_dashboard",
        account_label="150K",
        phase="FUNDED_FLEX",
        account_size=150000,
        current_balance=153000.0,
        realized_day_pnl=100.0,
        total_profit=3000.0,
        max_drawdown_limit=4500.0,
        drawdown_floor=150100.0,
        winning_days=3,
        payout_eligible=True,
        next_payout_cap=5000.0,
        last_payout_status=None,
        consistency_current_pct=28.0,
        observed_at=now,
    )
    rec = reconcile(broker, dashboard)
    assert rec.ok is False
    assert rec.block_trades is True


def test_stale_data_blocks():
    old = datetime.now(timezone.utc) - timedelta(seconds=300)
    stale, reason = check_stale(old)
    assert stale is True
    assert "STALE" in reason


def test_live_orders_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MARINERX_ALLOW_LIVE_ORDERS", raising=False)
    from marinerx_tradeify.sync_service import TradeifyDataSyncService

    svc = TradeifyDataSyncService()
    assert svc.live_orders_enabled is False