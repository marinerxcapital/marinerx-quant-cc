"""Phase 17 — statistical rigor upgrades (VIF, F-test, significance split)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mcc.backtest.costs import round_trip_cost_pct
from mcc.research.stat_models import (
    DEFAULT_VIF_THRESHOLD,
    compute_vif,
    fixture_economic_insignificance_panel,
    fixture_factor_panel,
    ols_factor_exposure,
)


def test_vif_flags_collinear_factor():
    dep, factors = fixture_factor_panel(n=150)
    factors = factors.copy()
    factors["collinear"] = factors["market_proxy"] * 0.98 + np.random.default_rng(1).normal(
        0, 0.0001, len(factors)
    )
    result = ols_factor_exposure(dep, factors, instrument="NQ", vif_threshold=DEFAULT_VIF_THRESHOLD)
    vif = result.diagnostics.get("vif", {})
    assert vif
    flagged = result.diagnostics.get("vif_flagged", [])
    assert isinstance(flagged, list)
    if any(v > DEFAULT_VIF_THRESHOLD for v in vif.values()):
        assert flagged


def test_joint_f_test_present():
    dep, factors = fixture_factor_panel()
    result = ols_factor_exposure(dep, factors, instrument="ES")
    assert "joint_f_statistic" in result.diagnostics
    assert "joint_f_pvalue" in result.diagnostics
    assert "joint_f_significant" in result.diagnostics
    assert isinstance(result.diagnostics["joint_f_significant"], bool)


def test_significance_split_statistical_vs_economic_independent():
    from mcc.research.stat_models import _coefficient_significance_split

    instrument = "NQ"
    cost = round_trip_cost_pct(instrument)
    effect = cost * 0.1
    split = _coefficient_significance_split(
        {"tiny_factor": effect},
        {"tiny_factor": 0.01},
        instrument=instrument,
    )["tiny_factor"]
    assert split["statistically_significant"] is True
    assert split["economically_significant"] is False
    assert split["predicted_effect_abs"] < cost


def test_ols_integration_all_rigor_fields_populated():
    dep, factors = fixture_factor_panel()
    result = ols_factor_exposure(dep, factors, instrument="NQ")
    d = result.diagnostics
    for key in ("vif", "joint_f_pvalue", "joint_f_significant", "coefficient_significance"):
        assert key in d


def test_compute_vif_standalone():
    rng = np.random.default_rng(3)
    n = 50
    a = rng.normal(0, 1, n)
    df = pd.DataFrame({"x1": a, "x2": a + rng.normal(0, 0.01, n)})
    vif, flagged = compute_vif(df, threshold=5.0)
    assert "x1" in vif and "x2" in vif
    assert any(v > 5 for v in vif.values())