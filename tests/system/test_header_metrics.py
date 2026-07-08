"""Header metrics must bind to Tradeify sync DB — never fabricated P&L."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mcc.system.header_metrics import build_header_metrics


def _seed_tradeify_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute(
        """
        CREATE TABLE accounts (
            account_id TEXT PRIMARY KEY,
            balance TEXT,
            equity TEXT,
            drawdown_headroom TEXT,
            daily_pnl TEXT,
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
        ("TDFYSL150133357496", "151242.40", "151242.40", "4500.00", "0", now, "EVAL", "active"),
    )
    conn.commit()
    conn.close()


def test_header_metrics_from_tradeify_db(tmp_path, monkeypatch):
    db_path = tmp_path / "tradeify_sync.db"
    _seed_tradeify_db(db_path)
    monkeypatch.setenv("TRADEIFY_SYNC_DB_PATH", str(db_path))

    metrics = build_header_metrics()
    assert metrics["source"] == "tradeify_sync_db"
    assert metrics["drawdown_headroom"] == 4500.0
    assert metrics["equity"] == 151242.4
    assert metrics["account_id"] == "TDFYSL150133357496"
    assert metrics["day_pnl"] == 0.0


def test_header_metrics_awaiting_sync_when_no_db(monkeypatch, tmp_path):
    missing = tmp_path / "missing.db"
    monkeypatch.setenv("TRADEIFY_SYNC_DB_PATH", str(missing))

    metrics = build_header_metrics()
    assert metrics["source"] == "awaiting_sync"
    assert metrics["drawdown_headroom"] is None