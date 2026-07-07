"""Integration: prove BAR/FILL wiring for MarketPulse, IndicatorEngine, TradeJournal, AccountSync."""
from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mcc.core.events import Event, FillEvent, Topic
from mcc.journal.journal import TradeJournal
from mcc.runtime.bootstrap import create_supervisor


def _green_bar_payload(symbol: str = "NQ", price: float = 15010.0) -> dict:
    return {
        "symbol": symbol,
        "o": price - 5,
        "h": price + 2,
        "l": price - 3,
        "c": price,
        "strategy_metrics": {
            "oos_pf": 1.4,
            "dsr": 0.8,
            "folds_positive": 5,
            "n_trades": 120,
        },
        "proxies": {"tick": 250, "trin": 0.82, "add": 180, "vold": "1.2:1", "breadth_score": 72},
    }


def _make_tradeify_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute(
        """
        CREATE TABLE accounts (
            account_id TEXT PRIMARY KEY,
            balance REAL,
            equity REAL,
            drawdown_headroom REAL,
            daily_pnl REAL,
            last_synced_utc TEXT,
            phase TEXT,
            status TEXT
        )
        """
    )
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO accounts
        (account_id, balance, equity, drawdown_headroom, daily_pnl, last_synced_utc, phase, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("demo-150k", 150000.0, 150500.0, 4500.0, 500.0, now, "EVAL", "active"),
    )
    conn.commit()
    conn.close()


@pytest.mark.asyncio
async def test_bar_market_pulse_publishes_internals():
    sup = create_supervisor(replay=True)
    internals: list[Event] = []

    async def collector():
        async for ev in sup.bus.subscribe(Topic.INTERNALS):
            internals.append(ev)
            if len(internals) >= 1:
                break

    coll = asyncio.create_task(collector())
    await sup.start_all()
    await asyncio.sleep(0.2)

    await sup.bus.publish(
        Event(Topic.BAR, datetime.now(timezone.utc), "test", _green_bar_payload())
    )
    await asyncio.sleep(0.5)
    coll.cancel()
    await sup.kill_switch()

    assert len(internals) >= 1
    names = {ev.payload.get("name") for ev in internals}
    assert "breadth_score" in names or "tick" in names
    snap = sup.agents["MarketPulse"].snapshot()
    assert snap.get("breadth_score") is not None or snap.get("regime") is not None


@pytest.mark.asyncio
async def test_bar_indicator_engine_publishes_indicators():
    sup = create_supervisor(replay=True)
    indicator_logs: list[Event] = []

    async def collector():
        async for ev in sup.bus.subscribe(Topic.LOG):
            if ev.source == "IndicatorEngine" and ev.payload.get("type") == "indicators":
                indicator_logs.append(ev)
                if ev.payload.get("values", {}).get("sma20") is not None:
                    break

    coll = asyncio.create_task(collector())
    await sup.start_all()
    await asyncio.sleep(0.2)

    # Feed enough bars for SMA warmup
    for i in range(22):
        payload = _green_bar_payload(price=15000.0 + i)
        await sup.bus.publish(Event(Topic.BAR, datetime.now(timezone.utc), "test", payload))
        await asyncio.sleep(0.02)

    await asyncio.sleep(0.5)
    coll.cancel()
    await sup.kill_switch()

    assert len(indicator_logs) >= 1
    values = indicator_logs[-1].payload.get("values", {})
    assert "sma20" in values
    assert values["sma20"] is not None
    assert "rsi14" in values
    snap = sup.agents["IndicatorEngine"].snapshot()
    assert "NQ" in snap.get("instruments", {})


@pytest.mark.asyncio
async def test_fill_trade_journal_persists(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'journal.db'}"
    sup = create_supervisor(replay=True, journal_db_url=db_url)

    await sup.start_all()
    await asyncio.sleep(0.2)

    fill = FillEvent(
        ts_utc=datetime.now(timezone.utc),
        source="test",
        symbol="NQ",
        side="BUY",
        qty=1,
        price=15010.0,
        pnl=0.0,
    )
    await sup.bus.publish(fill)
    await asyncio.sleep(0.5)

    agent_journal: TradeJournal = sup.agents["TradeJournal"]._journal
    assert agent_journal.count_trades() == 1
    trades = agent_journal.get_trades()
    assert trades[0]["symbol"] == "NQ"
    assert trades[0]["price"] == 15010.0

    await sup.kill_switch()
    agent_journal.engine.dispose()


@pytest.mark.asyncio
async def test_account_sync_reads_fixture_tradeify_db(tmp_path):
    db_path = tmp_path / "tradeify_sync.db"
    _make_tradeify_db(db_path)

    sup = create_supervisor(replay=True, tradeify_db_path=str(db_path))
    account_events: list[Event] = []

    async def collector():
        async for ev in sup.bus.subscribe(Topic.LOG):
            if ev.payload.get("type") == "account_state":
                account_events.append(ev)
                break

    coll = asyncio.create_task(collector())
    await sup.start_all()
    await asyncio.sleep(1.5)
    coll.cancel()
    await sup.kill_switch()

    acct_agent = sup.agents["AccountSync"]
    snap = acct_agent.snapshot()
    assert snap.get("stale") is False
    assert snap.get("last_state", {}).get("equity") == 150500.0
    assert len(account_events) >= 1
    assert account_events[0].payload.get("equity") == 150500.0