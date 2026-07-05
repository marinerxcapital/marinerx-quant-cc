"""Risk sizing (fixed, fractional Kelly capped, volatility targeting).

Per 08_RISK_ENGINE.md: returns (contract_count, reasoning). Never exceed caps.
Vol-targeting: smaller size as realized vol rises.
Phase 16: Kelly raw fraction sourced from riskfolio_adapter; fractional cap preserved on top.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Tuple

from mcc.analytics.conversion import decimal_to_float
from mcc.risk.riskfolio_adapter import kelly_raw_fraction


def fixed_size(contracts: int = 1, max_contracts: int = 5) -> Tuple[int, str]:
    """Fixed contracts, capped."""
    c = max(1, min(contracts, max_contracts))
    return c, f"fixed: {c} contract(s) (capped at {max_contracts})"


def kelly_size(
    equity: Decimal,
    win_prob: Decimal,
    payoff: Decimal,
    risk_budget: Decimal = Decimal("0.02"),
    cap: Decimal = Decimal("0.5"),
    max_contracts: int = 5,
    tick_value: Decimal = Decimal("20.0"),  # e.g. NQ ~$20 per full point move
) -> Tuple[int, str]:
    """Fractional Kelly (capped) mapped to contracts via risk budget + tick value.

    Raw Kelly fraction is computed by Riskfolio-Lib via riskfolio_adapter; capped at 'cap'.
    Contracts = floor( risk_dollars / per_contract_risk ) with max_contracts cap.
    Output always includes reasoning.
    """
    if payoff <= 0 or win_prob <= 0 or equity <= 0:
        return 0, "kelly: invalid inputs (payoff/win_prob/equity <=0) -> size 0"

    raw_frac, rf_reason = kelly_raw_fraction(win_prob, payoff)
    capped_frac = min(raw_frac, cap)
    risk_dollars = equity * capped_frac * risk_budget
    per_contract_risk = equity * risk_budget / Decimal("2")
    if per_contract_risk <= 0:
        per_contract_risk = Decimal("1000")
    contracts = int(risk_dollars / per_contract_risk)
    contracts = max(1 if risk_dollars > 0 else 0, min(contracts, max_contracts))
    reason = (
        f"kelly: raw_f={decimal_to_float(raw_frac, context='kelly_reason'):.4f} "
        f"capped_f={decimal_to_float(capped_frac, context='kelly_reason'):.4f} "
        f"risk$={decimal_to_float(risk_dollars, context='kelly_reason'):.2f} -> {contracts} contract(s) "
        f"(cap={max_contracts}); {rf_reason}"
    )
    return contracts, reason


def vol_target_size(
    equity: Decimal,
    target_vol: Decimal,
    current_vol: Decimal,
    max_contracts: int = 10,
    tick_value: Decimal = Decimal("20.0"),
) -> Tuple[int, str]:
    """Volatility targeting: scale contracts so $vol exposure ~ target_vol.

    As current_vol (realized) rises, contracts fall. Inputs equity for sanity cap.
    Output: (contracts, reasoning)
    """
    if current_vol <= 0:
        c = 1
        return c, f"vol_target: current_vol<=0 fallback to {c}"
    scale = target_vol / current_vol
    contracts = int(scale)
    contracts = max(1, min(contracts, max_contracts))
    if equity > 0 and contracts * tick_value * Decimal("10") > equity * Decimal("0.1"):
        contracts = max(1, contracts // 2)
    reason = (
        f"vol_target: target_vol={decimal_to_float(target_vol, context='vol_reason'):.2f} "
        f"current_vol={decimal_to_float(current_vol, context='vol_reason'):.2f} "
        f"scale={decimal_to_float(Decimal(str(scale)), context='vol_reason'):.3f} -> {contracts} contract(s) "
        f"(cap={max_contracts}); higher vol shrinks size"
    )
    return contracts, reason


def compute_size(
    equity: Decimal,
    method: str = "kelly",
    **kwargs: Any,
) -> Tuple[int, str]:
    """Unified entry: fixed | kelly | vol_target. Always returns (count, reasoning)."""
    method = method.lower().strip()
    if method == "fixed":
        return fixed_size(
            contracts=kwargs.get("contracts", 1),
            max_contracts=kwargs.get("max_contracts", 5),
        )
    if method == "kelly":
        return kelly_size(
            equity=equity,
            win_prob=kwargs.get("win_prob", Decimal("0.55")),
            payoff=kwargs.get("payoff", Decimal("1.5")),
            risk_budget=kwargs.get("risk_budget", Decimal("0.02")),
            cap=kwargs.get("cap", Decimal("0.5")),
            max_contracts=kwargs.get("max_contracts", 5),
            tick_value=kwargs.get("tick_value", Decimal("20.0")),
        )
    if method == "vol_target":
        return vol_target_size(
            equity=equity,
            target_vol=kwargs.get("target_vol", Decimal("800")),
            current_vol=kwargs.get("current_vol", Decimal("1200")),
            max_contracts=kwargs.get("max_contracts", 10),
            tick_value=kwargs.get("tick_value", Decimal("20.0")),
        )
    return kelly_size(equity, Decimal("0.55"), Decimal("1.5"))