from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Tradeify150KSelectFlexRules:
    """Tradeify 150K Select Flex rule constants.

    Keep these values mirrored with config/tradeify_150k_select_flex.yaml.
    Rules should be treated as external constraints and verified before deployment.
    """

    starting_balance: float = 150_000.0
    eval_profit_target: float = 9_000.0
    max_drawdown_eod: float = 4_500.0
    eval_daily_loss_limit: Optional[float] = None
    eval_consistency_max_single_day_pct: float = 0.40
    max_contracts_mini: int = 12
    max_contracts_micro: int = 120

    funded_winning_days_required: int = 5
    funded_winning_day_threshold: float = 250.0
    funded_max_payout_gross: float = 5_000.0
    funded_payout_profit_pct: float = 0.50
    trader_profit_split_pct: float = 0.90
    drawdown_lock_above_start: float = 100.0


@dataclass(frozen=True)
class MarinerXRiskPolicy:
    """Internal risk policy layered on top of Tradeify's rules.

    These are intentionally stricter than the prop-firm limits. The objective is
    payout survival, not maximum intraday leverage.
    """

    max_risk_per_trade_dollars: float = 250.0
    max_daily_loss_dollars: float = 750.0
    hard_daily_stop_dollars: float = 900.0
    max_drawdown_usage_pct: float = 0.50
    emergency_flatten_drawdown_headroom: float = 1_500.0
    first_payout_min_profit_before_request: float = 4_500.0
    max_payout_profit_target: float = 10_000.0
    default_mode: str = "PAPER_FIRST"
