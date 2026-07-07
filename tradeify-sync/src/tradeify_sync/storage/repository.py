"""Repository layer with idempotent inserts."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TypeVar

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from tradeify_sync.models import (
    Account,
    DailyPnLSnapshot,
    Fill,
    PayoutRecord,
    Position,
    SyncRun,
    SyncStatus,
    Trade,
)
from tradeify_sync.storage.schema import (
    AccountRow,
    DailyPnLRow,
    FillRow,
    PayoutRow,
    PositionRow,
    SyncRunRow,
    TradeRow,
)

T = TypeVar("T", Trade, Fill, PayoutRecord, DailyPnLSnapshot)


def _dec(val: Decimal | None) -> str | None:
    return str(val) if val is not None else None


def upsert_account(session: Session, account: Account) -> None:
    """Merge account on account_id, refreshing last_synced_utc."""
    row = session.get(AccountRow, account.account_id)
    data = {
        "nickname": account.nickname,
        "program": account.program,
        "phase": account.phase.value,
        "size_usd": _dec(account.size_usd),
        "platform": account.platform,
        "status": account.status,
        "balance": _dec(account.balance),
        "equity": _dec(account.equity),
        "high_water_mark": _dec(account.high_water_mark),
        "trailing_dd_amount": _dec(account.trailing_dd_amount),
        "trailing_dd_floor": _dec(account.trailing_dd_floor),
        "drawdown_headroom": _dec(account.drawdown_headroom),
        "daily_loss_limit": _dec(account.daily_loss_limit),
        "daily_pnl": _dec(account.daily_pnl),
        "days_traded": account.days_traded,
        "consistency_metric": _dec(account.consistency_metric),
        "payout_eligible": account.payout_eligible,
        "last_synced_utc": account.last_synced_utc,
    }
    if row is None:
        session.add(AccountRow(account_id=account.account_id, **data))
    else:
        for key, val in data.items():
            setattr(row, key, val)


def _trade_row(trade: Trade) -> dict[str, object]:
    return {
        "trade_id": trade.trade_id,
        "account_id": trade.account_id,
        "symbol_raw": trade.symbol_raw,
        "symbol": trade.symbol,
        "side": trade.side.value,
        "qty": trade.qty,
        "entry_time_utc": trade.entry_time_utc,
        "entry_price": str(trade.entry_price),
        "exit_time_utc": trade.exit_time_utc,
        "exit_price": str(trade.exit_price),
        "gross_pnl": _dec(trade.gross_pnl),
        "fees": _dec(trade.fees),
        "net_pnl": _dec(trade.net_pnl),
        "duration_sec": trade.duration_sec,
        "source_hash": trade.source_hash,
    }


def _fill_row(fill: Fill) -> dict[str, object]:
    return {
        "fill_id": fill.fill_id,
        "account_id": fill.account_id,
        "symbol_raw": fill.symbol_raw,
        "side": fill.side.value,
        "qty": fill.qty,
        "price": str(fill.price),
        "timestamp_utc": fill.timestamp_utc,
        "order_id": fill.order_id,
        "source_hash": fill.source_hash,
    }


def _payout_row(payout: PayoutRecord) -> dict[str, object]:
    return {
        "account_id": payout.account_id,
        "request_date_utc": payout.request_date_utc,
        "amount": str(payout.amount),
        "status": payout.status,
        "processed_date_utc": payout.processed_date_utc,
        "source_hash": payout.source_hash,
    }


def _daily_pnl_row(snap: DailyPnLSnapshot) -> dict[str, object]:
    return {
        "account_id": snap.account_id,
        "trade_date": snap.trade_date,
        "starting_balance": _dec(snap.starting_balance),
        "ending_balance": _dec(snap.ending_balance),
        "realized_pnl": _dec(snap.realized_pnl),
        "source_hash": snap.source_hash,
    }


def insert_ignore_trades(session: Session, trades: list[Trade]) -> int:
    """Insert trades, ignoring duplicates by source_hash."""
    return _insert_ignore(session, TradeRow, trades, _trade_row)


def insert_ignore_fills(session: Session, fills: list[Fill]) -> int:
    """Insert fills, ignoring duplicates by source_hash."""
    return _insert_ignore(session, FillRow, fills, _fill_row)


def insert_ignore_payouts(session: Session, payouts: list[PayoutRecord]) -> int:
    """Insert payouts, ignoring duplicates by source_hash."""
    return _insert_ignore(session, PayoutRow, payouts, _payout_row)


def insert_ignore_daily_pnl(session: Session, snaps: list[DailyPnLSnapshot]) -> int:
    """Insert daily P&L snapshots, ignoring duplicates."""
    return _insert_ignore(session, DailyPnLRow, snaps, _daily_pnl_row)


def _insert_ignore(
    session: Session,
    table: type[TradeRow | FillRow | PayoutRow | DailyPnLRow],
    models: list[T],
    row_fn: object,
) -> int:
    if not models:
        return 0
    inserted = 0
    for model in models:
        data = row_fn(model)  # type: ignore[operator]
        source_hash = str(data["source_hash"])
        exists = session.execute(
            select(table).where(table.source_hash == source_hash)  # type: ignore[attr-defined]
        ).first()
        if exists:
            continue
        stmt = sqlite_insert(table).values(**data)
        stmt = stmt.on_conflict_do_nothing(index_elements=["source_hash"])
        session.execute(stmt)
        inserted += 1
    return inserted


def replace_positions(session: Session, account_id: str, positions: list[Position]) -> None:
    """Replace open positions snapshot for an account."""
    session.execute(delete(PositionRow).where(PositionRow.account_id == account_id))
    for pos in positions:
        session.add(
            PositionRow(
                account_id=pos.account_id,
                symbol=pos.symbol,
                side=pos.side.value,
                qty=pos.qty,
                avg_price=str(pos.avg_price),
                unrealized_pnl=_dec(pos.unrealized_pnl),
                snapshot_utc=pos.snapshot_utc,
            )
        )


def last_trade_exit_utc(session: Session, account_id: str) -> datetime | None:
    """Return the latest exit time for incremental sync."""
    stmt = (
        select(TradeRow.exit_time_utc)
        .where(TradeRow.account_id == account_id)
        .order_by(TradeRow.exit_time_utc.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def account_headroom(session: Session, account_id: str) -> Decimal | None:
    """Return drawdown headroom for an account."""
    row = session.get(AccountRow, account_id)
    if row is None or row.drawdown_headroom is None:
        return None
    return Decimal(row.drawdown_headroom)


def open_sync_run(session: Session, run_id: str) -> SyncRun:
    """Create a new sync run audit row."""
    started = datetime.now(UTC)
    session.add(
        SyncRunRow(
            run_id=run_id,
            started_utc=started,
            status=SyncStatus.OK.value,
        )
    )
    return SyncRun(run_id=run_id, started_utc=started)


def close_sync_run(session: Session, run: SyncRun) -> None:
    """Finalize a sync run."""
    row = session.get(SyncRunRow, run.run_id)
    if row is None:
        return
    row.finished_utc = run.finished_utc or datetime.now(UTC)
    row.accounts_synced = run.accounts_synced
    row.trades_new = run.trades_new
    row.fills_new = run.fills_new
    row.errors = "; ".join(run.errors)
    row.status = run.status.value


def get_last_sync_run(session: Session) -> SyncRun | None:
    """Return the most recent sync run."""
    stmt = select(SyncRunRow).order_by(SyncRunRow.started_utc.desc()).limit(1)
    row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        return None
    return SyncRun(
        run_id=row.run_id,
        started_utc=row.started_utc,
        finished_utc=row.finished_utc,
        accounts_synced=row.accounts_synced,
        trades_new=row.trades_new,
        fills_new=row.fills_new,
        errors=[e for e in row.errors.split("; ") if e],
        status=SyncStatus(row.status),
    )


def count_rows(session: Session, table_name: str) -> int:
    """Count rows in a named table."""
    mapping = {
        "accounts": AccountRow,
        "trades": TradeRow,
        "fills": FillRow,
        "positions": PositionRow,
        "payouts": PayoutRow,
    }
    model = mapping.get(table_name)
    if model is None:
        return 0
    return len(session.execute(select(model)).scalars().all())


def list_accounts(session: Session) -> list[AccountRow]:
    """Return all account rows."""
    return list(session.execute(select(AccountRow)).scalars().all())