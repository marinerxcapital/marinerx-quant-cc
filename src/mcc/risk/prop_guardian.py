"""PropGuardian: trailing drawdown, daily loss, consistency, LOCKOUT veto (P2).

Per 08: track headroom, emit tiered RiskLevel OK -> CAUTION -> LOCKOUT.
LOCKOUT is hard veto.
Consume account state (from Phase02 adapter).
"""
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional


class RiskLevel(str, Enum):
    OK = "OK"
    CAUTION = "CAUTION"
    LOCKOUT = "LOCKOUT"


@dataclass(frozen=True)
class AccountState:
    equity: Decimal
    daily_pnl: Decimal
    trailing_dd_floor: Decimal  # e.g. 0.90 = 10% max dd from peak
    peak_equity: Decimal
    consistency: Decimal = Decimal("0.8")  # 0-1 metric


def get_risk_level(headroom: Decimal, daily_loss: Decimal) -> RiskLevel:
    """Legacy simple threshold (kept for compat)."""
    if headroom < Decimal("0.1") or daily_loss < Decimal("-0.03"):
        return RiskLevel.LOCKOUT
    if headroom < Decimal("0.3"):
        return RiskLevel.CAUTION
    return RiskLevel.OK


class PropGuardian:
    """Stateful PropGuardian. Updates from AccountState, returns level + veto flag + reason."""

    # Thresholds per acceptance: OK, CAUTION at 0.3, LOCKOUT at 0.1 or daily loss breach
    CAUTION_HEADROOM = Decimal("0.30")
    LOCKOUT_HEADROOM = Decimal("0.10")
    DAILY_LOSS_LOCK = Decimal("-0.03")  # 3% daily loss

    def __init__(self) -> None:
        self._last_level: RiskLevel = RiskLevel.OK
        self._headroom: Decimal = Decimal("1.0")
        self._daily_pnl: Decimal = Decimal("0")
        self._veto_events: list[Dict[str, Any]] = []

    def update(self, state: AccountState) -> RiskLevel:
        """Compute current level from state. Side effect: record veto if LOCKOUT."""
        peak = max(state.peak_equity, state.equity)
        dd = (peak - state.equity) / peak if peak > 0 else Decimal(0)
        headroom = max(Decimal(0), Decimal("1.0") - dd)  # remaining to floor

        # Also factor daily
        daily_loss = state.daily_pnl / state.equity if state.equity > 0 else Decimal(0)

        self._headroom = headroom
        self._daily_pnl = state.daily_pnl

        if headroom < self.LOCKOUT_HEADROOM or daily_loss < self.DAILY_LOSS_LOCK:
            level = RiskLevel.LOCKOUT
        elif headroom < self.CAUTION_HEADROOM:
            level = RiskLevel.CAUTION
        else:
            level = RiskLevel.OK

        if level == RiskLevel.LOCKOUT and self._last_level != RiskLevel.LOCKOUT:
            veto = {
                "type": "LOCKOUT",
                "headroom": float(headroom),
                "daily_loss": float(daily_loss),
                "reason": f"PropGuardian LOCKOUT: headroom={float(headroom):.3f} daily_pnl_pct={float(daily_loss):.4f}",
            }
            self._veto_events.append(veto)

        self._last_level = level
        return level

    @property
    def headroom(self) -> Decimal:
        return self._headroom

    @property
    def daily_pnl(self) -> Decimal:
        return self._daily_pnl

    def is_veto(self) -> bool:
        return self._last_level == RiskLevel.LOCKOUT

    def get_veto_reason(self) -> Optional[str]:
        if self._veto_events:
            return self._veto_events[-1].get("reason")
        return None

    def get_level(self) -> RiskLevel:
        return self._last_level

    def drawdown_headroom(self) -> Decimal:
        return self._headroom

    def consume_veto_event(self) -> Optional[Dict[str, Any]]:
        """For monitor/decision integration: pop last veto if any."""
        if self._veto_events:
            return self._veto_events.pop()
        return None


def from_account_state(state: AccountState) -> RiskLevel:
    """Convenience functional wrapper."""
    pg = PropGuardian()
    return pg.update(state)


def risk_veto_from_guardian(level: RiskLevel) -> bool:
    """Returns True if level causes hard veto (LOCKOUT)."""
    return level == RiskLevel.LOCKOUT