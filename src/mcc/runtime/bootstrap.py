"""Bootstrap factory for the live supervisor.

This is the single construction path for run / tests / web.
Creates Supervisor, wires bus, registers agents (real spine + NoOp), starts replay if requested.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from mcc.agents import pipeline as agents_pipeline
from mcc.core.bus import MessageBus
from mcc.core.clock import RealClock, SimClock
from mcc.core.supervisor import Supervisor
from mcc.data.live.replay import ReplayAdapter


def create_supervisor(
    *,
    replay: bool = True,
    auto_replay_feed: bool = False,
    tradeify_db_path: str | None = None,
    journal_db_url: str | None = None,
) -> Supervisor:
    """Create and return a fully wired Supervisor.

    - Always registers the 15 roster agents (real spine for validation/decision/execution, NoOp for rest).
    - If replay=True, uses SimClock and optionally starts a replay feed publishing BAR events.
    """
    bus = MessageBus()
    clock = SimClock() if replay else RealClock()
    sup = Supervisor(bus=bus)

    agent_map: dict[str, Any] = {
        "Overseer": agents_pipeline.OverseerAgent,
        "DataOps": agents_pipeline.DataOpsAgent,
        "AccountSync": agents_pipeline.AccountSyncAgent,
        "MarketPulse": agents_pipeline.MarketPulseAgent,
        "IndicatorEngine": agents_pipeline.IndicatorEngineAgent,
        "RegimeMonitor": agents_pipeline.RegimeMonitorAgent,
        "StrategyRunner": agents_pipeline.StrategyRunnerAgent,
        "ValidationEngine": agents_pipeline.ValidationEngineAgent,
        "ResearchLab": agents_pipeline.ResearchLabAgent,
        "RiskCommand": agents_pipeline.RiskCommandAgent,
        "DecisionEngine": agents_pipeline.DecisionEngineAgent,
        "ExecutionGateway": agents_pipeline.ExecutionGatewayAgent,
        "TradeJournal": agents_pipeline.TradeJournalAgent,
        "PerformanceAnalyst": agents_pipeline.PerformanceAnalystAgent,
        "ReportPublisher": agents_pipeline.ReportPublisherAgent,
    }

    for name, cls in agent_map.items():
        kwargs: dict[str, Any] = {}
        if name == "AccountSync" and tradeify_db_path:
            kwargs["db_path"] = tradeify_db_path
        if name == "TradeJournal" and journal_db_url:
            from mcc.journal.journal import TradeJournal

            kwargs["journal"] = TradeJournal(db_url=journal_db_url)
        agent = cls(name=name, bus=bus, clock=clock, **kwargs)
        sup.register(agent)

    if replay and auto_replay_feed:
        sup._replay_task = _start_replay_feeder(bus, clock)  # type: ignore[attr-defined]

    return sup


def _start_replay_feeder(bus: MessageBus, clock: SimClock | RealClock) -> asyncio.Task[None]:
    """Background task: stream replay BAR events onto the bus."""

    async def _run() -> None:
        adapter = ReplayAdapter(bus=bus, clock=clock, speed=120.0)
        await adapter.connect()
        await adapter.subscribe(["NQ"], ["bars"])
        async for _ in adapter.stream():
            pass

    try:
        loop = asyncio.get_running_loop()
        return loop.create_task(_run())
    except RuntimeError:
        # No running loop at construction time; caller may start feed manually
        return asyncio.get_event_loop().create_task(_run())


async def start_replay_feed(sup: Supervisor, *, limit: int | None = None) -> int:
    """Explicitly start replay feed for tests/runtime; returns bars published."""
    bus = sup.bus
    clock = SimClock()
    for agent in sup.agents.values():
        if hasattr(agent, "clock"):
            agent.clock = clock
    adapter = ReplayAdapter(bus=bus, clock=clock, speed=120.0)
    await adapter.connect()
    await adapter.subscribe(["NQ"], ["bars"])
    return await adapter.stream_and_count(limit=limit)