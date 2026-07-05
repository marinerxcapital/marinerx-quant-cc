# Phase 16 Testing Guide

## Full regression gate

```bash
cd C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc
pip install -e ".[dev]"
pytest tests/ -v --tb=short 2>&1 | tee pytest_phase16_full.txt
```

**Expected:** All Phase 01–15 tests (11) + Phase 16 tests pass.

## Phase 16 test modules

| Path | Covers |
|---|---|
| `tests/analytics/test_conversion.py` | Decimal↔float boundary |
| `tests/analytics/test_validation.py` | NaN rejection, tz index, weights |
| `tests/risk/test_riskfolio_adapter.py` | Allocation modes, Kelly, VaR/ES |
| `tests/performance/test_quantstats_adapter.py` | Tearsheet HTML, Sharpe hand-check |
| `tests/regime/test_hmm_statsmodels.py` | RegimeEvent shape, comparison doc |
| `tests/research/test_stat_models_extended.py` | OLS, ADF, Ljung-Box, t-test |
| `tests/integration/test_phase16_end_to_end.py` | E2E pipelines + contract regression |

## Coverage target

```bash
pytest tests/ --cov=mcc.analytics --cov=mcc.risk.riskfolio_adapter --cov=mcc.performance.quantstats_adapter --cov=mcc.regime.hmm --cov=mcc.research.stat_models --cov-report=term-missing
```

Target: ≥70% on new/modified modules.

## Regenerate regime comparison evidence

```bash
python -c "
import json
from pathlib import Path
from mcc.regime.hmm import hmmlearn_baseline_compare
out = Path('reports_out/diagnostics/regime_old_vs_new_comparison.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(hmmlearn_baseline_compare(), indent=2))
print(out)
"
```

## Decimal boundary grep guard

Included in `tests/integration/test_phase16_end_to_end.py::test_no_decimal_float_cast_outside_boundary`.

## Troubleshooting

| Failure | Fix |
|---|---|
| `riskfolio-lib is not installed` | `pip install riskfolio-lib` |
| QuantStats HTML empty | Check return series has ≥3 observations |
| MarkovRegression convergence | Increase fixture length (`FIXTURE_HMM_N_OBS=240`) |
| Flaky Sharpe comparison | Widen tolerance in `test_quantstats_adapter.py` |