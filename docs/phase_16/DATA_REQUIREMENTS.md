# Phase 16 Data Requirements

## Riskfolio-Lib (`risk/riskfolio_adapter.py`)

| Input | Source | Format |
|---|---|---|
| Return matrix | DuckDB/Parquet bar history or replay catalog | `pd.DataFrame`, columns NQ/ES/CL/GC, tz-aware UTC index |
| Position caps | `config/analytics.yaml` → `max_position_cap` | Per-instrument contract caps passed as weight upper bounds |
| Risk-free rate | `analytics.risk_free_rate_annual` | float, default 0.045 |

**Output:** Section 8.1 JSON to `reports_out/allocations/`

## QuantStats (`performance/quantstats_adapter.py`)

| Input | Source | Format |
|---|---|---|
| Trade blotter | TradeJournal SQLite / replay fixtures | `list[dict]` with `exit_ts`, `pnl` or `return_pct` |
| Benchmark | `analytics/benchmark.py` flat-rate resolver | Daily constant return series, labeled `flat_rate_4.5pct` |

**Output:** HTML tearsheet + Section 8.2 JSON to `reports_out/tear_sheets/`

## statsmodels (`regime/hmm.py`, `research/stat_models.py`)

| Input | Source | Format |
|---|---|---|
| Price series | Catalog bars via `load_or_synth_nq_bars` | tz-aware close prices, ≥31 observations |
| Factor panel (OLS) | Historical proxies | Aligned `pd.DataFrame` of factor columns |
| Residuals (Ljung-Box) | Fitted model residuals | `pd.Series` with DatetimeIndex |

**Output:** `RegimeEvent` + Section 8.3 diagnostics JSON to `reports_out/diagnostics/`

## Validation gate

All inputs pass through `analytics/validation.py` before any library call:

- tz-aware UTC indices
- monotonic increasing (no look-ahead)
- no NaN/inf values

Failures raise `AnalyticsValidationError` (logged, not silent NaN).

## Benchmark default behavior

MCC trades futures only (NQ, ES, CL, GC). There is no equity-index benchmark. Reports compare against a **flat configured risk-free rate** and label it explicitly — never "vs. market."