# Phase 17 Testing Guide

## Full regression gate (Phases 01–16 + 17)

```bash
cd C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc
python -m pytest tests/ -v --tb=short 2>&1 | tee pytest_phase17_full.txt
```

## Phase 17 test modules

| File | Covers |
|---|---|
| `tests/research/test_forecast_lab_extended.py` | IF baseline gate, PCA variance, RF P3 |
| `tests/research/test_stat_models_rigor.py` | VIF, joint F, significance split |
| `tests/reports/test_generator_styling.py` | Seaborn style + PNG output |

## Expected

All prior Phase 16 tests remain green. Phase 17 adds 12 new tests (60 total).

## Evidence regeneration

```bash
python -c "
import json
from pathlib import Path
from mcc.research.forecast_lab import fixture_forecast_panel, run_isolation_forest, run_pca_factors, run_random_forest
from mcc.research.stat_models import fixture_factor_panel, ols_factor_exposure
from mcc.reports.generator import generate_line_chart
import pandas as pd

f, t, c = fixture_forecast_panel()
evidence = {
  'isolation_forest': run_isolation_forest(f, c).to_dict(),
  'pca': run_pca_factors(f[['mkt','rates','vol']], n_components=2).to_dict(),
  'random_forest': run_random_forest(f, t).to_dict(),
  'ols_rigor': ols_factor_exposure(*fixture_factor_panel(), instrument='NQ').to_dict(),
}
out = Path('reports_out/diagnostics/phase17_evidence.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(evidence, indent=2, default=str))
generate_line_chart(pd.Series([1,2,3,2,4]), output_path='reports_out/diagnostics/phase17_chart.png')
print(out, 'chart written')
"
```