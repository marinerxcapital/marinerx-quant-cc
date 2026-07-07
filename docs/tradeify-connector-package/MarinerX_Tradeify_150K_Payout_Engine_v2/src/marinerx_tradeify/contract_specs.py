from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContractSpec:
    symbol: str
    mini_point_value: float
    micro_point_value: float


CONTRACT_SPECS = {
    "NQ": ContractSpec("NQ", mini_point_value=20.0, micro_point_value=2.0),
    "MNQ": ContractSpec("MNQ", mini_point_value=20.0, micro_point_value=2.0),
    "ES": ContractSpec("ES", mini_point_value=50.0, micro_point_value=5.0),
    "MES": ContractSpec("MES", mini_point_value=50.0, micro_point_value=5.0),
    "CL": ContractSpec("CL", mini_point_value=1000.0, micro_point_value=100.0),
    "MCL": ContractSpec("MCL", mini_point_value=1000.0, micro_point_value=100.0),
    "GC": ContractSpec("GC", mini_point_value=100.0, micro_point_value=10.0),
    "MGC": ContractSpec("MGC", mini_point_value=100.0, micro_point_value=10.0),
}


def dollars_at_risk(symbol: str, contract_type: str, contracts: int, points_at_risk: float) -> float:
    base = symbol.upper()
    if base not in CONTRACT_SPECS:
        # Try to map micro symbols to base symbols where appropriate.
        if base.startswith("M") and base[1:] in CONTRACT_SPECS:
            base = base[1:]
        else:
            raise ValueError(f"Unsupported symbol for risk sizing: {symbol}")
    spec = CONTRACT_SPECS[base]
    point_value = spec.micro_point_value if contract_type.lower() == "micro" else spec.mini_point_value
    return contracts * points_at_risk * point_value
