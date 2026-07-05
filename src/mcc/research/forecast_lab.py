"""ForecastLab — model candidates with P3 honest-forecasting discipline (Phase 17).

Extends ResearchLab with Isolation Forest (anomaly), PCA (preprocessing), and Random Forest
(forecast). Isolation Forest and PCA use adapted honesty disciplines from Phase 17 Section 3;
Random Forest uses the standard P3 baseline-beating gate.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Final, Literal, Sequence

import numpy as np
import pandas as pd
import structlog
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest, RandomForestRegressor

from mcc.analytics.validation import validate_return_series

logger = structlog.get_logger(__name__)

SignalVerdict = Literal["SIGNAL", "NO_SIGNAL"]

FIXTURE_FORECAST_SEED: Final[int] = 17
FIXTURE_FORECAST_N: Final[int] = 200
DEFAULT_VIF_RECOMMENDATION: Final[str] = "Consider PCA orthogonalization (forecast_lab.run_pca_factors)"

ModelType = Literal["isolation_forest", "pca", "random_forest", "naive_persistence"]


@dataclass
class ForecastResult:
    """Outcome of a ForecastLab candidate evaluation."""

    model_id: str
    model_type: ModelType
    verdict: SignalVerdict
    metric: float
    baseline_metric: float
    diagnostics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_type": self.model_type,
            "verdict": self.verdict,
            "metric": self.metric,
            "baseline_metric": self.baseline_metric,
            "diagnostics": self.diagnostics,
            "warnings": list(self.warnings),
        }


@dataclass
class PCAResult:
    """PCA preprocessing output — always carries explained-variance disclosure."""

    model_id: str
    components: pd.DataFrame
    explained_variance_ratio: dict[str, float]
    cumulative_explained_variance: dict[str, float]
    n_components: int
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_type": "pca",
            "n_components": self.n_components,
            "explained_variance_ratio": self.explained_variance_ratio,
            "cumulative_explained_variance": self.cumulative_explained_variance,
            "diagnostics": self.diagnostics,
        }


def _new_model_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def naive_persistence_mse(y_true: np.ndarray, y_history: np.ndarray) -> float:
    """Naive baseline: predict each point with the previous observation."""
    if len(y_true) < 2:
        return float("inf")
    preds = y_history[:-1]
    actual = y_true[1:]
    n = min(len(preds), len(actual))
    if n == 0:
        return float("inf")
    return float(np.mean((actual[:n] - preds[:n]) ** 2))


def evaluate_p3_gate(model_mse: float, baseline_mse: float) -> SignalVerdict:
    """Standard P3 gate: model must beat naive baseline out-of-sample."""
    if not np.isfinite(model_mse) or not np.isfinite(baseline_mse):
        return "NO_SIGNAL"
    return "SIGNAL" if model_mse < baseline_mse else "NO_SIGNAL"


def z_score_anomaly_flags(
    features: np.ndarray,
    *,
    threshold: float = 3.0,
) -> np.ndarray:
    """Naive z-score anomaly baseline — any feature exceeding threshold on any axis."""
    if features.ndim == 1:
        features = features.reshape(-1, 1)
    z = np.abs((features - np.nanmean(features, axis=0)) / (np.nanstd(features, axis=0) + 1e-12))
    return (np.nanmax(z, axis=1) > threshold).astype(int)


def _confirmed_hit_rate(flags: np.ndarray, confirmed: np.ndarray) -> float:
    """Fraction of confirmed issues that were flagged (recall on positives)."""
    confirmed = confirmed.astype(int).flatten()
    flags = flags.astype(int).flatten()
    n = min(len(flags), len(confirmed))
    if n == 0:
        return 0.0
    flags = flags[:n]
    confirmed = confirmed[:n]
    positives = int(confirmed.sum())
    if positives == 0:
        return 0.0
    hits = int(((flags == 1) & (confirmed == 1)).sum())
    return hits / positives


def run_isolation_forest(
    features: pd.DataFrame,
    confirmed_issues: pd.Series | np.ndarray,
    *,
    contamination: float = 0.05,
    random_state: int = FIXTURE_FORECAST_SEED,
    z_threshold: float = 3.0,
    model_id: str | None = None,
) -> ForecastResult:
    """Anomaly detection with adapted honesty discipline (Phase 17 Section 3).

    Verdict is SIGNAL only when Isolation Forest recall on confirmed issues exceeds the
    naive z-score threshold baseline on the same data. Otherwise NO_SIGNAL — not surfaced
    downstream.
    """
    x = features.astype(float).values
    confirmed = np.asarray(confirmed_issues, dtype=int).flatten()
    n = min(len(x), len(confirmed))
    x = x[:n]
    confirmed = confirmed[:n]

    if n < 20:
        return ForecastResult(
            model_id=model_id or _new_model_id("iforest"),
            model_type="isolation_forest",
            verdict="NO_SIGNAL",
            metric=0.0,
            baseline_metric=0.0,
            warnings=["insufficient observations for Isolation Forest"],
        )

    iso = IsolationForest(contamination=contamination, random_state=random_state)
    iso.fit(x)
    raw = iso.predict(x)
    if_flags = (raw == -1).astype(int)

    z_flags = z_score_anomaly_flags(x, threshold=z_threshold)
    if_hit = _confirmed_hit_rate(if_flags, confirmed)
    z_hit = _confirmed_hit_rate(z_flags, confirmed)

    verdict: SignalVerdict = "SIGNAL" if if_hit > z_hit else "NO_SIGNAL"
    logger.info(
        "isolation_forest_evaluated",
        if_hit_rate=if_hit,
        z_baseline_hit_rate=z_hit,
        verdict=verdict,
        n_flagged=int(if_flags.sum()),
    )

    return ForecastResult(
        model_id=model_id or _new_model_id("iforest"),
        model_type="isolation_forest",
        verdict=verdict,
        metric=if_hit,
        baseline_metric=z_hit,
        diagnostics={
            "n_obs": n,
            "n_flagged": int(if_flags.sum()),
            "z_threshold": z_threshold,
            "contamination": contamination,
            "if_recall_on_confirmed": if_hit,
            "zscore_baseline_recall": z_hit,
            "adapted_discipline": "anomaly_recall_vs_zscore_baseline",
        },
    )


def run_pca_factors(
    factors: pd.DataFrame,
    *,
    n_components: int | None = None,
    random_state: int = FIXTURE_FORECAST_SEED,
    model_id: str | None = None,
) -> PCAResult:
    """PCA dimensionality reduction with mandatory explained-variance disclosure.

    Preprocessing only — not subject to P3 forecast gate. Every output includes per-component
    and cumulative explained-variance ratios.
    """
    x = factors.astype(float).dropna()
    if x.empty or x.shape[0] < 5:
        raise ValueError("pca: need at least 5 rows after dropna")

    n_comp = n_components or min(x.shape[1], x.shape[0] - 1)
    n_comp = max(1, min(n_comp, x.shape[1]))

    pca = PCA(n_components=n_comp, random_state=random_state)
    transformed = pca.fit_transform(x.values)
    col_names = [f"PC{i + 1}" for i in range(n_comp)]
    components = pd.DataFrame(transformed, index=x.index, columns=col_names)

    evr = {col_names[i]: float(pca.explained_variance_ratio_[i]) for i in range(n_comp)}
    cum = np.cumsum(pca.explained_variance_ratio_)
    cum_evr = {col_names[i]: float(cum[i]) for i in range(n_comp)}

    return PCAResult(
        model_id=model_id or _new_model_id("pca"),
        components=components,
        explained_variance_ratio=evr,
        cumulative_explained_variance=cum_evr,
        n_components=n_comp,
        diagnostics={
            "input_columns": list(x.columns),
            "total_variance_explained": float(cum[-1]) if len(cum) else 0.0,
            "vif_remedy_note": DEFAULT_VIF_RECOMMENDATION,
        },
    )


def run_random_forest(
    features: pd.DataFrame,
    target: pd.Series,
    *,
    train_size: int | None = None,
    n_estimators: int = 100,
    random_state: int = FIXTURE_FORECAST_SEED,
    model_id: str | None = None,
) -> ForecastResult:
    """Random Forest forecast candidate — standard P3 baseline-beating gate."""
    aligned = pd.concat([features, target.rename("target")], axis=1).dropna()
    if len(aligned) < 30:
        return ForecastResult(
            model_id=model_id or _new_model_id("rf"),
            model_type="random_forest",
            verdict="NO_SIGNAL",
            metric=float("inf"),
            baseline_metric=float("inf"),
            warnings=["insufficient aligned observations"],
        )

    y = aligned["target"].values.astype(float)
    x = aligned.drop(columns=["target"]).values.astype(float)
    split = train_size or int(len(aligned) * 0.7)
    split = max(20, min(split, len(aligned) - 10))

    x_train, x_test = x[:split], x[split:]
    y_train, y_test = y[:split], y[split:]

    rf = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
    rf.fit(x_train, y_train)
    preds = rf.predict(x_test)
    model_mse = float(np.mean((y_test - preds) ** 2))
    naive_preds = np.empty_like(y_test)
    naive_preds[0] = y_train[-1]
    if len(y_test) > 1:
        naive_preds[1:] = y_test[:-1]
    baseline_mse = float(np.mean((y_test - naive_preds) ** 2))

    verdict = evaluate_p3_gate(model_mse, baseline_mse)
    logger.info("random_forest_evaluated", model_mse=model_mse, baseline_mse=baseline_mse, verdict=verdict)

    return ForecastResult(
        model_id=model_id or _new_model_id("rf"),
        model_type="random_forest",
        verdict=verdict,
        metric=model_mse,
        baseline_metric=baseline_mse,
        diagnostics={
            "n_train": split,
            "n_test": len(y_test),
            "n_estimators": n_estimators,
            "p3_gate": "mse_vs_naive_persistence",
            "beats_baseline": verdict == "SIGNAL",
        },
    )


def fixture_forecast_panel(
    seed: int = FIXTURE_FORECAST_SEED,
    n: int = FIXTURE_FORECAST_N,
) -> tuple[pd.DataFrame, pd.Series, np.ndarray]:
    """Deterministic panel for tests — labeled FIXTURE, not production."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-02 09:30", periods=n, freq="1min", tz="UTC")
    f1 = rng.normal(0, 1, n)
    f2 = 0.85 * f1 + rng.normal(0, 0.3, n)
    f3 = rng.normal(0, 1, n)
    features = pd.DataFrame({"mkt": f1, "rates": f2, "vol": f3}, index=idx)

    target = pd.Series(0.3 * f1 + 0.1 * f3 + rng.normal(0, 0.05, n), index=idx, name="fwd_ret")
    target = validate_return_series(target, name="fixture_target")

    confirmed = np.zeros(n, dtype=int)
    anomaly_idx = [40, 41, 90, 91, 150]
    for i in anomaly_idx:
        if i < n:
            features.iloc[i] *= 4.0
            confirmed[i] = 1

    return features, target, confirmed


def list_model_candidates() -> list[str]:
    """Registered ForecastLab candidates."""
    return ["isolation_forest", "pca", "random_forest"]