"""Unit tests for analytics/validation.py."""
from __future__ import annotations

from datetime import timezone

import numpy as np
import pandas as pd
import pytest

from mcc.analytics.validation import validate_price_series, validate_return_series, validate_weights
from mcc.core.exceptions import AnalyticsValidationError


def _utc_index(n: int = 10) -> pd.DatetimeIndex:
    return pd.date_range("2024-06-01", periods=n, freq="D", tz=timezone.utc)


def test_validate_price_series_rejects_nan():
    idx = _utc_index(3)
    s = pd.Series([1.0, float("nan"), 3.0], index=idx)
    with pytest.raises(AnalyticsValidationError):
        validate_price_series(s)


def test_validate_price_series_localizes_naive_index():
    idx = pd.date_range("2024-06-01", periods=5, freq="D")
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx)
    out = validate_price_series(s)
    assert out.index.tz is not None


def test_validate_return_series_rejects_non_monotonic():
    idx = _utc_index(3)
    s = pd.Series([0.01, 0.02, 0.0], index=idx[[2, 1, 0]])
    with pytest.raises(AnalyticsValidationError, match="monotonic"):
        validate_return_series(s)


def test_validate_weights_sum_to_one():
    w = validate_weights({"NQ": 0.5, "ES": 0.5})
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_validate_weights_rejects_bad_sum():
    with pytest.raises(AnalyticsValidationError):
        validate_weights({"NQ": 0.3, "ES": 0.3})