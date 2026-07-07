"""Trade journal — ingest FILL events and persist to relational Trade model."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from mcc.core.events import FillEvent
from mcc.storage.models import Trade
from mcc.storage.relational import init_db


class TradeJournal:
    """Persist fills from bus into the trades table."""

    def __init__(self, db_url: str = "sqlite:///:memory:") -> None:
        self.engine = init_db(db_url)

    def _fill_id(self, ts: datetime, symbol: str, side: str, qty: int, price: float) -> str:
        raw = f"{ts.isoformat()}|{symbol}|{side}|{qty}|{price}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def record_fill(self, ev: FillEvent | dict[str, Any]) -> str:
        """Ingest a fill event; returns trade id."""
        if isinstance(ev, FillEvent):
            payload = ev.payload
            ts = ev.ts_utc
            source = ev.source
        else:
            payload = ev.get("payload", ev)
            ts = ev.get("ts_utc", datetime.now(timezone.utc))
            source = ev.get("source", "unknown")

        symbol = str(payload.get("symbol", "UNKNOWN"))
        side = str(payload.get("side", "BUY"))
        qty = int(payload.get("qty", 0))
        price = float(payload.get("price", 0.0))
        pnl = float(payload.get("pnl", 0.0))

        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        trade_id = self._fill_id(ts, symbol, side, qty, price)

        with Session(self.engine) as session:
            existing = session.get(Trade, trade_id)
            if existing is not None:
                return trade_id

            row = Trade(
                id=trade_id,
                ts_utc=ts,
                symbol=symbol,
                side=side,
                qty=qty,
                price=price,
                pnl=pnl,
            )
            session.add(row)
            session.commit()

        return trade_id

    def count_trades(self) -> int:
        with Session(self.engine) as session:
            return len(session.scalars(select(Trade)).all())

    def get_trades(self, limit: int = 100) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            rows = session.scalars(select(Trade).order_by(Trade.ts_utc.desc()).limit(limit)).all()
            return [
                {
                    "id": r.id,
                    "ts_utc": r.ts_utc.isoformat() if r.ts_utc else None,
                    "symbol": r.symbol,
                    "side": r.side,
                    "qty": r.qty,
                    "price": r.price,
                    "pnl": r.pnl,
                }
                for r in rows
            ]