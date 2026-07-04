"""Strategy status lifecycle (P1: only verdict can promote to GREEN)."""
from __future__ import annotations
from enum import Enum

class StrategyStatus(str, Enum):
    DRAFT = "DRAFT"
    REGISTERED = "REGISTERED"
    TESTED = "TESTED"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"

_ALLOWED = {
    StrategyStatus.DRAFT: {StrategyStatus.REGISTERED},
    StrategyStatus.REGISTERED: {StrategyStatus.TESTED},
    StrategyStatus.TESTED: {StrategyStatus.GREEN, StrategyStatus.YELLOW, StrategyStatus.RED},
    StrategyStatus.GREEN: set(),
    StrategyStatus.YELLOW: {StrategyStatus.GREEN, StrategyStatus.RED},
    StrategyStatus.RED: set(),
}

def can_transition(current: StrategyStatus, target: StrategyStatus) -> bool:
    return target in _ALLOWED.get(current, set())

def transition(current: StrategyStatus, target: StrategyStatus, has_passing_verdict: bool = False) -> StrategyStatus:
    if not can_transition(current, target):
        raise ValueError(f"Illegal transition {current} -> {target}")
    if target == StrategyStatus.GREEN and not has_passing_verdict:
        raise ValueError("GREEN requires a passing verdict (no override)")
    return target
