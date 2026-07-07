"""SQLAlchemy 2.x table definitions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM tables."""


class AccountRow(Base):
    """Persisted account snapshot."""

    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(128), default="")
    program: Mapped[str] = mapped_column(String(64), default="")
    phase: Mapped[str] = mapped_column(String(16), default="EVAL")
    size_usd: Mapped[str | None] = mapped_column(String(32), nullable=True)
    platform: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(64), default="")
    balance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    equity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    high_water_mark: Mapped[str | None] = mapped_column(String(32), nullable=True)
    trailing_dd_amount: Mapped[str | None] = mapped_column(String(32), nullable=True)
    trailing_dd_floor: Mapped[str | None] = mapped_column(String(32), nullable=True)
    drawdown_headroom: Mapped[str | None] = mapped_column(String(32), nullable=True)
    daily_loss_limit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    daily_pnl: Mapped[str | None] = mapped_column(String(32), nullable=True)
    days_traded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consistency_metric: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payout_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    last_synced_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TradeRow(Base):
    """Persisted trade."""

    __tablename__ = "trades"
    __table_args__ = (UniqueConstraint("source_hash", name="uq_trades_source_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trade_id: Mapped[str] = mapped_column(String(64), default="")
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    symbol_raw: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(32), default="")
    side: Mapped[str] = mapped_column(String(8))
    qty: Mapped[int] = mapped_column(Integer)
    entry_time_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    entry_price: Mapped[str] = mapped_column(String(32))
    exit_time_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    exit_price: Mapped[str] = mapped_column(String(32))
    gross_pnl: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fees: Mapped[str | None] = mapped_column(String(32), nullable=True)
    net_pnl: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class FillRow(Base):
    """Persisted fill."""

    __tablename__ = "fills"
    __table_args__ = (UniqueConstraint("source_hash", name="uq_fills_source_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fill_id: Mapped[str] = mapped_column(String(64), default="")
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    symbol_raw: Mapped[str] = mapped_column(String(32))
    side: Mapped[str] = mapped_column(String(8))
    qty: Mapped[int] = mapped_column(Integer)
    price: Mapped[str] = mapped_column(String(32))
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    order_id: Mapped[str] = mapped_column(String(64), default="")
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class PositionRow(Base):
    """Persisted open position snapshot."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    symbol: Mapped[str] = mapped_column(String(32))
    side: Mapped[str] = mapped_column(String(8))
    qty: Mapped[int] = mapped_column(Integer)
    avg_price: Mapped[str] = mapped_column(String(32))
    unrealized_pnl: Mapped[str | None] = mapped_column(String(32), nullable=True)
    snapshot_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PayoutRow(Base):
    """Persisted payout record."""

    __tablename__ = "payouts"
    __table_args__ = (UniqueConstraint("source_hash", name="uq_payouts_source_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    request_date_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(64), default="")
    processed_date_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class DailyPnLRow(Base):
    """Persisted daily P&L snapshot."""

    __tablename__ = "daily_pnl"
    __table_args__ = (UniqueConstraint("source_hash", name="uq_daily_pnl_source_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    trade_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    starting_balance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ending_balance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    realized_pnl: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class SyncRunRow(Base):
    """Persisted sync run audit."""

    __tablename__ = "sync_runs"

    run_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    started_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accounts_synced: Mapped[int] = mapped_column(Integer, default=0)
    trades_new: Mapped[int] = mapped_column(Integer, default=0)
    fills_new: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="OK")