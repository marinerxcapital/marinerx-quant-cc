"""Clean events for bus spine."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

class Topic(str, Enum):
    BAR = "bar"
    TICK = "tick"
    INTERNALS = "internals"
    DECISION = "decision"
    FILL = "fill"
    AGENT_STATUS = "agent_status"
    LOG = "log"

@dataclass(frozen=True)
class Event:
    topic: Topic
    ts_utc: datetime
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ts_utc.tzinfo is None:
            object.__setattr__(self, 'ts_utc', self.ts_utc.replace(tzinfo=timezone.utc))

@dataclass(frozen=True)
class BarEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, symbol: str, **kw: Any):
        super().__init__(Topic.BAR, ts_utc, source, {"symbol": symbol, **kw})

@dataclass(frozen=True)
class DecisionEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, symbol: str, decision: str, reason: str, size: int = 0):
        super().__init__(Topic.DECISION, ts_utc, source, {"symbol": symbol, "decision": decision, "reason": reason, "size": size})

@dataclass(frozen=True)
class FillEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, symbol: str, side: str, qty: int, price: float, pnl: float = 0.0):
        super().__init__(Topic.FILL, ts_utc, source, {"symbol": symbol, "side": side, "qty": qty, "price": price, "pnl": pnl})

@dataclass(frozen=True)
class LogEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, level: str, message: str, **f: Any):
        super().__init__(Topic.LOG, ts_utc, source, {"level": level, "message": message, **f})

@dataclass(frozen=True)
class AgentStatusEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, agent: str, status: str, current_task: str | None = None):
        super().__init__(Topic.AGENT_STATUS, ts_utc, source, {"agent": agent, "status": status, "current_task": current_task})


# Additional events referenced by live feeds / account sync (minimal for type + protocol)
@dataclass(frozen=True)
class TickEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, symbol: str, price: float, **kw: Any):
        super().__init__(Topic.TICK, ts_utc, source, {"symbol": symbol, "price": price, **kw})

@dataclass(frozen=True)
class InternalsEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, name: str, value: float, **kw: Any):
        super().__init__(Topic.INTERNALS, ts_utc, source, {"name": name, "value": value, **kw})

@dataclass(frozen=True)
class AccountStateEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, account: str = "", equity: float = 0.0, **kw: Any):
        payload: dict[str, Any] = {"type": "account_state", "account": account, "equity": equity, **kw}
        p = kw.get("payload")
        if isinstance(p, dict):
            payload = p
        super().__init__(Topic.LOG, ts_utc, source, payload)

@dataclass(frozen=True)
class DrawdownUpdateEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, drawdown: float = 0.0, **kw: Any):
        payload: dict[str, Any] = {"type": "drawdown", "drawdown": drawdown, **kw}
        p = kw.get("payload")
        if isinstance(p, dict):
            payload = p
        super().__init__(Topic.LOG, ts_utc, source, payload)

@dataclass(frozen=True)
class TradeNewEvent(Event):
    def __init__(self, ts_utc: datetime, source: str, symbol: str = "", side: str = "", qty: int = 0, **kw: Any):
        payload: dict[str, Any] = {"type": "trade_new", "symbol": symbol, "side": side, "qty": qty, **kw}
        p = kw.get("payload")
        if isinstance(p, dict):
            payload = p
        super().__init__(Topic.LOG, ts_utc, source, payload)
