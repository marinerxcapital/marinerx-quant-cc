from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List, Optional


class AccountPhase(str, Enum):
    EVALUATION = "EVALUATION"
    FUNDED_FLEX = "FUNDED_FLEX"


class TradeDecision(str, Enum):
    ALLOW = "ALLOW"
    REDUCE_SIZE = "REDUCE_SIZE"
    BLOCK = "BLOCK"
    FLATTEN = "FLATTEN"


@dataclass(frozen=True)
class DayResult:
    date: str
    realized_pnl: float


@dataclass(frozen=True)
class AccountSnapshot:
    phase: AccountPhase
    balance: float
    eod_drawdown_floor: float
    realized_day_pnl: float
    open_trade_risk: float = 0.0
    largest_winning_day: float = 0.0
    total_eval_profit: float = 0.0
    funded_cycle_start_balance: Optional[float] = None
    funded_day_results: List[DayResult] = field(default_factory=list)

    @property
    def drawdown_headroom(self) -> float:
        return self.balance - self.eod_drawdown_floor

    @property
    def funded_total_profit(self) -> float:
        return self.balance - 150_000.0


@dataclass(frozen=True)
class SignalIntent:
    symbol: str
    direction: str
    setup_name: str
    entry_price: float
    stop_price: float
    target_price: float
    contract_type: str = "micro"  # micro or mini
    requested_contracts: int = 1

    @property
    def points_at_risk(self) -> float:
        return abs(self.entry_price - self.stop_price)


@dataclass(frozen=True)
class GateResult:
    decision: TradeDecision
    approved_contracts: int
    reason: str
    max_risk_dollars: float
    projected_risk_dollars: float
    drawdown_headroom_after_loss: float
