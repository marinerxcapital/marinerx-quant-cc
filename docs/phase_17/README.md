# Phase 17 — Forecast Model Extension + Statistical Rigor

## Purpose

Small, bounded extension of **ResearchLab** and **ReportPublisher**:

| Item | Module | Library |
|---|---|---|
| Isolation Forest (anomaly) | `research/forecast_lab.py` | scikit-learn |
| PCA (factor orthogonalization) | `research/forecast_lab.py` | scikit-learn |
| Random Forest (forecast) | `research/forecast_lab.py` | scikit-learn |
| VIF + joint F-test + econ significance | `research/stat_models.py` | statsmodels |
| Seaborn report styling | `reports/generator.py` | seaborn |

## Honesty disciplines

- **Isolation Forest / PCA:** adapted criteria per Phase 17 Section 3 (not literal P3 forecast gate)
- **Random Forest:** standard P3 baseline-beating gate (`SIGNAL` / `NO_SIGNAL`)

## Quick verification

```bash
cd C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc
python -m pytest tests/research/test_forecast_lab_extended.py tests/research/test_stat_models_rigor.py tests/reports/test_generator_styling.py -v
```

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for the full regression gate.