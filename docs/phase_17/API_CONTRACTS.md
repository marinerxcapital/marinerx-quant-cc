# Phase 17 API Contracts

## ForecastLab (`forecast_lab.py`)

### `ForecastResult`

| Field | Type | Notes |
|---|---|---|
| `verdict` | `"SIGNAL"` \| `"NO_SIGNAL"` | Downstream gate |
| `metric` | float | Model score (MSE or recall) |
| `baseline_metric` | float | Naive comparison value |
| `diagnostics` | dict | Discipline-specific metadata |

### Adapted disciplines

**Isolation Forest:** `metric` = recall on confirmed issues; `baseline_metric` = z-score baseline recall. `NO_SIGNAL` if baseline wins.

**PCA:** `PCAResult` always includes `explained_variance_ratio` and `cumulative_explained_variance` — no `verdict` field (preprocessing).

**Random Forest:** `metric` = OOS MSE; `baseline_metric` = naive persistence MSE. Standard P3.

## Statistical rigor (`stat_models.py`)

Extended `ols_factor_exposure` diagnostics:

```python
{
  "vif": {"factor_name": float},
  "vif_flagged": ["factor_name", ...],
  "joint_f_statistic": float,
  "joint_f_pvalue": float,
  "joint_f_significant": bool,
  "coefficient_significance": {
    "factor_name": {
      "statistically_significant": bool,
      "economically_significant": bool,  # independent flag
      "predicted_effect_abs": float,
      "round_trip_cost": float,
    }
  }
}
```

**Never merge** statistical and economic significance into one boolean.

## Reports (`generator.py`)

- `apply_report_style()` → Seaborn whitegrid default
- `generate_line_chart(...)` → PNG with active style