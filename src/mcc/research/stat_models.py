"""Extended statistical models for ResearchLab (Phase 07 + Phase 16).

Exports :class:`StatisticalModelResult` matching Section 8.3 schema.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Final, Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller

from mcc.analytics.conversion import json_number
from mcc.analytics.validation import validate_price_series, validate_return_series

# FIXTURE — tests only
FIXTURE_OLS_SEED: Final[int] = 7
FIXTURE_OLS_N: Final[int] = 200


@dataclass
class StatisticalModelResult:
    """Section 8.3 Statistical Model Result."""

    model_id: str
    model_type: str
    dependent_variable: str
    independent_variables: list[str]
    coefficients: dict[str, float] = field(default_factory=dict)
    p_values: dict[str, float] = field(default_factory=dict)
    r_squared: float | None = None
    adjusted_r_squared: float | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export / dashboard consumption."""
        return result_to_dict(self)


def result_to_dict(result: StatisticalModelResult) -> dict[str, Any]:
    """Convert :class:`StatisticalModelResult` to Section 8.3 JSON-compatible dict."""
    return {
        "model_id": result.model_id,
        "model_type": result.model_type,
        "dependent_variable": result.dependent_variable,
        "independent_variables": list(result.independent_variables),
        "coefficients": {k: json_number(Decimal(str(v))) for k, v in result.coefficients.items()},
        "p_values": {k: json_number(Decimal(str(v))) for k, v in result.p_values.items()},
        "r_squared": (
            json_number(Decimal(str(result.r_squared))) if result.r_squared is not None else None
        ),
        "adjusted_r_squared": (
            json_number(Decimal(str(result.adjusted_r_squared)))
            if result.adjusted_r_squared is not None
            else None
        ),
        "diagnostics": result.diagnostics,
        "warnings": list(result.warnings),
    }


def _new_model_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _returns_from_series(series: pd.Series) -> pd.Series:
    validated = validate_price_series(series, name="stat_input")
    ret = np.log(validated.astype(float)).diff().dropna()
    return validate_return_series(ret, name="stat_returns")


def ols_factor_exposure(
    dependent: pd.Series,
    factors: pd.DataFrame,
    *,
    model_id: str | None = None,
    add_constant: bool = True,
) -> StatisticalModelResult:
    """OLS regression of instrument returns against a factor set.

    Parameters
    ----------
    dependent:
        Price or return series for the instrument (prices are log-differenced).
    factors:
        DataFrame of aligned factor columns (e.g. broad market, rates proxy).
    """
    y = _returns_from_series(dependent)
    x_raw = factors.copy()
    if not isinstance(x_raw.index, pd.DatetimeIndex):
        raise ValueError("factors: index must be DatetimeIndex")
    x_aligned = x_raw.reindex(y.index).dropna(how="any")
    y_aligned = y.reindex(x_aligned.index)

    if len(y_aligned) < 10:
        return StatisticalModelResult(
            model_id=model_id or _new_model_id("ols"),
            model_type="OLS",
            dependent_variable=str(dependent.name or "dependent"),
            independent_variables=list(x_aligned.columns),
            warnings=["insufficient overlapping observations after alignment"],
        )

    x_vals = x_aligned.astype(float)
    if add_constant:
        x_design = sm.add_constant(x_vals, has_constant="add")
    else:
        x_design = x_vals

    fit = sm.OLS(y_aligned, x_design).fit()

    coef_names = [str(name) for name in fit.params.index]
    coefficients = {name: float(fit.params[name]) for name in coef_names}
    p_values = {name: float(fit.pvalues[name]) for name in coef_names}

    return StatisticalModelResult(
        model_id=model_id or _new_model_id("ols"),
        model_type="OLS",
        dependent_variable=str(dependent.name or "dependent"),
        independent_variables=[c for c in coef_names if c != "const"],
        coefficients=coefficients,
        p_values=p_values,
        r_squared=float(fit.rsquared),
        adjusted_r_squared=float(fit.rsquared_adj),
        diagnostics={
            "n_obs": int(fit.nobs),
            "f_statistic": float(fit.fvalue) if fit.fvalue is not None else None,
            "f_pvalue": float(fit.f_pvalue) if fit.f_pvalue is not None else None,
            "aic": float(fit.aic),
            "bic": float(fit.bic),
        },
    )


def adf_stationarity(
    series: pd.Series,
    *,
    model_id: str | None = None,
    regression: str = "c",
    maxlag: int | None = None,
) -> StatisticalModelResult:
    """Augmented Dickey-Fuller stationarity test (extends Phase 07 cointegration suite)."""
    if series.name and str(series.name).endswith("_returns"):
        validated = validate_return_series(series, name="adf_series")
        y = validated.values.astype(float)
        dep_name = str(series.name)
    else:
        validated = validate_price_series(series, name="adf_series")
        y = validated.values.astype(float)
        dep_name = str(validated.name or "price")

    warnings_list: list[str] = []
    try:
        adf_stat, p_value, used_lag, nobs, crit, icbest = adfuller(
            y, regression=regression, maxlag=maxlag, autolag="AIC"
        )
    except Exception as exc:
        return StatisticalModelResult(
            model_id=model_id or _new_model_id("adf"),
            model_type="ADF",
            dependent_variable=dep_name,
            independent_variables=[],
            warnings=[f"ADF failed: {exc}"],
        )

    return StatisticalModelResult(
        model_id=model_id or _new_model_id("adf"),
        model_type="ADF",
        dependent_variable=dep_name,
        independent_variables=[],
        coefficients={"adf_statistic": float(adf_stat)},
        p_values={"adf_pvalue": float(p_value)},
        r_squared=None,
        adjusted_r_squared=None,
        diagnostics={
            "used_lag": int(used_lag),
            "nobs": int(nobs),
            "critical_values": {k: float(v) for k, v in crit.items()},
            "icbest": float(icbest) if icbest is not None else None,
            "is_stationary_5pct": bool(p_value < 0.05),
            "regression": regression,
        },
        warnings=warnings_list,
    )


def ljung_box_autocorr(
    residuals: pd.Series,
    *,
    model_id: str | None = None,
    lags: int | Sequence[int] = 10,
) -> StatisticalModelResult:
    """Ljung-Box test for residual autocorrelation."""
    validated = validate_return_series(residuals, name="ljungbox_residuals")
    y = validated.values.astype(float)

    lag_list = list(range(1, lags + 1)) if isinstance(lags, int) else list(lags)
    lb = acorr_ljungbox(y, lags=lag_list, return_df=True)
    last = lb.iloc[-1]

    lag_label = str(lb.index[-1])
    return StatisticalModelResult(
        model_id=model_id or _new_model_id("ljungbox"),
        model_type="LjungBox",
        dependent_variable=str(validated.name or "residuals"),
        independent_variables=[f"lag_{lag_label}"],
        coefficients={"lb_statistic": float(last["lb_stat"])},
        p_values={"lb_pvalue": float(last["lb_pvalue"])},
        r_squared=None,
        adjusted_r_squared=None,
        diagnostics={
            "lags_tested": list(lb.index.astype(int)),
            "all_results": lb.reset_index().rename(columns={"index": "lag"}).to_dict(orient="records"),
            "no_autocorr_5pct": bool(float(last["lb_pvalue"]) > 0.05),
        },
    )


def ttest_wrapper(
    sample_a: Sequence[float] | pd.Series,
    sample_b: Sequence[float] | pd.Series | None = None,
    *,
    model_id: str | None = None,
    paired: bool = False,
    alternative: str = "two-sided",
    name_a: str = "sample_a",
    name_b: str = "sample_b",
) -> StatisticalModelResult:
    """Generic t-test wrapper for ResearchLab forecast evaluation."""
    a = np.asarray(sample_a, dtype=float)
    a = a[~np.isnan(a)]
    if len(a) < 2:
        return StatisticalModelResult(
            model_id=model_id or _new_model_id("ttest"),
            model_type="ttest",
            dependent_variable=name_a,
            independent_variables=[name_b] if sample_b is not None else [],
            warnings=["sample_a has fewer than 2 non-NaN observations"],
        )

    if sample_b is None:
        stat, pval = stats.ttest_1samp(a, popmean=0.0, alternative=alternative)
        indep: list[str] = []
        coef = {"mean": float(np.mean(a)), "t_statistic": float(stat)}
    else:
        b = np.asarray(sample_b, dtype=float)
        b = b[~np.isnan(b)]
        min_len = min(len(a), len(b))
        if paired:
            stat, pval = stats.ttest_rel(a[:min_len], b[:min_len], alternative=alternative)
        else:
            stat, pval = stats.ttest_ind(a, b, equal_var=False, alternative=alternative)
        indep = [name_b]
        coef = {
            f"{name_a}_mean": float(np.mean(a)),
            f"{name_b}_mean": float(np.mean(b)),
            "mean_diff": float(np.mean(a[:min_len]) - np.mean(b[:min_len])),
            "t_statistic": float(stat),
        }

    return StatisticalModelResult(
        model_id=model_id or _new_model_id("ttest"),
        model_type="ttest",
        dependent_variable=name_a,
        independent_variables=indep,
        coefficients=coef,
        p_values={"t_pvalue": float(pval)},
        r_squared=None,
        adjusted_r_squared=None,
        diagnostics={
            "n_a": int(len(a)),
            "n_b": int(len(sample_b)) if sample_b is not None else 0,
            "paired": paired,
            "alternative": alternative,
            "significant_5pct": bool(pval < 0.05),
        },
    )


def fixture_factor_panel(seed: int = FIXTURE_OLS_SEED, n: int = FIXTURE_OLS_N) -> tuple[pd.Series, pd.DataFrame]:
    """Synthetic factor panel for tests — labeled FIXTURE, not production."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-02 09:30", periods=n, freq="1min", tz="UTC")
    market = pd.Series(rng.normal(0.0001, 0.002, n), index=idx, name="market_proxy")
    rates = pd.Series(rng.normal(0.0, 0.0005, n), index=idx, name="rates_proxy")
    noise = rng.normal(0, 0.001, n)
    dependent_prices = 100.0 * np.exp(
        np.cumsum(0.6 * market.values + 0.3 * rates.values + noise)
    )
    dep = pd.Series(dependent_prices, index=idx, name="NQ_fixture")
    factors = pd.DataFrame({"market_proxy": market, "rates_proxy": rates})
    return dep, factors