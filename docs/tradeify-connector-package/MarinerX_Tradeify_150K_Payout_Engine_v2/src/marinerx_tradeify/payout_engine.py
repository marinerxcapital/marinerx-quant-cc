from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import DayResult
from .rules import MarinerXRiskPolicy, Tradeify150KSelectFlexRules


@dataclass(frozen=True)
class PayoutStatus:
    balance: float
    total_profit: float
    winning_days: int
    eligible_by_days: bool
    gross_payout_available: float
    trader_net_payout: float
    profit_needed_for_max_gross_payout: float
    additional_profit_needed_for_max: float
    safe_to_request_under_marinerx_policy: bool
    recommended_gross_request: float
    post_payout_balance: float
    risk_note: str


def count_winning_days(day_results: Iterable[DayResult], threshold: float) -> int:
    return sum(1 for day in day_results if day.realized_pnl >= threshold)


def calculate_flex_payout(
    balance: float,
    day_results: Iterable[DayResult],
    rules: Tradeify150KSelectFlexRules | None = None,
    policy: MarinerXRiskPolicy | None = None,
) -> PayoutStatus:
    rules = rules or Tradeify150KSelectFlexRules()
    policy = policy or MarinerXRiskPolicy()

    day_results = list(day_results)
    total_profit = max(0.0, balance - rules.starting_balance)
    winning_days = count_winning_days(day_results, rules.funded_winning_day_threshold)
    eligible_by_days = winning_days >= rules.funded_winning_days_required

    gross_available = min(total_profit * rules.funded_payout_profit_pct, rules.funded_max_payout_gross)
    if not eligible_by_days:
        gross_available = 0.0

    profit_needed_for_max = rules.funded_max_payout_gross / rules.funded_payout_profit_pct
    additional_profit_needed_for_max = max(0.0, profit_needed_for_max - total_profit)

    # Internal policy: do not request if it strips the account too thin.
    min_profit_before_request = policy.first_payout_min_profit_before_request
    safe_to_request = eligible_by_days and total_profit >= min_profit_before_request

    recommended_gross_request = 0.0
    if safe_to_request:
        # Conservative: request up to half profits, but leave at least half profits in account.
        recommended_gross_request = gross_available

    post_payout_balance = balance - recommended_gross_request
    risk_note = "NOT_ELIGIBLE"
    if eligible_by_days and not safe_to_request:
        risk_note = "ELIGIBLE_BY_RULES_BUT_NOT_BY_MARINERX_POLICY: build more cushion before withdrawing."
    elif safe_to_request and additional_profit_needed_for_max > 0:
        risk_note = "PARTIAL_PAYOUT_ZONE: payout allowed, max payout requires more cushion."
    elif safe_to_request and additional_profit_needed_for_max == 0:
        risk_note = "MAX_PAYOUT_ZONE: gross cap available; verify rule status before request."

    return PayoutStatus(
        balance=balance,
        total_profit=total_profit,
        winning_days=winning_days,
        eligible_by_days=eligible_by_days,
        gross_payout_available=gross_available,
        trader_net_payout=gross_available * rules.trader_profit_split_pct,
        profit_needed_for_max_gross_payout=profit_needed_for_max,
        additional_profit_needed_for_max=additional_profit_needed_for_max,
        safe_to_request_under_marinerx_policy=safe_to_request,
        recommended_gross_request=recommended_gross_request,
        post_payout_balance=post_payout_balance,
        risk_note=risk_note,
    )
