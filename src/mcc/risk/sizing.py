"""Risk sizing (Kelly/vol target, capped)."""
from decimal import Decimal

def kelly_size(equity: Decimal, win_prob: Decimal, payoff: Decimal, cap: Decimal = Decimal('0.5')) -> Decimal:
    if payoff <= 0:
        return Decimal(0)
    k = win_prob - (1 - win_prob) / payoff
    return min(k * equity, cap * equity)

def vol_target_size(equity: Decimal, target_vol: Decimal, current_vol: Decimal, max_contracts: int = 10) -> int:
    if current_vol <= 0:
        return 1
    scale = target_vol / current_vol
    contracts = int(scale * 2)  # rough for demo
    return max(1, min(contracts, max_contracts))
