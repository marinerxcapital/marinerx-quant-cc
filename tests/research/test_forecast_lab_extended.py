"""Phase 17 — ForecastLab extended candidates."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mcc.research.forecast_lab import (
    evaluate_p3_gate,
    fixture_forecast_panel,
    run_isolation_forest,
    run_pca_factors,
    run_random_forest,
    z_score_anomaly_flags,
)


def test_isolation_forest_beats_zscore_baseline_on_fixture():
    features, _, confirmed = fixture_forecast_panel()
    result = run_isolation_forest(features, confirmed, contamination=0.05)
    assert result.model_type == "isolation_forest"
    assert result.diagnostics["adapted_discipline"] == "anomaly_recall_vs_zscore_baseline"
    assert result.metric >= result.baseline_metric
    if result.metric > result.baseline_metric:
        assert result.verdict == "SIGNAL"
    else:
        assert result.verdict == "NO_SIGNAL"


def test_isolation_forest_no_signal_when_baseline_wins():
    rng = np.random.default_rng(99)
    n = 120
    x = pd.DataFrame({"a": rng.normal(0, 1, n), "b": rng.normal(0, 1, n)})
    confirmed = np.zeros(n, dtype=int)
    result = run_isolation_forest(x, confirmed, contamination=0.1)
    assert result.verdict == "NO_SIGNAL"


def test_pca_always_discloses_explained_variance():
    features, _, _ = fixture_forecast_panel(n=80)
    pca = run_pca_factors(features[["mkt", "rates", "vol"]], n_components=2)
    assert pca.explained_variance_ratio
    assert pca.cumulative_explained_variance
    assert sum(pca.explained_variance_ratio.values()) == pytest.approx(
        pca.diagnostics["total_variance_explained"], rel=1e-6
    )
    d = pca.to_dict()
    assert "explained_variance_ratio" in d
    assert all(v > 0 for v in d["explained_variance_ratio"].values())


def test_random_forest_p3_gate():
    features, target, _ = fixture_forecast_panel(n=250)
    result = run_random_forest(features, target, train_size=180)
    assert result.model_type == "random_forest"
    assert result.verdict in ("SIGNAL", "NO_SIGNAL")
    expected = evaluate_p3_gate(result.metric, result.baseline_metric)
    assert result.verdict == expected
    assert result.diagnostics["p3_gate"] == "mse_vs_naive_persistence"


def test_z_score_baseline_flags_extreme_rows():
    rng = np.random.default_rng(5)
    normal = rng.normal(0, 0.1, size=(30, 2))
    extreme = np.array([[10.0, 10.0]])
    x = np.vstack([normal, extreme])
    flags = z_score_anomaly_flags(x, threshold=2.0)
    assert flags[-1] == 1