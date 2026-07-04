"""Verdict (P1). Synthetic good edge -> GREEN."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Verdict:
    status: str
    dsr: float
    pf: float
    rationale: str

def run_verdict(oos_pf: float, dsr: float, folds_positive: int, n_trades: int) -> Verdict:
    if oos_pf >= 1.25 and dsr > 0 and folds_positive >= 4 and n_trades >= 100:
        return Verdict('GREEN', dsr, oos_pf, 'synthetic edge beats baseline + sufficient OOS')
    return Verdict('RED', dsr, oos_pf, 'insufficient edge or sample')
