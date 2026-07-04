"""BaseAgent (minimal for 15-agent roster and status reporting)."""
from __future__ import annotations
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
from .bus import MessageBus
from .clock import RealClock, Clock
from .events import Event, Topic


class BaseAgent(ABC):
    def __init__(self, name: str, bus: MessageBus, clock: Optional[Clock] = None) -> None:
        self.name = name
        self.bus = bus
        self.clock: Clock = clock or RealClock()
        self.status: str = "idle"
        self.current_task: Optional[str] = None
        self.heartbeat_ts: datetime = self.clock.now()
        self.log_buffer: list[str] = []

    def set_status(self, s: str, task: Optional[str] = None) -> None:
        self.status = s
        if task is not None:
            self.current_task = task
        self.heartbeat_ts = self.clock.now()
        # status events emitted in async activate/run to keep construct sync-safe

    def log_line(self, msg: str) -> None:
        self.log_buffer.append(msg)
        if len(self.log_buffer) > 100:
            self.log_buffer.pop(0)
        # log events emitted async in activate/run

    async def emit(self, ev: Any) -> None:
        await self.bus.publish(ev)

    async def activate(self) -> None:
        """Async activation: start listeners, emit initial status. Called from supervisor.start_all."""
        # default no-op; overridden in agents that need bus subs
        await self.emit(Event(
            topic=Topic.AGENT_STATUS,
            ts_utc=self.heartbeat_ts,
            source=self.name,
            payload={"agent": self.name, "status": self.status, "task": self.current_task},
        ))

    @abstractmethod
    async def work(self) -> None: ...

    async def run(self) -> None:
        self.status = "working"
        try:
            while self.status == "working":
                await self.work()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            self.status = "stopped"
            raise

    async def start(self) -> None:
        asyncio.create_task(self.run())

    async def stop(self) -> None:
        self.status = "stopped"
