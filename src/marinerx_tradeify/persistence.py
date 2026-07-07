from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, select
from sqlalchemy.orm import Session

from mcc.storage.database import get_engine
from mcc.storage.models import Base


class TradeifyAccountSnapshot(Base):
    __tablename__ = "tradeify_account_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    account_id_hash = Column(String(32), default="")
    phase = Column(String(32), default="EVALUATION")
    balance = Column(Float, default=0.0)
    realized_day_pnl = Column(Float, default=0.0)
    drawdown_headroom = Column(Float, default=0.0)
    reconciliation_status = Column(String(32), default="unknown")
    block_trades = Column(Integer, default=1)
    snapshot_json = Column(Text, default="{}")


class TradeifySyncEvent(Base):
    __tablename__ = "tradeify_sync_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    source = Column(String(64), default="sync")
    status = Column(String(32), default="ok")
    message = Column(Text, default="")
    details_json = Column(Text, default="{}")


class TradovateFill(Base):
    __tablename__ = "tradovate_fills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    account_id_hash = Column(String(32), default="")
    symbol = Column(String(32), default="")
    side = Column(String(16), default="")
    qty = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    fill_json = Column(Text, default="{}")


class TradovatePosition(Base):
    __tablename__ = "tradovate_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    account_id_hash = Column(String(32), default="")
    symbol = Column(String(32), default="")
    net_qty = Column(Integer, default=0)
    unrealized_pnl = Column(Float, default=0.0)
    position_json = Column(Text, default="{}")


def ensure_tables() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)


def save_snapshot(payload: dict[str, Any]) -> int:
    ensure_tables()
    snap = payload.get("snapshot") or {}
    rec = payload.get("reconciliation") or {}
    row = TradeifyAccountSnapshot(
        account_id_hash=str(payload.get("account_id_hash", "")),
        phase=str(snap.get("phase", "EVALUATION")),
        balance=float(snap.get("balance", 0.0)),
        realized_day_pnl=float(snap.get("realized_day_pnl", 0.0)),
        drawdown_headroom=float(snap.get("drawdown_headroom", 0.0)),
        reconciliation_status=str(rec.get("status", "unknown")),
        block_trades=1 if rec.get("block_trades") else 0,
        snapshot_json=json.dumps(_redact_payload(payload)),
    )
    with Session(get_engine()) as session:
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)


def save_sync_event(source: str, status: str, message: str, details: dict[str, Any] | None = None) -> None:
    ensure_tables()
    row = TradeifySyncEvent(
        source=source,
        status=status,
        message=message[:2000],
        details_json=json.dumps(details or {}),
    )
    with Session(get_engine()) as session:
        session.add(row)
        session.commit()


def load_latest_snapshot() -> dict[str, Any] | None:
    ensure_tables()
    with Session(get_engine()) as session:
        row = session.scalars(
            select(TradeifyAccountSnapshot).order_by(TradeifyAccountSnapshot.id.desc()).limit(1)
        ).first()
        if not row:
            return None
        try:
            payload = json.loads(row.snapshot_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        payload.setdefault("observed_at", row.ts_utc.isoformat() if row.ts_utc else None)
        payload.setdefault("status", "cached")
        return payload


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip any credential-like keys before persistence."""
    banned = {"password", "secret", "token", "accessToken", "access_token", "cookies"}
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if k.lower() in banned or any(b in k.lower() for b in banned):
            continue
        if isinstance(v, dict):
            out[k] = _redact_payload(v)
        else:
            out[k] = v
    return out