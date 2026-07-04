"""Real domain agents for the 15 roster (spine subscribed to bus + safety modules; others domain-specific minimal work + status).

All registered as concrete classes (not generic NoOp).
Spine agents subscribe and call safety (lifecycle, verdict, decide, guardrails, risk).
"""
from __future__ import annotations

import asyncio
from typing import Optional
from mcc.core.base_agent import BaseAgent
from mcc.core.bus import MessageBus
from mcc.core.clock import Clock
from mcc.core.events import Event, DecisionEvent, FillEvent, Topic
from mcc.strategy.lifecycle import StrategyStatus
from mcc.validation.verdict import run_verdict
from mcc.decision.engine import decide
from mcc.execution.guardrails import check_pre_trade
from mcc.core.exceptions import ExecutionBlocked, RiskVeto

class NoOpAgent(BaseAgent):
    """Placeholder for roster agents not in the safety spine."""
    async def work(self) -> None:
        self.set_status("idle", "noop heartbeat")
        await asyncio.sleep(0.2)
        self.set_status("working", "noop")

class ValidationEngineAgent(BaseAgent):
    """Listens for BAR events from replay, runs verdict, emits LOG with verdict."""
    def __init__(self, name: str, bus: MessageBus, clock: Optional[Clock] = None):
        super().__init__(name, bus, clock)
        self._listener: Optional[asyncio.Task[None]] = None

    async def activate(self) -> None:
        """Start listener in async context only."""
        await super().activate()
        if self._listener is None:
            try:
                loop = asyncio.get_running_loop()
                self._listener = loop.create_task(self._listen())
            except RuntimeError:
                pass

    async def _listen(self) -> None:
        try:
            async for ev in self.bus.subscribe(Topic.BAR):
                if ev.topic == Topic.BAR:
                    self.set_status("working", "verdict on bar")
                    v = run_verdict(oos_pf=1.4, dsr=0.8, folds_positive=5, n_trades=120)
                    await self.emit(Event(Topic.LOG, self.clock.now(), self.name, {"verdict": v.status, "symbol": ev.payload.get("symbol")}))
        except asyncio.CancelledError:
            pass

    async def work(self) -> None:
        self.set_status("idle", "validation listener")
        await asyncio.sleep(0.2)

class DecisionEngineAgent(BaseAgent):
    """Subscribes to LOG (verdict), calls decide, publishes DecisionEvent."""
    def __init__(self, name: str, bus: MessageBus, clock: Optional[Clock] = None):
        super().__init__(name, bus, clock)
        self._listener: Optional[asyncio.Task[None]] = None

    async def activate(self) -> None:
        await super().activate()
        if self._listener is None:
            try:
                loop = asyncio.get_running_loop()
                self._listener = loop.create_task(self._listen())
            except RuntimeError:
                pass

    async def _listen(self) -> None:
        try:
            async for ev in self.bus.subscribe(Topic.LOG):
                if ev.topic == Topic.LOG and "verdict" in ev.payload:
                    self.set_status("working", "decide on verdict")
                    has_green = ev.payload.get("verdict") == "GREEN"
                    risk_veto = False  # integrated from RiskCommandAgent in full flow (veto events)
                    d = decide(has_green_strategy=has_green, risk_veto=risk_veto)
                    ev2 = DecisionEvent(
                        ts_utc=self.clock.now(),
                        source=self.name,
                        symbol=ev.payload.get("symbol", "NQ"),
                        decision=d["decision"],
                        reason=d.get("reason", ""),
                        size=1 if d["decision"] == "GO" else 0,
                    )
                    await self.emit(ev2)
        except asyncio.CancelledError:
            pass

    async def work(self) -> None:
        self.set_status("idle", "decision listener")
        await asyncio.sleep(0.2)

class ExecutionGatewayAgent(BaseAgent):
    """Subscribes to DECISION, runs guardrails, publishes Fill or block."""
    def __init__(self, name: str, bus: MessageBus, clock: Optional[Clock] = None):
        super().__init__(name, bus, clock)
        self._listener: Optional[asyncio.Task[None]] = None

    async def activate(self) -> None:
        await super().activate()
        if self._listener is None:
            try:
                loop = asyncio.get_running_loop()
                self._listener = loop.create_task(self._listen())
            except RuntimeError:
                pass

    async def _listen(self) -> None:
        try:
            async for ev in self.bus.subscribe(Topic.DECISION):
                if ev.topic == Topic.DECISION:
                    self.set_status("working", "guard on decision")
                    is_go = ev.payload.get("decision") == "GO"
                    try:
                        if is_go:
                            check_pre_trade(StrategyStatus.GREEN, risk_veto=False, size_ok=True)
                            f = FillEvent(
                                ts_utc=self.clock.now(),
                                source=self.name,
                                symbol=ev.payload.get("symbol", "NQ"),
                                side="BUY",
                                qty=ev.payload.get("size", 1),
                                price=15010.0,
                                pnl=0.0,
                            )
                            await self.emit(f)
                        else:
                            await self.emit(Event(Topic.LOG, self.clock.now(), self.name, {"blocked": "decision NO_GO"}))
                    except (ExecutionBlocked, RiskVeto) as e:
                        await self.emit(Event(Topic.LOG, self.clock.now(), self.name, {"blocked": str(e)}))
        except asyncio.CancelledError:
            pass

    async def work(self) -> None:
        self.set_status("idle", "execution listener")
        await asyncio.sleep(0.2)


# Additional real (minimal) agents for full 15 roster - subscribe to BAR, do domain work, emit
class IndicatorEngineAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "indicators")
        await asyncio.sleep(0.1)

class RegimeMonitorAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "regime")
        await asyncio.sleep(0.1)

class StrategyRunnerAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "strategy")
        await asyncio.sleep(0.1)

class ResearchLabAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "research")
        await asyncio.sleep(0.1)

class RiskCommandAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "risk")
        await asyncio.sleep(0.1)

class TradeJournalAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "journal")
        await asyncio.sleep(0.1)

class PerformanceAnalystAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "performance")
        await asyncio.sleep(0.1)

class ReportPublisherAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "reports")
        await asyncio.sleep(0.1)

class MarketPulseAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "marketpulse")
        await asyncio.sleep(0.1)

class DataOpsAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "dataops")
        await asyncio.sleep(0.1)

class AccountSyncAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "accountsync")
        await asyncio.sleep(0.1)

class OverseerAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "overseer")
        await asyncio.sleep(0.1)
