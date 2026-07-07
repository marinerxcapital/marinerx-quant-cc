"""Test deterministic source hashes."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from tradeify_sync.models import (
    DailyPnLSnapshot,
    Fill,
    OrderSide,
    PayoutRecord,
    Side,
    Trade,
)


def test_trade_hash_stable() -> None:
    trade = Trade(
        account_id="ACC-001",
        symbol_raw="NQU25",
        side=Side.LONG,
        qty=2,
        entry_time_utc=datetime(2025, 7, 1, 13, 35, tzinfo=UTC),
        entry_price=Decimal("21500.50"),
        exit_time_utc=datetime(2025, 7, 1, 14, 15, tzinfo=UTC),
        exit_price=Decimal("21525.75"),
    )
    h1 = trade.build_hash()
    h2 = trade.build_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_trade_hash_differs_on_input() -> None:
    base = dict(
        account_id="ACC-001",
        symbol_raw="NQU25",
        side=Side.LONG,
        qty=2,
        entry_time_utc=datetime(2025, 7, 1, 13, 35, tzinfo=UTC),
        entry_price=Decimal("21500.50"),
        exit_time_utc=datetime(2025, 7, 1, 14, 15, tzinfo=UTC),
        exit_price=Decimal("21525.75"),
    )
    t1 = Trade(**base)
    t2 = Trade(**{**base, "qty": 3})
    assert t1.build_hash() != t2.build_hash()


def test_fill_hash_stable() -> None:
    fill = Fill(
        account_id="ACC-001",
        symbol_raw="ESZ25",
        side=OrderSide.BUY,
        qty=1,
        price=Decimal("5800.25"),
        timestamp_utc=datetime(2025, 7, 2, 18, 20, tzinfo=UTC),
        order_id="ORD-99",
    )
    h = fill.build_hash()
    assert len(h) == 64


def test_payout_hash_stable() -> None:
    payout = PayoutRecord(
        account_id="ACC-002",
        request_date_utc=datetime(2025, 6, 1, 12, 0, tzinfo=UTC),
        amount=Decimal("1500.00"),
    )
    assert len(payout.build_hash()) == 64


def test_daily_pnl_hash_stable() -> None:
    snap = DailyPnLSnapshot(
        account_id="ACC-001",
        trade_date=datetime(2025, 7, 1, 4, 0, tzinfo=UTC),
    )
    assert len(snap.build_hash()) == 64