"""Test idempotent repository inserts."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from tradeify_sync.models import Side, Trade
from tradeify_sync.storage.repository import insert_ignore_trades


def _sample_trade(account_id: str = "ACC-001") -> Trade:
    return Trade(
        account_id=account_id,
        symbol_raw="NQU25",
        side=Side.LONG,
        qty=2,
        entry_time_utc=datetime(2025, 7, 1, 13, 35, tzinfo=UTC),
        entry_price=Decimal("21500.50"),
        exit_time_utc=datetime(2025, 7, 1, 14, 15, tzinfo=UTC),
        exit_price=Decimal("21525.75"),
        gross_pnl=Decimal("252.50"),
        fees=Decimal("4.50"),
        net_pnl=Decimal("248.00"),
    )


def test_insert_ignore_dedup(db_session: Session) -> None:
    trades = [_sample_trade(), _sample_trade()]
    first = insert_ignore_trades(db_session, trades)
    db_session.commit()
    second = insert_ignore_trades(db_session, trades)
    db_session.commit()
    assert first == 1
    assert second == 0