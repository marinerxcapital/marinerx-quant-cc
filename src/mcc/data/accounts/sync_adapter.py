"""Account sync adapter per 02_DATA_LAYER.md.

Consumes Tradeify normalized events (AccountStateEvent / TradeNewEvent / DrawdownUpdateEvent)
republishes on MCC bus. Degrades to last-known from sqlite if sync engine absent; flags staleness.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from mcc.core.bus import MessageBus
from mcc.core.events import AccountStateEvent, DrawdownUpdateEvent, TradeNewEvent
from mcc.storage.relational import init_db



class AccountSyncAdapter:
    """Bridge from Tradeify sync engine to MCC bus."""
    def __init__(self, bus: MessageBus, db_url: str = "sqlite:///:memory:") -> None:
        self.bus = bus
        self.engine = init_db(db_url)
        self.last_known: Optional[dict[str, Any]] = None
        self.stale = False

    async def handle_incoming(self, ev: Any) -> None:
        """Called by external sync or test injector. Republish normalized."""
        if isinstance(ev, (AccountStateEvent, DrawdownUpdateEvent, TradeNewEvent)):
            # republish as-is to MCC bus
            await self.bus.publish(ev)
            if isinstance(ev, DrawdownUpdateEvent):
                self.last_known = {"type": "drawdown", "payload": ev.payload, "ts": ev.ts_utc}
            elif isinstance(ev, AccountStateEvent):
                self.last_known = {"type": "state", "payload": ev.payload, "ts": ev.ts_utc}
            self.stale = False
            return

        # raw dict from tradeify fixture
        if isinstance(ev, dict):
            topic = ev.get("topic", "account_state")
            ts = ev.get("ts_utc", datetime.now(timezone.utc))
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            payload = ev.get("payload", ev)
            out_ev: Any
            if "drawdown" in str(topic).lower() or "drawdown" in payload:
                out_ev = DrawdownUpdateEvent(ts_utc=ts, source="tradeify", payload=payload)
            else:
                out_ev = AccountStateEvent(ts_utc=ts, source="tradeify", payload=payload)
            await self.bus.publish(out_ev)
            self.last_known = {"type": "raw", "payload": payload, "ts": ts}
            self.stale = False

    def get_last_known(self) -> dict[str, Any]:
        if self.last_known:
            return {**self.last_known, "stale": self.stale}
        # degrade to db
        try:
            # simple last from sqlite
            from sqlalchemy import text
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT equity, drawdown, ts_utc FROM account_states ORDER BY id DESC LIMIT 1")).fetchone()
                if res:
                    return {"type": "db", "equity": res[0], "drawdown": res[1], "ts": res[2], "stale": True}
        except Exception:
            pass
        self.stale = True
        return {"type": "none", "stale": True, "note": "no sync engine, no prior state"}

    async def republish_sample_drawdown(self, sample: dict[str, Any] | None = None) -> DrawdownUpdateEvent:
        if sample is None:
            sample = {"account_id": "demo", "drawdown_pct": 4.2, "limit": 6.0}
        ev = DrawdownUpdateEvent(
            ts_utc=datetime.now(timezone.utc),
            source="sync_adapter",
            payload=sample,
        )
        await self.bus.publish(ev)
        self.last_known = {"type": "drawdown", "payload": sample, "ts": ev.ts_utc}
        self.stale = False
        return ev

