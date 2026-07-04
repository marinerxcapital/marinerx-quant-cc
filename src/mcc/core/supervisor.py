"""Supervisor with real snapshot for /health."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from .base_agent import BaseAgent
from .bus import MessageBus

@dataclass
class SystemStatus:
    ts_utc: datetime
    agents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    kill_active: bool = False


class Supervisor:
    def __init__(self, bus: Optional[MessageBus] = None) -> None:
        self.bus: MessageBus = bus or MessageBus()
        self.agents: Dict[str, BaseAgent] = {}
        self._tasks: Dict[str, asyncio.Task[Any]] = {}
        self._kill_active: bool = False

    def register(self, agent: BaseAgent) -> None:
        self.agents[agent.name] = agent

    async def start_all(self) -> None:
        for name, agent in self.agents.items():
            await agent.activate()
            self._tasks[name] = asyncio.create_task(agent.run())

    async def kill_switch(self) -> None:
        self._kill_active = True
        for agent in list(self.agents.values()):
            await agent.stop()

    def snapshot(self) -> SystemStatus:
        ag: Dict[str, Dict[str, Any]] = {}
        for n, a in self.agents.items():
            ag[n] = {"status": getattr(a, "status", "unknown"), "task": getattr(a, "current_task", None)}
        return SystemStatus(datetime.now(timezone.utc), ag, self._kill_active)
