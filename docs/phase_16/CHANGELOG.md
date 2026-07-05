# Phase 16 Changelog

## 2026-07-04 — Phase 16 Complete

### Added

- `src/mcc/analytics/` — `validation.py`, `conversion.py`, `benchmark.py`
- `src/mcc/risk/riskfolio_adapter.py` — mean-risk, risk-parity, HRP, Kelly; Section 8.1 export
- `src/mcc/performance/quantstats_adapter.py` — trade→returns, metrics, HTML tearsheets
- `src/mcc/regime/hmm.py` — statsmodels MarkovRegression (replaces hmmlearn)
- `src/mcc/research/stat_models.py` — OLS, ADF, Ljung-Box, t-test wrappers
- `config/analytics.yaml` — risk-free rate, caps, report paths
- `docs/phase_16/*` — six documentation files
- Phase 16 test suite (7 modules, integration + grep guard)

### Modified

- `risk/sizing.py` — Kelly raw fraction via `riskfolio_adapter`; fractional cap preserved
- `risk/var_es.py` — optional `use_riskfolio` CVaR path
- `risk/portfolio.py` — `optimize_allocation` delegates to adapter with cap pass-through
- `performance/analytics.py` — composes QuantStats + preserved decision attribution
- `core/events.py` — `RegimeEvent` (shape stable)
- `core/exceptions.py` — `AnalyticsValidationError`, `AnalyticsConversionError`
- `pyproject.toml` — riskfolio-lib, quantstats, statsmodels, scipy pins
- `tests/test_safety_gates.py` — tuple unpack fix for `kelly_size`/`vol_target_size`

### Unchanged (by design)

- `risk/monitor.py` — `RiskState` dataclass
- `risk/prop_guardian.py`
- `regime/volatility_regime.py`
- `decision/engine.py` — `decide()` signature and behavior

### Cross-reference

See `BUILD_DECISIONS.md` for material technical decisions (Decimal boundary, flat-rate benchmark).