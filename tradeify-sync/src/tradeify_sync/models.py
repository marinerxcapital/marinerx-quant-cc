"""Pydantic v2 domain models with deterministic source hashes."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from tradeify_sync.utils.timeparse import canonical_iso


class Phase(str, Enum):
    EVAL = "EVAL"
    FUNDED = "FUNDED"
    PA = "PA"


class Side(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class SyncStatus(str, Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Account(BaseModel):
    """Tradeify account snapshot."""

    account_id: str
    nickname: str = ""
    program: str = ""
    phase: Phase = Phase.EVAL
    size_usd: Decimal | None = None
    platform: str = ""
    status: str = ""
    balance: Decimal | None = None
    equity: Decimal | None = None
    high_water_mark: Decimal | None = None
    trailing_dd_amount: Decimal | None = None
    trailing_dd_floor: Decimal | None = None
    drawdown_headroom: Decimal | None = None
    daily_loss_limit: Decimal | None = None
    daily_pnl: Decimal | None = None
    days_traded: int | None = None
    consistency_metric: Decimal | None = None
    payout_eligible: bool = False
    last_synced_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def compute_headroom(self) -> Account:
        if self.equity is not None and self.trailing_dd_floor is not None:
            self.drawdown_headroom = self.equity - self.trailing_dd_floor
        return self


class Trade(BaseModel):
    """Closed trade record."""

    trade_id: str = ""
    account_id: str
    symbol_raw: str
    symbol: str = ""
    side: Side
    qty: int
    entry_time_utc: datetime
    entry_price: Decimal
    exit_time_utc: datetime
    exit_price: Decimal
    gross_pnl: Decimal | None = None
    fees: Decimal | None = None
    net_pnl: Decimal | None = None
    duration_sec: int | None = None
    source_hash: str = ""

    def build_hash(self) -> str:
        entry_iso = canonical_iso(self.entry_time_utc)
        exit_iso = canonical_iso(self.exit_time_utc)
        raw = (
            f"{self.account_id}|{self.symbol_raw}|{self.side.value}|{self.qty}|"
            f"{entry_iso}|{self.entry_price}|{exit_iso}|{self.exit_price}"
        )
        return _sha256(raw)

    @model_validator(mode="after")
    def finalize(self) -> Trade:
        if self.duration_sec is None:
            delta = self.exit_time_utc - self.entry_time_utc
            self.duration_sec = int(delta.total_seconds())
        if self.net_pnl is None and self.gross_pnl is not None:
            fees = self.fees or Decimal("0")
            self.net_pnl = self.gross_pnl - fees
        if not self.source_hash:
            self.source_hash = self.build_hash()
        return self


class Fill(BaseModel):
    """Individual fill/execution record."""

    fill_id: str = ""
    account_id: str
    symbol_raw: str
    side: OrderSide
    qty: int
    price: Decimal
    timestamp_utc: datetime
    order_id: str = ""
    source_hash: str = ""

    def build_hash(self) -> str:
        ts_iso = canonical_iso(self.timestamp_utc)
        raw = (
            f"{self.account_id}|{self.symbol_raw}|{self.side.value}|{self.qty}|"
            f"{self.price}|{ts_iso}|{self.order_id}"
        )
        return _sha256(raw)

    @model_validator(mode="after")
    def finalize(self) -> Fill:
        if not self.source_hash:
            self.source_hash = self.build_hash()
        return self


class Position(BaseModel):
    """Open position snapshot."""

    account_id: str
    symbol: str
    side: Side
    qty: int
    avg_price: Decimal
    unrealized_pnl: Decimal | None = None
    snapshot_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PayoutRecord(BaseModel):
    """Payout request/history record."""

    account_id: str
    request_date_utc: datetime
    amount: Decimal
    status: str = ""
    processed_date_utc: datetime | None = None
    source_hash: str = ""

    def build_hash(self) -> str:
        req_iso = canonical_iso(self.request_date_utc)
        raw = f"{self.account_id}|{req_iso}|{self.amount}"
        return _sha256(raw)

    @model_validator(mode="after")
    def finalize(self) -> PayoutRecord:
        if not self.source_hash:
            self.source_hash = self.build_hash()
        return self


class DailyPnLSnapshot(BaseModel):
    """Daily P&L summary."""

    account_id: str
    trade_date: datetime
    starting_balance: Decimal | None = None
    ending_balance: Decimal | None = None
    realized_pnl: Decimal | None = None
    source_hash: str = ""

    def build_hash(self) -> str:
        date_iso = canonical_iso(self.trade_date)
        raw = f"{self.account_id}|{date_iso}"
        return _sha256(raw)

    @model_validator(mode="after")
    def finalize(self) -> DailyPnLSnapshot:
        if not self.source_hash:
            self.source_hash = self.build_hash()
        return self


class SyncRun(BaseModel):
    """Audit record for a sync execution."""

    run_id: str
    started_utc: datetime
    finished_utc: datetime | None = None
    accounts_synced: int = 0
    trades_new: int = 0
    fills_new: int = 0
    errors: list[str] = Field(default_factory=list)
    status: SyncStatus = SyncStatus.OK