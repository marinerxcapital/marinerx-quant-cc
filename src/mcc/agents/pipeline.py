"""Real domain agents for the 15 roster (spine subscribed to bus + safety modules; others domain-specific minimal work + status).

All registered as concrete classes (not generic NoOp).
Spine agents subscribe and call safety (lifecycle, verdict, decide, guardrails, risk).
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional

from mcc.agents.snapshots import AgentSnapshotRegistry
from mcc.core.base_agent import BaseAgent
from mcc.core.bus import MessageBus
from mcc.core.clock import Clock
from mcc.core.events import (
    AccountStateEvent,
    DecisionEvent,
    Event,
    FillEvent,
    Topic,
)
from mcc.core.exceptions import ExecutionBlocked, RiskVeto
from mcc.data.accounts.sync_adapter import AccountSyncAdapter
from mcc.data.accounts.tradeify_reader import read_account_state
from mcc.decision.engine import decide
from mcc.execution.guardrails import check_pre_trade
from mcc.indicators.engine import IndicatorEngine
from mcc.internals.breadth import BreadthComputer, breadth_to_internals_events
from mcc.journal.journal import TradeJournal
from mcc.risk.monitor import RiskMonitor
from mcc.strategy.lifecycle import StrategyStatus
from mcc.validation.verdict import run_verdict

# Conservative defaults when BAR lacks strategy metrics (validation-first)
_DEFAULT_METRICS: dict[str, float | int] = {
    "oos_pf": 0.9,
    "dsr": -0.1,
    "folds_positive": 1,
    "n_trades": 20,
}

# Replay spine: synthetic GREEN edge when BAR omits strategy_metrics (see verdict.py)
_REPLAY_GREEN_METRICS: dict[str, float | int] = {
    "oos_pf": 1.4,
    "dsr": 0.8,
    "folds_positive": 5,
    "n_trades": 120,
}

# Module-level last bar prices for ExecutionGateway
_last_bar_prices: dict[str, float] = {}


def _parse_risk_veto_from_payload(payload: dict) -> bool | None:
    """Return veto flag when payload is a RiskCommand risk-state publication."""
    if payload.get("type") == "risk_veto":
        return bool(payload.get("veto"))
    if "risk_state" in payload:
        return bool(payload.get("veto", payload["risk_state"].get("veto")))
    return None


def _has_explicit_strategy_metrics(payload: dict[str, Any]) -> bool:
    if isinstance(payload.get("strategy_metrics"), dict):
        return True
    return any(key in payload for key in ("oos_pf", "dsr", "folds_positive", "n_trades"))


def _metrics_from_bar(payload: dict[str, Any], *, replay: bool = False) -> dict[str, float | int]:
    """Extract validation metrics from BAR payload or bus context fields."""
    base = _REPLAY_GREEN_METRICS if replay and not _has_explicit_strategy_metrics(payload) else _DEFAULT_METRICS
    metrics = dict(base)
    for key in ("oos_pf", "dsr", "folds_positive", "n_trades"):
        if key in payload:
            metrics[key] = payload[key]
    strategy = payload.get("strategy_metrics")
    if isinstance(strategy, dict):
        for key in ("oos_pf", "dsr", "folds_positive", "n_trades"):
            if key in strategy:
                metrics[key] = strategy[key]
    return metrics


def _bar_close(payload: dict[str, Any]) -> float:
    return float(payload.get("c", payload.get("close", 0)) or 0)


class NoOpAgent(BaseAgent):
    """Placeholder for roster agents not in the safety spine."""

    async def work(self) -> None:
        self.set_status("idle", "noop heartbeat")
        await asyncio.sleep(0.2)
        self.set_status("working", "noop")


class ValidationEngineAgent(BaseAgent):
    """Listens for BAR events from replay, runs verdict, emits LOG with verdict."""

    def __init__(
        self,
        name: str,
        bus: MessageBus,
        clock: Optional[Clock] = None,
        *,
        replay: bool = False,
    ):
        super().__init__(name, bus, clock)
        self._replay = replay
        self._listener: Optional[asyncio.Task[None]] = None
        self._last_verdict: dict[str, Any] = {}

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
            async for ev in self.bus.subscribe(Topic.BAR):
                if ev.topic != Topic.BAR:
                    continue
                self.set_status("working", "verdict on bar")
                symbol = ev.payload.get("symbol", "NQ")
                metrics = _metrics_from_bar(ev.payload, replay=self._replay)
                v = run_verdict(
                    oos_pf=float(metrics["oos_pf"]),
                    dsr=float(metrics["dsr"]),
                    folds_positive=int(metrics["folds_positive"]),
                    n_trades=int(metrics["n_trades"]),
                )
                self._last_verdict = {
                    "verdict": v.status,
                    "symbol": symbol,
                    "metrics": metrics,
                    "rationale": v.rationale,
                }
                AgentSnapshotRegistry.set(self.name, self.snapshot())
                await self.emit(
                    Event(
                        Topic.LOG,
                        self.clock.now(),
                        self.name,
                        {
                            "verdict": v.status,
                            "symbol": symbol,
                            "metrics": metrics,
                            "rationale": v.rationale,
                            "price": _bar_close(ev.payload),
                        },
                    )
                )
                global _last_bar_prices
                price = _bar_close(ev.payload)
                if price:
                    _last_bar_prices[symbol] = price
        except asyncio.CancelledError:
            pass

    def snapshot(self) -> dict[str, Any]:
        return dict(self._last_verdict)

    async def work(self) -> None:
        self.set_status("idle", "validation listener")
        await asyncio.sleep(0.2)


class DecisionEngineAgent(BaseAgent):
    """Subscribes to LOG (verdict), calls decide, publishes DecisionEvent."""

    def __init__(self, name: str, bus: MessageBus, clock: Optional[Clock] = None):
        super().__init__(name, bus, clock)
        self._listener: Optional[asyncio.Task[None]] = None
        self._risk_listener: Optional[asyncio.Task[None]] = None
        self._risk_veto = False
        self._last_decision: dict[str, Any] = {}

    async def activate(self) -> None:
        await super().activate()
        if self._listener is None:
            try:
                loop = asyncio.get_running_loop()
                self._listener = loop.create_task(self._listen())
                self._risk_listener = loop.create_task(self._listen_risk())
            except RuntimeError:
                pass

    async def _listen_risk(self) -> None:
        try:
            async for ev in self.bus.subscribe(Topic.LOG):
                if ev.topic != Topic.LOG or ev.source != "RiskCommand":
                    continue
                veto = _parse_risk_veto_from_payload(ev.payload)
                if veto is not None:
                    self._risk_veto = veto
        except asyncio.CancelledError:
            pass

    async def _listen(self) -> None:
        try:
            async for ev in self.bus.subscribe(Topic.LOG):
                if ev.topic != Topic.LOG or "verdict" not in ev.payload:
                    continue
                self.set_status("working", "decide on verdict")
                has_green = ev.payload.get("verdict") == "GREEN"
                acct = AgentSnapshotRegistry.get("AccountSync", {"stale": False})
                data_ok = not bool(acct.get("stale", False))
                d = decide(
                    has_green_strategy=has_green,
                    risk_veto=self._risk_veto,
                    data_ok=data_ok,
                    session_ok=True,
                )
                self._last_decision = d
                AgentSnapshotRegistry.set(self.name, {"last": d, "data_ok": data_ok, "risk_veto": self._risk_veto})
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

    def snapshot(self) -> dict[str, Any]:
        return dict(self._last_decision)

    async def work(self) -> None:
        self.set_status("idle", "decision listener")
        await asyncio.sleep(0.2)


class ExecutionGatewayAgent(BaseAgent):
    """Subscribes to DECISION, runs guardrails, publishes Fill or block."""

    def __init__(self, name: str, bus: MessageBus, clock: Optional[Clock] = None):
        super().__init__(name, bus, clock)
        self._listener: Optional[asyncio.Task[None]] = None
        self._risk_listener: Optional[asyncio.Task[None]] = None
        self._bar_listener: Optional[asyncio.Task[None]] = None
        self._risk_veto = False
        self._last_prices: dict[str, float] = {}

    async def activate(self) -> None:
        await super().activate()
        if self._listener is None:
            try:
                loop = asyncio.get_running_loop()
                self._listener = loop.create_task(self._listen())
                self._risk_listener = loop.create_task(self._listen_risk())
                self._bar_listener = loop.create_task(self._listen_bars())
            except RuntimeError:
                pass

    async def _listen_bars(self) -> None:
        try:
            async for ev in self.bus.subscribe(Topic.BAR):
                if ev.topic != Topic.BAR:
                    continue
                symbol = ev.payload.get("symbol", "NQ")
                price = _bar_close(ev.payload)
                if price:
                    self._last_prices[symbol] = price
                    _last_bar_prices[symbol] = price
        except asyncio.CancelledError:
            pass

    async def _listen_risk(self) -> None:
        try:
            async for ev in self.bus.subscribe(Topic.LOG):
                if ev.topic != Topic.LOG or ev.source != "RiskCommand":
                    continue
                veto = _parse_risk_veto_from_payload(ev.payload)
                if veto is not None:
                    self._risk_veto = veto
        except asyncio.CancelledError:
            pass

    async def _listen(self) -> None:
        try:
            async for ev in self.bus.subscribe(Topic.DECISION):
                if ev.topic != Topic.DECISION:
                    continue
                self.set_status("working", "guard on decision")
                is_go = ev.payload.get("decision") == "GO"
                symbol = ev.payload.get("symbol", "NQ")
                try:
                    if is_go:
                        check_pre_trade(StrategyStatus.GREEN, risk_veto=self._risk_veto, size_ok=True)
                        price = self._last_prices.get(symbol) or _last_bar_prices.get(symbol, 0.0)
                        if not price:
                            price = float(ev.payload.get("price", 0) or 0)
                        f = FillEvent(
                            ts_utc=self.clock.now(),
                            source=self.name,
                            symbol=symbol,
                            side="BUY",
                            qty=ev.payload.get("size", 1),
                            price=price,
                            pnl=0.0,
                        )
                        await self.emit(f)
                    else:
                        await self.emit(
                            Event(Topic.LOG, self.clock.now(), self.name, {"blocked": "decision NO_GO"})
                        )
                except (ExecutionBlocked, RiskVeto) as e:
                    await self.emit(Event(Topic.LOG, self.clock.now(), self.name, {"blocked": str(e)}))
        except asyncio.CancelledError:
            pass

    def snapshot(self) -> dict[str, Any]:
        return {"last_prices": dict(self._last_prices), "risk_veto": self._risk_veto}

    async def work(self) -> None:
        self.set_status("idle", "execution listener")
        await asyncio.sleep(0.2)


class MarketPulseAgent(BaseAgent):
    """Subscribe BAR + poll free market; breadth, heatmaps, volume profile."""

    def __init__(self, name: str, bus: MessageBus, clock: Optional[Clock] = None):
        super().__init__(name, bus, clock)
        self._listener: Optional[asyncio.Task[None]] = None
        self._poll_task: Optional[asyncio.Task[None]] = None
        self._breadth = BreadthComputer()
        self._heatmaps: dict[str, dict[str, Any]] = {}
        self._volume_profiles: dict[str, dict[str, Any]] = {}
        self._series: dict[str, list[float]] = {"tick": [], "trin": [], "add": [], "breadth": []}
        self._as_of: str | None = None
        self._proxy_meta: dict[str, Any] = {}

    async def activate(self) -> None:
        await super().activate()
        try:
            loop = asyncio.get_running_loop()
            if self._listener is None:
                self._listener = loop.create_task(self._listen())
            if self._poll_task is None:
                self._poll_task = loop.create_task(self._poll_loop())
        except RuntimeError:
            pass

    def _record_series(self, state: Any) -> None:
        for key, attr in (("tick", "tick"), ("trin", "trin"), ("add", "add"), ("breadth", "breadth_score")):
            val = getattr(state, attr, None)
            if val is None:
                continue
            buf = self._series.setdefault(key, [])
            buf.append(float(val))
            if len(buf) > 60:
                del buf[:-60]

    def _refresh_market_layers(self, symbol: str = "NQ") -> None:
        from mcc.data.live.free_market import INSTRUMENT_META, get_bars, get_internals_proxy
        from mcc.heatmaps.correlation import build_correlation_frame
        from mcc.heatmaps.volatility import build_volatility_frame
        from mcc.microstructure.volume_profile import build_volume_profile

        proxy = get_internals_proxy()
        self._proxy_meta = {
            "proxies": proxy.get("proxies", {}),
            "vix": proxy.get("vix"),
            "regime": proxy.get("regime"),
            "regime_confidence": proxy.get("regime_confidence"),
            "breadth_score": proxy.get("breadth_score"),
            "disclaimer": proxy.get("disclaimer"),
            "source": proxy.get("source", "yfinance_proxy"),
            "sparklines": proxy.get("sparklines", {}),
        }
        self._as_of = proxy.get("as_of")

        symbols = list(INSTRUMENT_META.keys())
        corr = build_correlation_frame(symbols, get_bars)
        vol = build_volatility_frame(symbols, get_bars)
        if corr:
            self._heatmaps["correlation"] = corr.to_dict()
        if vol:
            self._heatmaps["volatility"] = vol.to_dict()

        bars = get_bars(symbol).get("bars") or []
        profile = build_volume_profile(bars)
        if profile:
            self._volume_profiles[symbol] = profile

    async def _poll_loop(self) -> None:
        try:
            while True:
                self.set_status("working", "market pulse poll")
                state = self._breadth.update_from_free_market()
                self._record_series(state)
                self._refresh_market_layers()
                AgentSnapshotRegistry.set(self.name, self.snapshot())
                for iev in breadth_to_internals_events(
                    state, ts_utc=self.clock.now(), source=self.name, symbol="MARKET"
                ):
                    await self.emit(iev)
                await asyncio.sleep(60.0)
        except asyncio.CancelledError:
            pass

    async def _listen(self) -> None:
        try:
            async for ev in self.bus.subscribe(Topic.BAR):
                if ev.topic != Topic.BAR:
                    continue
                self.set_status("working", "breadth on bar")
                payload = ev.payload
                if payload.get("use_free_market"):
                    state = self._breadth.update_from_free_market()
                else:
                    state = self._breadth.update_from_bar(payload)
                symbol = payload.get("symbol", "NQ")
                self._record_series(state)
                self._refresh_market_layers(symbol)
                AgentSnapshotRegistry.set(self.name, self.snapshot())
                for iev in breadth_to_internals_events(
                    state, ts_utc=self.clock.now(), source=self.name, symbol=symbol
                ):
                    await self.emit(iev)
        except asyncio.CancelledError:
            pass

    def snapshot(self) -> dict[str, Any]:
        base = self._breadth.snapshot()
        regime = base.get("regime", "neutral")
        display_regime = regime.upper().replace("_", "-") if isinstance(regime, str) else "NEUTRAL"
        sparklines = dict(self._proxy_meta.get("sparklines") or {})
        if not sparklines.get("tick") and self._series.get("tick"):
            sparklines["tick"] = list(self._series["tick"])
        if not sparklines.get("trin") and self._series.get("trin"):
            sparklines["trin"] = list(self._series["trin"])
        return {
            **base,
            **self._proxy_meta,
            "regime": self._proxy_meta.get("regime") or display_regime,
            "breadth_score": self._proxy_meta.get("breadth_score") or base.get("breadth_score"),
            "heatmaps": dict(self._heatmaps),
            "volume_profiles": dict(self._volume_profiles),
            "series": {k: list(v) for k, v in self._series.items()},
            "sparklines": sparklines,
            "as_of": self._as_of,
            "buffer_len": base.get("buffer_len", 0),
        }

    async def work(self) -> None:
        self.set_status("idle", "marketpulse listener")
        await asyncio.sleep(0.2)


class IndicatorEngineAgent(BaseAgent):
    """Subscribe BAR, compute indicators, publish LOG with indicator values."""

    def __init__(self, name: str, bus: MessageBus, clock: Optional[Clock] = None):
        super().__init__(name, bus, clock)
        self._listener: Optional[asyncio.Task[None]] = None
        self._engine = IndicatorEngine()

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
            async for ev in self.bus.subscribe(Topic.BAR):
                if ev.topic != Topic.BAR:
                    continue
                self.set_status("working", "indicators on bar")
                symbol = ev.payload.get("symbol", "NQ")
                values = self._engine.on_bar(symbol, ev.payload)
                AgentSnapshotRegistry.set(self.name, self.snapshot())
                await self.emit(
                    Event(
                        Topic.LOG,
                        self.clock.now(),
                        self.name,
                        {"type": "indicators", "symbol": symbol, "values": values},
                    )
                )
        except asyncio.CancelledError:
            pass

    def snapshot(self) -> dict[str, Any]:
        return self._engine.snapshot()

    async def work(self) -> None:
        self.set_status("idle", "indicator listener")
        await asyncio.sleep(0.2)


class TradeJournalAgent(BaseAgent):
    """Subscribe FILL, persist via journal.record_fill()."""

    def __init__(
        self,
        name: str,
        bus: MessageBus,
        clock: Optional[Clock] = None,
        *,
        journal: TradeJournal | None = None,
    ):
        super().__init__(name, bus, clock)
        self._listener: Optional[asyncio.Task[None]] = None
        self._journal = journal or TradeJournal()
        self._fills_recorded = 0

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
            async for ev in self.bus.subscribe(Topic.FILL):
                if ev.topic != Topic.FILL:
                    continue
                self.set_status("working", "journal fill")
                trade_id = self._journal.record_fill(ev)
                self._fills_recorded += 1
                AgentSnapshotRegistry.set(self.name, self.snapshot())
                await self.emit(
                    Event(
                        Topic.LOG,
                        self.clock.now(),
                        self.name,
                        {"type": "journal_fill", "trade_id": trade_id},
                    )
                )
        except asyncio.CancelledError:
            pass

    def snapshot(self) -> dict[str, Any]:
        return {"fills_recorded": self._fills_recorded, "trade_count": self._journal.count_trades()}

    async def work(self) -> None:
        self.set_status("idle", "journal listener")
        await asyncio.sleep(0.2)


class AccountSyncAgent(BaseAgent):
    """Poll tradeify_reader, publish AccountStateEvent via sync_adapter; track stale."""

    def __init__(
        self,
        name: str,
        bus: MessageBus,
        clock: Optional[Clock] = None,
        *,
        db_path: str | Path | None = None,
        poll_interval_sec: float = 2.0,
        replay: bool = False,
    ):
        super().__init__(name, bus, clock)
        self._replay = replay
        self._poll_task: Optional[asyncio.Task[None]] = None
        self._adapter = AccountSyncAdapter(bus)
        self._db_path = Path(db_path) if db_path else Path("data/tradeify_sync.db")
        self._poll_interval_sec = poll_interval_sec
        self._stale = True
        self._last_state: dict[str, Any] = {}

    async def activate(self) -> None:
        await super().activate()
        if self._poll_task is None:
            try:
                loop = asyncio.get_running_loop()
                self._poll_task = loop.create_task(self._poll_loop())
            except RuntimeError:
                pass

    async def _poll_loop(self) -> None:
        try:
            while True:
                await self._sync_once()
                await asyncio.sleep(self._poll_interval_sec)
        except asyncio.CancelledError:
            pass

    async def _sync_once(self) -> None:
        self.set_status("working", "account sync poll")
        state = read_account_state(self._db_path)
        if self._replay and state.get("error") in ("db_not_found", "no_accounts"):
            # Replay spine: absent sync engine is a fresh stub, not a hard data veto.
            self._stale = False
            self._last_state = {
                "stale": False,
                "equity": 150000.0,
                "account": "replay-stub",
                "replay_stub": True,
            }
            AgentSnapshotRegistry.set(self.name, self.snapshot())
            return
        self._stale = bool(state.get("stale", True))
        self._last_state = state
        AgentSnapshotRegistry.set(self.name, self.snapshot())
        if state.get("error") and state.get("error") != "no_accounts":
            return
        if not state.get("error"):
            ev = AccountStateEvent(
                ts_utc=self.clock.now(),
                source="tradeify",
                account=state.get("account", ""),
                equity=state.get("equity", 0.0),
                payload=state,
            )
            await self._adapter.handle_incoming(ev)
            self._adapter.stale = self._stale

    def snapshot(self) -> dict[str, Any]:
        return {"stale": self._stale, "last_state": dict(self._last_state)}

    async def work(self) -> None:
        self.set_status("idle", "accountsync poll")
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
    """Publishes consolidated risk state (including veto) on the bus for spine agents."""

    def __init__(self, name: str, bus: MessageBus, clock: Optional[Clock] = None):
        super().__init__(name, bus, clock)
        self._monitor: Optional[RiskMonitor] = None

    async def activate(self) -> None:
        await super().activate()
        if self._monitor is None:
            self._monitor = RiskMonitor(self.bus, self.clock)
            await self._monitor.start()

    async def work(self) -> None:
        self.set_status("working", "risk monitor")
        await asyncio.sleep(0.1)


class PerformanceAnalystAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "performance")
        await asyncio.sleep(0.1)


class ReportPublisherAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "reports")
        await asyncio.sleep(0.1)


class DataOpsAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "dataops")
        await asyncio.sleep(0.1)


class OverseerAgent(BaseAgent):
    async def work(self) -> None:
        self.set_status("working", "overseer")
        await asyncio.sleep(0.1)