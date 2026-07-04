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

    def __post_init__(self):
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
