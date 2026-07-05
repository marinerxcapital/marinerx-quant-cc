# Phase 17 Implementation Guide

## Pre-inspection (Step 1)

Phase 16 `stat_models.py` already contained OLS, ADF, Ljung-Box, and t-tests. Phase 17 **extends** OLS with VIF/F-test/economic split — no duplication.

`forecast_lab.py` did not exist; created per master brief tree with three new candidates.

## Runnable examples

### Isolation Forest (adapted discipline)

```bash
python -c "
from mcc.research.forecast_lab import fixture_forecast_panel, run_isolation_forest
f, _, c = fixture_forecast_panel()
r = run_isolation_forest(f, c)
print(r.verdict, r.metric, 'vs', r.baseline_metric)
"
```

### PCA (variance disclosure)

```bash
python -c "
from mcc.research.forecast_lab import fixture_forecast_panel, run_pca_factors
f, _, _ = fixture_forecast_panel(n=80)
p = run_pca_factors(f[['mkt','rates','vol']], n_components=2)
print(p.explained_variance_ratio)
"
```

### Random Forest (standard P3)

```bash
python -c "
from mcc.research.forecast_lab import fixture_forecast_panel, run_random_forest
f, t, _ = fixture_forecast_panel(n=250)
r = run_random_forest(f, t)
print(r.verdict, 'mse', r.metric, 'baseline', r.baseline_metric)
"
```

### OLS rigor (VIF + F-test + significance split)

```bash
python -c "
from mcc.research.stat_models import fixture_factor_panel, ols_factor_exposure
dep, factors = fixture_factor_panel()
r = ols_factor_exposure(dep, factors, instrument='NQ')
print('VIF flagged:', r.diagnostics['vif_flagged'])
print('Joint F sig:', r.diagnostics['joint_f_significant'])
print('Coeffs:', r.diagnostics['coefficient_significance'])
"
```

### Seaborn report chart

```bash
python -c "
import pandas as pd
from mcc.reports.generator import generate_line_chart
generate_line_chart(pd.Series([1,2,3,2,4]), title='Weekly PnL', output_path='reports_out/diagnostics/phase17_chart.png')
"
```

## Known limitations

- hmmlearn/RL/CNN excluded per work order Section 1
- openpyxl export is optional (`reports/generator.export_trades_to_excel`)
- scikit-learn was in master brief stack; pinned in `pyproject.toml` during Phase 17