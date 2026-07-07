"""Simulate production legacy schemas and verify Tier 1 migration."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, text

from mcc.core.config import reset_settings_cache
from mcc.storage.database import get_engine, reset_engine
from mcc.storage.repositories import (
    InstrumentRepository,
    JournalRepository,
    OrderRepository,
    RiskRepository,
    StrategyRepository,
)


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    db = Path(tmpdir) / "old.sqlite"
    eng = create_engine(f"sqlite:///{db}")
    with eng.begin() as conn:
        conn.execute(
            text("CREATE TABLE strategies (id TEXT PRIMARY KEY, status TEXT DEFAULT 'DRAFT')")
        )
        conn.execute(text("CREATE TABLE risk_settings (id INTEGER PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE journal_entries (id INTEGER PRIMARY KEY, entry_id TEXT)"))
        conn.execute(text("CREATE TABLE instruments (id INTEGER PRIMARY KEY, symbol TEXT)"))
        conn.execute(text("CREATE TABLE orders (id INTEGER PRIMARY KEY, order_id TEXT)"))
    reset_engine()
    reset_settings_cache()
    get_engine(f"sqlite:///{db}")
    print("strategies", StrategyRepository().list_strategies())
    print("risk", RiskRepository().get_settings())
    print("journal", JournalRepository().list_entries())
    print("instruments", InstrumentRepository().list_active())
    print("orders", OrderRepository().list_orders())
    print("OK")


if __name__ == "__main__":
    main()