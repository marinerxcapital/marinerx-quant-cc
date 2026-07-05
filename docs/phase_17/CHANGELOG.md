# Phase 17 Changelog

## 2026-07-04 — Phase 17 Complete

### Added

- `src/mcc/research/forecast_lab.py` — Isolation Forest, PCA, Random Forest candidates
- `src/mcc/backtest/costs.py` — round-trip cost model for economic significance
- `src/mcc/reports/generator.py` — Seaborn default styling + optional openpyxl export
- `tests/research/test_forecast_lab_extended.py`
- `tests/research/test_stat_models_rigor.py`
- `tests/reports/test_generator_styling.py`
- `docs/phase_17/*` (5 files)

### Modified

- `src/mcc/research/stat_models.py` — VIF, joint F-test, statistical/economic significance split on OLS
- `src/mcc/research/__init__.py` — exports ForecastLab symbols
- `pyproject.toml` — `scikit-learn`, `seaborn`, `openpyxl`

### Explicitly excluded (per work order)

- Reinforcement learning, CNN/Transformer, genetic algorithms

### Cross-reference

`BUILD_DECISIONS.md` Phase 17 entry