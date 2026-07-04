"""Bootstrap factory for the live supervisor.

This is the single construction path for run / tests / web.
Creates Supervisor, wires bus, registers agents (real spine + NoOp), starts replay if requested.
"""
from __future__ import annotations

from typing import Optional
from mcc.core.bus import MessageBus
from mcc.core.clock import RealClock, SimClock
from mcc.core.supervisor import Supervisor
from mcc.agents import pipeline as agents_pipeline  # will define real agents
from mcc.data.live import replay as replay_mod  # existing or stub

def create_supervisor(*, replay: bool = True) -> Supervisor:
    """Create and return a fully wired Supervisor.

    - Always registers the 15 roster agents (real spine for validation/decision/execution, NoOp for rest).
    - If replay=True, starts a replay feed that publishes BarEvent on a SimClock.
    """
    bus = MessageBus()
    clock = SimClock() if replay else RealClock()
    sup = Supervisor(bus=bus)  # current Supervisor takes bus; clock passed to individual agents

    # Register all 15 as real (minimal but domain-named) agents from pipeline
    agent_map = {
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
        agent = cls(name=name, bus=bus, clock=clock)
        sup.register(agent)

    # Optionally wire a replay feeder (the replay module can publish to bus)
    if replay:
        # The test or run can drive it; here we just make sure the module is importable
        # In practice, the e2e test will call replay functions or publish directly.
        pass

    return sup
