"""Tests for research/stat_models.py Phase 16 extensions."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mcc.research.stat_models import (
    StatisticalModelResult,
    adf_stationarity,
    fixture_factor_panel,
    ljung_box_autocorr,
    ols_factor_exposure,
    result_to_dict,
    ttest_wrapper,
)


def test_ols_factor_exposure_schema():
    dep, factors = fixture_factor_panel()
    result = ols_factor_exposure(dep, factors)
    assert isinstance(result, StatisticalModelResult)
    assert result.model_type == "OLS"
    d = result_to_dict(result)
    assert "coefficients" in d
    assert "p_values" in d
    assert result.r_squared is not None


def test_adf_stationarity_on_returns():
    dep, _ = fixture_factor_panel(n=100)
    ret = np.log(dep.astype(float)).diff().dropna()
    ret.name = "NQ_returns"
    result = adf_stationarity(ret)
    assert result.model_type == "ADF"
    assert "adf_statistic" in result.coefficients
    assert "adf_pvalue" in result.p_values


def test_ljung_box_autocorr():
    rng = np.random.default_rng(1)
    residuals = pd.Series(rng.normal(0, 1, 80), index=pd.date_range("2024-01-01", periods=80, freq="D", tz="UTC"))
    result = ljung_box_autocorr(residuals, lags=5)
    assert result.model_type == "LjungBox"
    assert "lb_statistic" in result.coefficients


def test_ttest_wrapper_two_sample():
    a = [0.01, 0.02, -0.01, 0.03, 0.0]
    b = [-0.01, 0.0, -0.02, 0.01, -0.005]
    result = ttest_wrapper(a, b, name_a="strategy", name_b="baseline")
    assert result.model_type == "ttest"
    assert "t_pvalue" in result.p_values