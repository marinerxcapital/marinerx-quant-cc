"""Unit tests for analytics/conversion.py — Decimal <-> float boundary."""
from __future__ import annotations

from decimal import Decimal

import pytest

from mcc.analytics.conversion import (
    decimal_to_float,
    float_to_decimal,
    json_number,
    series_decimal_to_float,
    series_float_to_decimal,
)
from mcc.core.exceptions import AnalyticsConversionError


def test_decimal_float_round_trip_exact_cents():
    original = Decimal("12345.67890123")
    back = float_to_decimal(decimal_to_float(original), precision=8)
    assert back == Decimal("12345.67890123")


def test_series_round_trip():
    src = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.005")]
    floats = series_decimal_to_float(src)
    back = series_float_to_decimal(floats, precision=8)
    assert back == src


def test_json_number_boundary():
    val = Decimal("0.04500000")
    assert json_number(val) == pytest.approx(0.045)


def test_decimal_to_float_rejects_non_decimal():
    with pytest.raises(AnalyticsConversionError):
        decimal_to_float(1.23)  # type: ignore[arg-type]