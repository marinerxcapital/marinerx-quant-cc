"""Persistence layer tests."""
from __future__ import annotations

from datetime import datetime, timezone

from mcc.storage.repositories import (
    BacktestRepository,
    DecisionRepository,
    InstrumentRepository,
    JournalRepository,
    MarketBarRepository,
    ReportRepository,
    RiskRepository,
    StrategyRepository,
)


def _strategy_payload(sid: str | None = None) -> dict:
    import uuid
    sid = sid or f"STR-TEST-{uuid.uuid4().hex[:8].upper()}"
    return {
        "strategy_id": sid,
        "name": "Test ORB",
        "instrument": "NQ",
        "timeframe": "15m",
        "hypothesis": "ORB works",
        "entry_rules": "break OR",
        "exit_rules": "EOD",
        "risk_rules": "350 stop",
    }


def test_strategy_crud_and_archive(memory_db):
    repo = StrategyRepository()
    sid = "STR-TEST-CRUD-001"
    created = repo.create(_strategy_payload(sid))
    assert created["strategy_id"] == sid
    assert created["status"] == "DRAFT"

    updated = repo.update(sid, {"status": "GREEN", "latest_verdict": "PASS"})
    assert updated["status"] == "GREEN"

    listed = repo.list_strategies()
    assert len(listed) == 1

    archived = repo.archive(sid)
    assert archived["status"] == "ARCHIVED"
    assert repo.list_strategies(include_archived=False) == []


def test_backtest_and_decision_persistence(memory_db):
    sid = "STR-TEST-BT-001"
    StrategyRepository().create(_strategy_payload(sid))
    bt = BacktestRepository().save_run({
        "strategy_id": sid,
        "symbol": "NQ",
        "metrics": {"total_trades": 5},
        "equity_curve": [100000, 100350],
        "trade_list": [],
        "config_hash": "abc123",
    })
    assert bt["id"] is not None

    dec = DecisionRepository().save({
        "symbol": "NQ",
        "strategy_id": sid,
        "decision": "GO",
        "confidence": 0.8,
        "rationale": "test",
        "vetoes": [],
        "factor_scores": {"strategy_validation": 90},
    })
    assert dec["decision_id"] is not None
    assert DecisionRepository().get_latest("NQ") is not None


def test_risk_journal_report_persistence(memory_db):
    risk = RiskRepository()
    settings = risk.get_settings()
    assert settings["kill_switch_active"] is False
    risk.set_kill_switch(True)
    assert risk.get_settings()["kill_switch_active"] is True
    eid = risk.record_event("ORDER_REJECTED", "test reject")
    assert eid > 0

    journal = JournalRepository().create({"symbol": "NQ", "setup": "ORB"})
    assert journal["entry_id"]

    report = ReportRepository().save({"report_type": "DAILY_RESEARCH_BRIEF", "title": "Test"})
    assert report["report_id"]


def test_instrument_and_bars(memory_db):
    InstrumentRepository().create({"symbol": "NQ", "name": "Nasdaq Mini"})
    bars = MarketBarRepository()
    count = bars.save_bars([{
        "symbol": "NQ", "timeframe": "15m",
        "timestamp": datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc),
        "open": 18000, "high": 18010, "low": 17990, "close": 18005, "volume": 1000,
    }])
    assert count == 1
    assert len(bars.get_bars("NQ", "15m")) == 1