from __future__ import annotations

from .contract_specs import dollars_at_risk
from .models import AccountPhase, AccountSnapshot, GateResult, SignalIntent, TradeDecision
from .rules import MarinerXRiskPolicy, Tradeify150KSelectFlexRules


def gate_trade(
    snapshot: AccountSnapshot,
    signal: SignalIntent,
    rules: Tradeify150KSelectFlexRules | None = None,
    policy: MarinerXRiskPolicy | None = None,
) -> GateResult:
    """Pre-trade risk gate for MarinerX Trade-or-No-Trade.

    Returns ALLOW/REDUCE_SIZE/BLOCK/FLATTEN. This function should be called before
    any order is staged. It does not place orders.
    """
    rules = rules or Tradeify150KSelectFlexRules()
    policy = policy or MarinerXRiskPolicy()

    if snapshot.drawdown_headroom <= policy.emergency_flatten_drawdown_headroom:
        return GateResult(
            decision=TradeDecision.FLATTEN,
            approved_contracts=0,
            reason="DRAWNDOWN_HEADROOM_EMERGENCY_FLATTEN",
            max_risk_dollars=0.0,
            projected_risk_dollars=0.0,
            drawdown_headroom_after_loss=snapshot.drawdown_headroom,
        )

    if snapshot.realized_day_pnl <= -policy.hard_daily_stop_dollars:
        return GateResult(
            decision=TradeDecision.BLOCK,
            approved_contracts=0,
            reason="MARINERX_HARD_DAILY_STOP_REACHED",
            max_risk_dollars=0.0,
            projected_risk_dollars=0.0,
            drawdown_headroom_after_loss=snapshot.drawdown_headroom,
        )

    if snapshot.realized_day_pnl <= -policy.max_daily_loss_dollars:
        return GateResult(
            decision=TradeDecision.BLOCK,
            approved_contracts=0,
            reason="MARINERX_DAILY_LOSS_LIMIT_REACHED",
            max_risk_dollars=0.0,
            projected_risk_dollars=0.0,
            drawdown_headroom_after_loss=snapshot.drawdown_headroom,
        )

    max_contracts = rules.max_contracts_micro if signal.contract_type.lower() == "micro" else rules.max_contracts_mini
    requested_contracts = min(signal.requested_contracts, max_contracts)

    max_risk_allowed = min(
        policy.max_risk_per_trade_dollars,
        max(0.0, policy.hard_daily_stop_dollars + snapshot.realized_day_pnl),
        max(0.0, snapshot.drawdown_headroom - policy.emergency_flatten_drawdown_headroom),
    )

    if max_risk_allowed <= 0:
        return GateResult(
            decision=TradeDecision.BLOCK,
            approved_contracts=0,
            reason="NO_AVAILABLE_RISK_BUDGET",
            max_risk_dollars=max_risk_allowed,
            projected_risk_dollars=0.0,
            drawdown_headroom_after_loss=snapshot.drawdown_headroom,
        )

    approved = requested_contracts
    projected = dollars_at_risk(signal.symbol, signal.contract_type, approved, signal.points_at_risk)
    while approved > 0 and projected > max_risk_allowed:
        approved -= 1
        projected = dollars_at_risk(signal.symbol, signal.contract_type, approved, signal.points_at_risk) if approved else 0.0

    if approved <= 0:
        return GateResult(
            decision=TradeDecision.BLOCK,
            approved_contracts=0,
            reason="STOP_DISTANCE_TOO_WIDE_FOR_RISK_BUDGET",
            max_risk_dollars=max_risk_allowed,
            projected_risk_dollars=0.0,
            drawdown_headroom_after_loss=snapshot.drawdown_headroom,
        )

    decision = TradeDecision.ALLOW if approved == signal.requested_contracts else TradeDecision.REDUCE_SIZE
    reason = "APPROVED" if decision == TradeDecision.ALLOW else "SIZE_REDUCED_TO_FIT_RISK_BUDGET"

    return GateResult(
        decision=decision,
        approved_contracts=approved,
        reason=reason,
        max_risk_dollars=max_risk_allowed,
        projected_risk_dollars=projected,
        drawdown_headroom_after_loss=snapshot.drawdown_headroom - projected,
    )
