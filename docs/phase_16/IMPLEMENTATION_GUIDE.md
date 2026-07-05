# Phase 16 Implementation Guide

## Build order (Section 7 sub-agents)

1. **Quant Architecture** — `analytics/validation.py`, `analytics/conversion.py`, `config/analytics.yaml`
2. **Portfolio Optimization** — `risk/riskfolio_adapter.py` wired into `sizing.py`, `var_es.py`, `portfolio.py`
3. **Performance Analytics** — `performance/quantstats_adapter.py` composed in `analytics.py`
4. **Statistical Modeling** — `regime/hmm.py` statsmodels swap + `research/stat_models.py` extensions
5. **Testing/QA** — full pytest suite under `tests/analytics/`, `tests/risk/`, etc.
6. **Documentation** — this folder

## Decimal ↔ float boundary

All library calls receive `float` data converted via `mcc.analytics.conversion`:

```python
from decimal import Decimal
from mcc.analytics.conversion import decimal_to_float, float_to_decimal

price = Decimal("4521.25")
lib_input = decimal_to_float(price, context="riskfolio")
result = float_to_decimal(lib_output, precision=8, context="riskfolio")
```

**Rule:** No bare `float(decimal_var)` outside `analytics/conversion.py`.

## Runnable examples

### Riskfolio allocation

```bash
python -c "
import pandas as pd, numpy as np
from mcc.risk.portfolio import optimize_allocation
rng = np.random.default_rng(42)
idx = pd.date_range('2024-01-02', periods=120, freq='B', tz='UTC')
rets = pd.DataFrame({s: rng.normal(0.0003, 0.01, 120) for s in ('NQ','ES','CL','GC')}, index=idx)
r = optimize_allocation(rets, method='hrp', account_id='demo')
print(r.weights)
"
```

### QuantStats tearsheet

```bash
python -c "
from mcc.performance.analytics import compose_performance_report
from mcc.performance.quantstats_adapter import fixture_trades
r = compose_performance_report(fixture_trades(), strategy_id='DEMO-001')
print(r['tearsheet_path'])
"
```

### statsmodels regime

```bash
python -c "
from mcc.regime.hmm import classify_regime, _fixture_two_regime_prices
print(classify_regime(_fixture_two_regime_prices()))
"
```

## Configuration

See `config/analytics.yaml` for risk-free rate, default risk measure, regime model, and report paths.

## Known limitations

- Futures-only book: benchmark defaults to flat risk-free rate, labeled `flat_rate_4.5pct`
- Sharpe/Sortino/Calmar are **period-return** metrics (daily), not per-trade
- hmmlearn vs statsmodels regime labels may differ on the same fixture (documented, not asserted equal)