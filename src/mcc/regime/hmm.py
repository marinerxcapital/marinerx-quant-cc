"""Markov-switching regime classification via statsmodels (Phase 16).

Replaces the prior hmmlearn GaussianHMM concept with ``MarkovRegression`` while
preserving the ``RegimeEvent`` contract (state label + confidence).
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Final, TypedDict

import numpy as np
import pandas as pd
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

from mcc.analytics.conversion import json_number
from mcc.analytics.validation import validate_price_series, utc_now
from mcc.core.events import RegimeEvent
from mcc.core.exceptions import AnalyticsValidationError

# ---------------------------------------------------------------------------
# FIXTURE constants — tests / documentation comparison only, not production data
# ---------------------------------------------------------------------------
FIXTURE_HMM_SYMBOL: Final[str] = "NQ_FIXTURE"
FIXTURE_HMM_SEED: Final[int] = 42
FIXTURE_HMM_N_OBS: Final[int] = 240

_STATE_TRENDING: Final[str] = "trending"
_STATE_MEAN_REVERTING: Final[str] = "mean-reverting"


class RegimeClassification(TypedDict):
    """Output of :func:`classify_regime` — RegimeEvent-compatible fields plus diagnostics."""

    state: str
    confidence: float
    model_type: str
    regime_probabilities: dict[str, float]
    diagnostics: dict[str, Any]


def _fixture_two_regime_prices(n: int = FIXTURE_HMM_N_OBS, seed: int = FIXTURE_HMM_SEED) -> pd.Series:
    """Synthetic two-regime price path for tests and hmmlearn comparison docs."""
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2024-01-02 09:30", tz="UTC")
    idx = pd.date_range(start, periods=n, freq="1min")
    returns = np.empty(n, dtype=float)
    mid = n // 2
    returns[:mid] = rng.normal(0.0004, 0.0012, mid)  # trending segment
    returns[mid:] = rng.normal(0.0, 0.0004, n - mid)  # mean-reverting segment
    prices = 100.0 * np.exp(np.cumsum(returns))
    return pd.Series(prices, index=idx, name="close")


def _returns_from_prices(prices: pd.Series) -> pd.Series:
    """Log-return series derived from validated prices."""
    validated = validate_price_series(prices, name="regime_prices")
    log_prices = np.log(validated.astype(float))
    returns = log_prices.diff().dropna()
    if len(returns) < 30:
        raise AnalyticsValidationError(
            "regime_prices: need at least 31 observations for MarkovRegression fit",
            {"n_returns": len(returns)},
        )
    return returns


def _param_dict(result: Any) -> dict[str, float]:
    """Named parameter map from a statsmodels fit result."""
    names = list(getattr(result.model, "param_names", []))
    if not names:
        return {}
    return {name: float(val) for name, val in zip(names, result.params, strict=False)}


def _label_regimes(result: Any, n_regimes: int) -> dict[int, str]:
    """Map regime indices to human labels using fitted switching variances."""
    params = _param_dict(result)
    variances: list[tuple[int, float]] = []
    for i in range(n_regimes):
        key = f"sigma2[{i}]"
        sigma = float(params.get(key, 1.0))
        variances.append((i, sigma))
    variances.sort(key=lambda x: x[1], reverse=True)
    labels: dict[int, str] = {}
    labels[variances[0][0]] = _STATE_TRENDING
    for idx, _ in variances[1:]:
        labels[idx] = _STATE_MEAN_REVERTING
    return labels


def classify_regime(
    prices: pd.Series,
    *,
    n_regimes: int = 2,
    switching_variance: bool = True,
) -> RegimeClassification:
    """Classify the latest observation into a Markov-switching regime.

    Parameters
    ----------
    prices:
        Point-in-time close (or mid) prices indexed by tz-aware UTC timestamps.
    n_regimes:
        Number of latent regimes (default 2: trending vs mean-reverting).
    switching_variance:
        Allow regime-dependent variance in the Markov regression.

    Returns
    -------
    dict
        ``state`` and ``confidence`` match the ``RegimeEvent`` payload contract.
        Additional diagnostics are included for research / comparison exports.
    """
    returns = _returns_from_prices(prices)
    y = returns.values.astype(float)

    model = MarkovRegression(
        y,
        k_regimes=n_regimes,
        trend="c",
        switching_variance=switching_variance,
    )
    fit = model.fit(disp=False, maxiter=200, search_reps=10)

    smoothed = fit.smoothed_marginal_probabilities
    if smoothed.ndim == 1:
        last_probs = np.asarray([1.0])
    else:
        last_probs = smoothed[-1]

    regime_labels = _label_regimes(fit, n_regimes)
    prob_by_label: dict[str, float] = {}
    for i in range(n_regimes):
        label = regime_labels.get(i, f"regime_{i}")
        prob_by_label[label] = float(last_probs[i]) if i < len(last_probs) else 0.0

    best_idx = int(np.argmax(last_probs))
    state = regime_labels.get(best_idx, f"regime_{best_idx}")
    confidence = float(np.clip(last_probs[best_idx], 0.0, 1.0))

    param_map = _param_dict(fit)
    return RegimeClassification(
        state=state,
        confidence=confidence,
        model_type="MarkovRegression",
        regime_probabilities=prob_by_label,
        diagnostics={
            "n_obs": int(len(returns)),
            "n_regimes": n_regimes,
            "aic": float(fit.aic),
            "bic": float(fit.bic),
            "regime_variances": {
                regime_labels[i]: float(param_map.get(f"sigma2[{i}]", np.nan))
                for i in range(n_regimes)
            },
            "last_timestamp": str(returns.index[-1]),
        },
    )


def build_regime_event(
    prices: pd.Series,
    *,
    ts_utc: datetime | None = None,
    source: str = "RegimeMonitor",
    symbol: str = "UNKNOWN",
    **extra_payload: Any,
) -> RegimeEvent:
    """Run classification and emit a ``RegimeEvent`` with preserved public shape."""
    result = classify_regime(prices)
    when = ts_utc or utc_now()
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return RegimeEvent(
        when,
        source,
        symbol,
        result["state"],
        result["confidence"],
        model_type=result["model_type"],
        regime_probabilities=result["regime_probabilities"],
        diagnostics=result["diagnostics"],
        **extra_payload,
    )


def _hmmlearn_classify(prices: pd.Series, *, n_regimes: int = 2) -> dict[str, Any]:
    """Optional hmmlearn baseline for documentation comparison (not production)."""
    try:
        from hmmlearn.hmm import GaussianHMM  # type: ignore[import-untyped]
    except ImportError as exc:
        return {
            "available": False,
            "error": f"hmmlearn not installed: {exc}",
        }

    returns = _returns_from_prices(prices)
    features = returns.values.reshape(-1, 1)
    hmm = GaussianHMM(n_components=n_regimes, covariance_type="full", n_iter=200, random_state=FIXTURE_HMM_SEED)
    hmm.fit(features)
    posteriors = hmm.predict_proba(features)
    last = posteriors[-1]
    # Label by component variance (higher -> trending)
    vars_: list[tuple[int, float]] = []
    for i in range(n_regimes):
        cov = hmm.covars_[i]
        var = float(cov[0, 0]) if cov.ndim == 2 else float(cov[0])
        vars_.append((i, var))
    vars_.sort(key=lambda x: x[1], reverse=True)
    label_map = {vars_[0][0]: _STATE_TRENDING}
    for idx, _ in vars_[1:]:
        label_map[idx] = _STATE_MEAN_REVERTING
    best = int(np.argmax(last))
    return {
        "available": True,
        "engine": "hmmlearn.GaussianHMM",
        "state": label_map.get(best, f"regime_{best}"),
        "confidence": float(np.clip(last[best], 0.0, 1.0)),
        "regime_probabilities": {
            label_map.get(i, f"regime_{i}"): float(last[i]) for i in range(n_regimes)
        },
        "n_obs": len(returns),
    }


def hmmlearn_baseline_compare(
    prices: pd.Series | None = None,
    *,
    n_regimes: int = 2,
) -> dict[str, Any]:
    """Side-by-side statsmodels vs hmmlearn output on a shared fixture.

    Intended for test evidence and ``docs/phase_16`` comparison notes.  Engines may
    legitimately disagree slightly — this function documents both outputs rather
    than asserting equality.
    """
    series = prices if prices is not None else _fixture_two_regime_prices()
    statsmodels_out = classify_regime(series, n_regimes=n_regimes)
    hmmlearn_out = _hmmlearn_classify(series, n_regimes=n_regimes)

    agreement = None
    if hmmlearn_out.get("available"):
        agreement = statsmodels_out["state"] == hmmlearn_out["state"]

    return {
        "fixture": {
            "symbol": FIXTURE_HMM_SYMBOL,
            "n_obs": int(len(series)),
            "source": "synthetic" if prices is None else "caller_supplied",
            "seed": FIXTURE_HMM_SEED if prices is None else None,
        },
        "statsmodels": {
            "engine": "MarkovRegression",
            "state": statsmodels_out["state"],
            "confidence": json_number(Decimal(str(statsmodels_out["confidence"]))),
            "regime_probabilities": statsmodels_out["regime_probabilities"],
            "diagnostics": statsmodels_out["diagnostics"],
        },
        "hmmlearn": hmmlearn_out,
        "states_agree": agreement,
        "confidence_delta": (
            abs(statsmodels_out["confidence"] - float(hmmlearn_out["confidence"]))
            if hmmlearn_out.get("available")
            else None
        ),
        "note": (
            "Behavioral differences between engines are expected; "
            "RegimeEvent shape (state + confidence) is preserved."
        ),
    }


def load_fixture_prices_from_catalog(symbol: str = "NQ", n: int = FIXTURE_HMM_N_OBS) -> pd.Series:
    """Load catalog bars and return a close-price series for regime fitting."""
    from mcc.data.historical.catalog import load_or_synth_nq_bars

    df = load_or_synth_nq_bars(n=n, symbol=symbol)
    if "ts" not in df.columns or "c" not in df.columns:
        raise AnalyticsValidationError("catalog bars missing ts/c columns", {"columns": list(df.columns)})
    idx = pd.DatetimeIndex(pd.to_datetime(df["ts"], utc=True))
    close = pd.Series(df["c"].astype(float).values, index=idx, name="close")
    return validate_price_series(close, name="catalog_close")