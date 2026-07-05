"""Tests for risk/riskfolio_adapter.py."""
from __future__ import annotations

from datetime import timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mcc.core.exceptions import AnalyticsValidationError
from mcc.risk.riskfolio_adapter import (
    _RISKFOLIO_AVAILABLE,
    kelly_raw_fraction,
    optimize_portfolio,
    riskfolio_var_es,
)
from mcc.risk.sizing import kelly_size
from decimal import Decimal


def _fixture_returns(n: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    idx = pd.date_range("2024-01-02", periods=n, freq="B", tz=timezone.utc)
    return pd.DataFrame(
        {
            "NQ": rng.normal(0.0005, 0.01, n),
            "ES": rng.normal(0.0003, 0.008, n),
            "CL": rng.normal(0.0001, 0.015, n),
            "GC": rng.normal(0.0002, 0.007, n),
        },
        index=idx,
    )


@pytest.mark.skipif(not _RISKFOLIO_AVAILABLE, reason="riskfolio-lib not installed")
def test_optimize_portfolio_weights_sum_to_one(tmp_path: Path):
    result = optimize_portfolio(
        _fixture_returns(),
        method="mean_risk",
        account_id="test_acct",
        output_dir=tmp_path,
    )
    total = sum(float(w) for w in result.weights.values())
    assert abs(total - 1.0) < 0.05
    assert list(tmp_path.glob("*.json"))


@pytest.mark.skipif(not _RISKFOLIO_AVAILABLE, reason="riskfolio-lib not installed")
@pytest.mark.parametrize("method", ["mean_risk", "risk_parity", "hrp", "kelly"])
def test_all_allocation_modes(method: str, tmp_path: Path):
    result = optimize_portfolio(
        _fixture_returns(),
        method=method,  # type: ignore[arg-type]
        output_dir=tmp_path,
        export_json=True,
    )
    assert result.method == method
    assert len(result.weights) >= 1


@pytest.mark.skipif(not _RISKFOLIO_AVAILABLE, reason="riskfolio-lib not installed")
def test_riskfolio_var_es():
    rets = [-0.01, -0.02, 0.005, -0.015, 0.01, -0.008, -0.003, 0.002]
    var, es = riskfolio_var_es(rets, confidence=0.95)
    assert var >= 0
    assert es >= var


def test_kelly_raw_fraction_analytical_fallback():
    frac, reason = kelly_raw_fraction(Decimal("0.6"), Decimal("1.5"))
    assert frac >= Decimal(0)
    assert "kelly" in reason.lower()


def test_kelly_size_preserves_public_signature():
    contracts, reason = kelly_size(Decimal("100000"), Decimal("0.55"), Decimal("1.5"))
    assert isinstance(contracts, int)
    assert isinstance(reason, str)
    assert contracts >= 0


def test_optimize_rejects_empty_returns():
    with pytest.raises(AnalyticsValidationError):
        optimize_portfolio(pd.DataFrame())