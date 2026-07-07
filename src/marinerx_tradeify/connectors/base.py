from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class PositionSnapshot:
    symbol: str
    net_quantity: int
    average_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None


@dataclass(frozen=True)
class BrokerAccountMetrics:
    source: str
    account_name: str
    account_id_hash: str
    balance: float
    net_liq: Optional[float]
    cash_balance: Optional[float]
    realized_day_pnl: float
    unrealized_pnl: float
    open_trade_risk: float
    eod_drawdown_floor: Optional[float]
    positions: list[PositionSnapshot] = field(default_factory=list)
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def drawdown_headroom(self) -> Optional[float]:
        if self.eod_drawdown_floor is None:
            return None
        return self.balance - self.eod_drawdown_floor


@dataclass(frozen=True)
class TradeifyDashboardMetrics:
    source: str
    account_label: str
    phase: str
    account_size: int
    current_balance: Optional[float]
    realized_day_pnl: Optional[float]
    total_profit: Optional[float]
    max_drawdown_limit: Optional[float]
    drawdown_floor: Optional[float]
    winning_days: Optional[int]
    payout_eligible: Optional[bool]
    next_payout_cap: Optional[float]
    last_payout_status: Optional[str]
    consistency_current_pct: Optional[float]
    raw: dict[str, Any] = field(default_factory=dict)
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
