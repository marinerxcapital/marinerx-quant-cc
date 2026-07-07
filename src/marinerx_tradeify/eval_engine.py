from __future__ import annotations

from dataclasses import dataclass

from .rules import Tradeify150KSelectFlexRules


@dataclass(frozen=True)
class EvalStatus:
    total_profit: float
    largest_winning_day: float
    required_total_for_consistency: float
    remaining_profit_to_target: float
    remaining_profit_to_consistency: float
    pass_eligible: bool
    max_allowed_single_day_at_current_total: float
    warning: str


def evaluate_select_150k_eval(total_profit: float, largest_winning_day: float, rules: Tradeify150KSelectFlexRules | None = None) -> EvalStatus:
    rules = rules or Tradeify150KSelectFlexRules()
    required_total_for_consistency = largest_winning_day / rules.eval_consistency_max_single_day_pct if largest_winning_day > 0 else 0.0
    effective_required_total = max(rules.eval_profit_target, required_total_for_consistency)
    remaining_profit_to_target = max(0.0, rules.eval_profit_target - total_profit)
    remaining_profit_to_consistency = max(0.0, required_total_for_consistency - total_profit)
    pass_eligible = total_profit >= rules.eval_profit_target and largest_winning_day <= rules.eval_consistency_max_single_day_pct * total_profit
    max_allowed_single_day_at_current_total = rules.eval_consistency_max_single_day_pct * max(total_profit, 0.0)

    warning = "OK"
    if not pass_eligible and remaining_profit_to_consistency > 0:
        warning = "CONSISTENCY_DEFICIT: reduce size and add smaller green days before attempting to pass."
    elif not pass_eligible and remaining_profit_to_target > 0:
        warning = "PROFIT_TARGET_DEFICIT: continue only inside MarinerX daily risk policy."

    return EvalStatus(
        total_profit=total_profit,
        largest_winning_day=largest_winning_day,
        required_total_for_consistency=required_total_for_consistency,
        remaining_profit_to_target=remaining_profit_to_target,
        remaining_profit_to_consistency=remaining_profit_to_consistency,
        pass_eligible=pass_eligible,
        max_allowed_single_day_at_current_total=max_allowed_single_day_at_current_total,
        warning=warning,
    )
