from __future__ import annotations

import hashlib
from typing import Optional

from marinerx_tradeify.models import AccountPhase, AccountSnapshot

from .base import BrokerAccountMetrics, TradeifyDashboardMetrics


def stable_hash(value: str) -> str:
    """Hash sensitive account identifiers before persistence/logging."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def infer_phase(dashboard: Optional[TradeifyDashboardMetrics]) -> AccountPhase:
    if dashboard and dashboard.phase.upper().startswith("FUNDED"):
        return AccountPhase.FUNDED_FLEX
    return AccountPhase.EVALUATION


def merge_to_account_snapshot(
    broker: BrokerAccountMetrics,
    dashboard: Optional[TradeifyDashboardMetrics] = None,
) -> AccountSnapshot:
    """Merge broker telemetry and Tradeify dashboard metrics into the MarinerX snapshot model.

    Priority order:
    1. Broker values for balance, realized day PnL, open risk, and positions.
    2. Tradeify dashboard values for prop-firm-specific limits and phase.
    3. Conservative fallbacks when a dashboard field is missing.
    """
    floor = dashboard.drawdown_floor if dashboard and dashboard.drawdown_floor is not None else broker.eod_drawdown_floor
    if floor is None:
        # Conservative fallback for a 150K account with $4,500 EOD max loss.
        floor = 145_500.0

    return AccountSnapshot(
        phase=infer_phase(dashboard),
        balance=broker.balance,
        eod_drawdown_floor=floor,
        realized_day_pnl=broker.realized_day_pnl,
        open_trade_risk=broker.open_trade_risk,
        total_eval_profit=dashboard.total_profit if dashboard and dashboard.total_profit is not None else max(0.0, broker.balance - 150_000.0),
    )
