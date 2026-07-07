from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from marinerx_tradeify.models import AccountPhase, AccountSnapshot, TradeDecision

from .base import BrokerAccountMetrics, TradeifyDashboardMetrics


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def infer_phase(dashboard: Optional[TradeifyDashboardMetrics]) -> AccountPhase:
    if dashboard and dashboard.phase.upper().startswith("FUNDED"):
        return AccountPhase.FUNDED_FLEX
    return AccountPhase.EVALUATION


def merge_to_account_snapshot(
    broker: BrokerAccountMetrics,
    dashboard: Optional[TradeifyDashboardMetrics] = None,
) -> AccountSnapshot:
    floor = dashboard.drawdown_floor if dashboard and dashboard.drawdown_floor is not None else broker.eod_drawdown_floor
    if floor is None:
        floor = 145_500.0

    balance = broker.balance
    if dashboard and dashboard.current_balance is not None:
        balance = float(dashboard.current_balance)

    day_pnl = broker.realized_day_pnl
    if dashboard and dashboard.realized_day_pnl is not None:
        day_pnl = float(dashboard.realized_day_pnl)

    return AccountSnapshot(
        phase=infer_phase(dashboard),
        balance=balance,
        eod_drawdown_floor=float(floor),
        realized_day_pnl=day_pnl,
        open_trade_risk=broker.open_trade_risk,
        total_eval_profit=(
            dashboard.total_profit
            if dashboard and dashboard.total_profit is not None
            else max(0.0, balance - 150_000.0)
        ),
    )


@dataclass(frozen=True)
class ReconciliationResult:
    ok: bool
    block_trades: bool
    status: str
    balance_delta: float
    pnl_delta: float
    warnings: list[str] = field(default_factory=list)
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "block_trades": self.block_trades,
            "status": self.status,
            "reconciliation": self.status,
            "balance_delta": round(self.balance_delta, 2),
            "pnl_delta": round(self.pnl_delta, 2),
            "warnings": self.warnings,
            "observed_at": self.observed_at.isoformat(),
            "safe_default": "BLOCK_NEW_TRADES" if self.block_trades else "ALLOW_WITH_CAUTION",
        }


def _tolerance() -> float:
    return float(os.getenv("MARINERX_TRADEIFY_RECONCILIATION_TOLERANCE", "25"))


def _stale_block_seconds() -> int:
    return int(os.getenv("MARINERX_TRADEIFY_STALE_BLOCK_SECONDS", "180"))


def check_stale(observed_at: datetime | None, *, now: datetime | None = None) -> tuple[bool, str]:
    if observed_at is None:
        return True, "NO_TIMESTAMP"
    now = now or datetime.now(timezone.utc)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    age = (now - observed_at).total_seconds()
    if age > _stale_block_seconds():
        return True, f"STALE_DATA_{int(age)}s"
    return False, "FRESH"


def reconcile(
    broker: BrokerAccountMetrics,
    dashboard: Optional[TradeifyDashboardMetrics] = None,
    *,
    dashboard_required: bool = False,
) -> ReconciliationResult:
    warnings: list[str] = []
    tol = _tolerance()

    stale_broker, stale_reason = check_stale(broker.observed_at)
    if stale_broker:
        return ReconciliationResult(
            ok=False,
            block_trades=True,
            status="stale_broker",
            balance_delta=0.0,
            pnl_delta=0.0,
            warnings=[stale_reason],
        )

    if dashboard is None:
        if dashboard_required:
            return ReconciliationResult(
                ok=False,
                block_trades=True,
                status="dashboard_missing",
                balance_delta=0.0,
                pnl_delta=0.0,
                warnings=["Dashboard metrics required but unavailable"],
            )
        if broker.eod_drawdown_floor is None:
            return ReconciliationResult(
                ok=False,
                block_trades=True,
                status="missing_drawdown_floor",
                balance_delta=0.0,
                pnl_delta=0.0,
                warnings=["Drawdown floor unknown — blocking new trades"],
            )
        return ReconciliationResult(ok=True, block_trades=False, status="broker_only", balance_delta=0.0, pnl_delta=0.0)

    stale_dash, dash_reason = check_stale(dashboard.observed_at)
    if stale_dash:
        return ReconciliationResult(
            ok=False,
            block_trades=True,
            status="stale_dashboard",
            balance_delta=0.0,
            pnl_delta=0.0,
            warnings=[dash_reason],
        )

    balance_delta = 0.0
    pnl_delta = 0.0
    if dashboard.current_balance is not None:
        balance_delta = abs(broker.balance - float(dashboard.current_balance))
    if dashboard.realized_day_pnl is not None:
        pnl_delta = abs(broker.realized_day_pnl - float(dashboard.realized_day_pnl))

    if balance_delta > tol:
        warnings.append(f"Balance mismatch ${balance_delta:.2f} exceeds tolerance ${tol:.2f}")
    if pnl_delta > tol:
        warnings.append(f"Daily PnL mismatch ${pnl_delta:.2f} exceeds tolerance ${tol:.2f}")

    block = bool(warnings)
    status = "matched" if not warnings else "mismatch"
    return ReconciliationResult(
        ok=not block,
        block_trades=block,
        status=status,
        balance_delta=balance_delta,
        pnl_delta=pnl_delta,
        warnings=warnings,
    )


def data_health_gate_decision(reconciliation: ReconciliationResult) -> tuple[TradeDecision, str]:
    if reconciliation.block_trades:
        return TradeDecision.BLOCK, reconciliation.status.upper() + ": " + "; ".join(reconciliation.warnings)
    if reconciliation.warnings:
        return TradeDecision.REDUCE_SIZE, "; ".join(reconciliation.warnings)
    return TradeDecision.ALLOW, "DATA_HEALTH_OK"


def merge_with_reconciliation(
    broker: BrokerAccountMetrics,
    dashboard: Optional[TradeifyDashboardMetrics] = None,
    *,
    dashboard_required: bool = False,
) -> tuple[AccountSnapshot, ReconciliationResult]:
    snapshot = merge_to_account_snapshot(broker, dashboard)
    rec = reconcile(broker, dashboard, dashboard_required=dashboard_required)
    return snapshot, rec