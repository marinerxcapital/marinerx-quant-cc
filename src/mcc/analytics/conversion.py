"""Decimal <-> float conversion boundary — single source of truth (Phase 16)."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Sequence

from mcc.core.exceptions import AnalyticsConversionError

_MONEY_QUANT = Decimal("0.00000001")


def decimal_to_float(value: Decimal, *, context: str = "analytics") -> float:
    """Convert Decimal to float for wrapped library calls only."""
    if not isinstance(value, Decimal):
        raise AnalyticsConversionError(
            f"{context}: expected Decimal, got {type(value).__name__}",
            {"value": repr(value)},
        )
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise AnalyticsConversionError(f"{context}: invalid Decimal -> float", {"value": str(value)}) from exc


def float_to_decimal(value: float, *, precision: int = 8, context: str = "analytics") -> Decimal:
    """Convert library float output back to Decimal for persistence/bus events."""
    try:
        q = Decimal(10) ** -precision
        return Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP)
    except (TypeError, ValueError) as exc:
        raise AnalyticsConversionError(f"{context}: invalid float -> Decimal", {"value": value}) from exc


def series_decimal_to_float(values: Sequence[Decimal]) -> list[float]:
    """Convert a sequence of Decimals for numpy/pandas library input."""
    return [decimal_to_float(v, context="series") for v in values]


def series_float_to_decimal(values: Iterable[float], *, precision: int = 8) -> list[Decimal]:
    """Convert library float series back to Decimal."""
    return [float_to_decimal(v, precision=precision, context="series") for v in values]


def json_number(value: Decimal) -> float:
    """JSON serialization boundary for report schemas (Section 8)."""
    return decimal_to_float(value, context="json_export")