"""Round-trip transaction cost model for futures (Phase 00 + Phase 17 economic significance)."""
from __future__ import annotations

from decimal import Decimal
from typing import Final

# Per-instrument round-trip cost as fraction of notional (commission + slippage estimate).
_DEFAULT_ROUND_TRIP_PCT: Final[dict[str, Decimal]] = {
    "NQ": Decimal("0.00015"),
    "ES": Decimal("0.00012"),
    "CL": Decimal("0.00020"),
    "GC": Decimal("0.00018"),
}
_DEFAULT_FALLBACK: Final[Decimal] = Decimal("0.00015")


def round_trip_cost(instrument: str) -> Decimal:
    """Return round-trip cost in price/return-equivalent terms for an instrument."""
    key = instrument.upper().strip()
    return _DEFAULT_ROUND_TRIP_PCT.get(key, _DEFAULT_FALLBACK)


def round_trip_cost_pct(instrument: str) -> float:
    """Float view of round-trip cost for comparison against OLS return coefficients."""
    return float(round_trip_cost(instrument))