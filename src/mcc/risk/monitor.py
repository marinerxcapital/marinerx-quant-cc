"""Risk monitor + RiskState for RiskCommand agent (Phase 08).

Real-time: subscribes fills/positions/prices (via bus), recomputes sizing/VaR/ES/PropGuardian,
publishes consolidated RiskState snapshots.
Owns kill-switch path (veto).
Throttle updates.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, cast

from mcc.core.events import Event, Topic
from mcc.risk.sizing import compute_size, vol_target_size
from mcc.risk.var_es import VaRResult, historical_var_es, check_var_es_breach
from mcc.risk.prop_guardian import PropGuardian, AccountState, RiskLevel, risk_veto_from_guardian
from mcc.risk.portfolio import aggregate_exposure, Exposure


@dataclass
class RiskState:
    """Consolidated snapshot published by monitor."""
    ts_utc: datetime
    source: str
    equity: Decimal
    risk_level: RiskLevel
    position_size: int
    size_reason: str
    var: float
    es: float
    var_breach: bool
    exposure_gross: Decimal
    exposure_net: Decimal
    veto: bool
    veto_reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["risk_level"] = self.risk_level.value
        d["ts_utc"] = self.ts_utc.isoformat()
        d["equity"] = float(self.equity)
        d["exposure_gross"] = float(self.exposure_gross)
        d["exposure_net"] = float(self.exposure_net)
        return d


class RiskMonitor:
    """Owned by RiskCommand. Real-time risk engine."""

    def __init__(
        self,
        bus: Any,
        clock: Any = None,
        throttle_sec: float = 0.5,
        equity: Decimal = Decimal("100000"),
        max_contracts: int = 5,
    ) -> None:
        self.bus = bus
        self.clock = clock
        self.throttle_sec = throttle_sec
        self._equity = equity
        self._max_contracts = max_contracts
        self._guardian = PropGuardian()
        self._last_state: Optional[RiskState] = None
        self._running = False
        self._task: Optional[asyncio.Task[Any]] = None
        self._pnl_buffer: List[float] = []  # for rolling VaR
        self._positions: List[Dict[str, Any]] = []
        self._fills_seen = 0

    @property
    def current_state(self) -> Optional[RiskState]:
        return self._last_state

    def _now(self) -> datetime:
        if self.clock and hasattr(self.clock, "now"):
            return cast(datetime, self.clock.now())
        return datetime.now(timezone.utc)

    def update_account(self, state: AccountState) -> RiskLevel:
        return self._guardian.update(state)

    def _recompute(self, symbol: str = "NQ") -> RiskState:
        level = self._guardian.get_level()
        veto = risk_veto_from_guardian(level) or (self._guardian.headroom < Decimal("0.05"))

        # Sizing (prefer kelly demo)
        size, reason = compute_size(
            self._equity,
            method="kelly",
            win_prob=Decimal("0.56"),
            payoff=Decimal("1.6"),
            risk_budget=Decimal("0.015"),
            cap=Decimal("0.45"),
            max_contracts=self._max_contracts,
        )
        # Demo vol target influence if vol high
        if len(self._pnl_buffer) > 3:
            # crude current vol proxy from pnl std
            import numpy as np
            vol = float(np.std(self._pnl_buffer[-10:]) * 100) or 800.0
            if vol > 1200:
                vsize, vreason = vol_target_size(
                    self._equity, Decimal("700"), Decimal(str(vol)), self._max_contracts
                )
                if vsize < size:
                    size, reason = vsize, vreason

        # VaR/ES on rolling pnl buffer (synthetic returns)
        if len(self._pnl_buffer) < 5:
            self._pnl_buffer.extend([-100, 50, -300, 120, -80])  # seed
        var_res: VaRResult = historical_var_es(
            [p / float(self._equity) for p in self._pnl_buffer[-20:]],
            confidence=0.95,
            limit_var=0.018,
            limit_es=0.028,
        )
        var_breach = check_var_es_breach(var_res) or var_res.var > 0.025

        # Portfolio exposure
        exp: Exposure = aggregate_exposure(self._positions or [{"symbol": symbol, "qty": size, "notional": 15000 * size}])

        if var_breach or veto:
            # shrink size on risk
            size = max(0, size // 2)
            if veto:
                reason = (self._guardian.get_veto_reason() or "risk veto") + " | size reduced"

        state = RiskState(
            ts_utc=self._now(),
            source="RiskMonitor",
            equity=self._equity,
            risk_level=level,
            position_size=size,
            size_reason=reason,
            var=var_res.var,
            es=var_res.es,
            var_breach=var_breach or veto,
            exposure_gross=exp.gross,
            exposure_net=exp.net,
            veto=veto or var_breach,
            veto_reason=self._guardian.get_veto_reason() if veto else None,
            details={
                "headroom": float(self._guardian.headroom),
                "daily_pnl": float(self._guardian.daily_pnl),
                "var_limit_breach": var_breach,
                "positions": len(self._positions),
                "fills": self._fills_seen,
            },
        )
        self._last_state = state
        return state

    async def _publish_state(self, state: RiskState) -> None:
        # Publish as LOG for now (or extend events later); also as generic Event for interface
        payload = state.to_dict()
        await self.bus.publish(
            Event(Topic.LOG, state.ts_utc, "RiskCommand", {"risk_state": payload, "veto": state.veto})
        )

    async def _listen_fills(self) -> None:
        """Subscribe to FILLs to update positions/pnl and recompute."""
        try:
            async for ev in self.bus.subscribe(Topic.FILL):
                if getattr(ev, "topic", None) != Topic.FILL:
                    continue
                self._fills_seen += 1
                payload = getattr(ev, "payload", ev) if isinstance(ev, dict) else getattr(ev, "payload", {})
                pnl = float(payload.get("pnl", 0.0))
                self._pnl_buffer.append(pnl)
                if len(self._pnl_buffer) > 50:
                    self._pnl_buffer = self._pnl_buffer[-30:]
                # crude position update
                sym = payload.get("symbol", "NQ")
                qty = int(payload.get("qty", 1))
                self._positions = [p for p in self._positions if p.get("symbol") != sym]
                self._positions.append({"symbol": sym, "qty": qty, "notional": 15000 * qty})
                if len(self._positions) > 5:
                    self._positions = self._positions[-5:]

                # Recompute + publish throttled
                state = self._recompute(sym)
                await self._publish_state(state)
                await asyncio.sleep(self.throttle_sec)  # throttle
        except asyncio.CancelledError:
            pass

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        # Initial state
        init_state = self._recompute()
        await self._publish_state(init_state)
        # Start listener
        self._task = asyncio.create_task(self._listen_fills())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def simulate_fill_stream(self, fills: List[Dict[str, Any]]) -> List[RiskState]:
        """Helper for tests: feed simulated fills, return captured RiskStates (within throttle)."""
        states: List[RiskState] = []
        for f in fills:
            self._fills_seen += 1
            pnl = float(f.get("pnl", 0))
            self._pnl_buffer.append(pnl)
            sym = f.get("symbol", "NQ")
            qty = int(f.get("qty", 1))
            self._positions = [{"symbol": sym, "qty": qty, "notional": 15000 * qty}]
            st = self._recompute(sym)
            states.append(st)
            await asyncio.sleep(0.01)  # simulate fast but within
        return states


def get_risk_veto(state: Optional[RiskState]) -> bool:
    return bool(state and state.veto)