# BUILD DECISIONS LEDGER

## Phase 17 — Forecast Extension + Statistical Rigor (2026-07-04)

- **Scope:** ResearchLab (`forecast_lab.py` new) + `stat_models.py` OLS rigor + `reports/generator.py` styling. Five bounded items only.
- **forecast_lab.py:** Created (did not exist pre-Phase 17). Isolation Forest uses adapted recall-vs-z-score discipline; PCA always discloses explained variance; Random Forest uses standard P3 MSE gate.
- **stat_models.py:** Phase 16 OLS extended additively with VIF (threshold 5), joint F-test, independent statistical/economic significance flags via `backtest/costs.py`.
- **Excluded:** RL, CNN/Transformer, genetic algorithms per work order Section 1.
- **Dependencies:** Only `seaborn` and `openpyxl` added as new; `scikit-learn` pinned (was in master brief but missing from pyproject.toml).

## Phase 16 — Riskfolio + QuantStats + statsmodels (2026-07-04)

- **Scope:** Refactor RegimeMonitor, RiskCommand, PerformanceAnalyst only. New `analytics/` boundary package.
- **Decimal boundary:** All `Decimal`→`float` for library calls routes through `analytics/conversion.py`. No bare `float(decimal_field)` in modified modules.
- **Riskfolio integration:** New `risk/riskfolio_adapter.py`; existing `kelly_size`/`historical_var_es` signatures preserved. Fractional Kelly cap wraps adapter raw output.
- **QuantStats benchmark:** Flat risk-free rate (`flat_rate_4.5pct`), not equity index — futures-only book.
- **Regime engine:** `hmmlearn.GaussianHMM` replaced by `statsmodels.MarkovRegression`. `RegimeEvent` shape unchanged; behavioral differences documented in `reports_out/diagnostics/regime_old_vs_new_comparison.json`.
- **RegimeEvent:** Added to `core/events.py` with `{type, symbol, state, confidence}` — no breaking change to consumers (new event type on LOG topic).
- **Dependencies:** `riskfolio-lib`, `quantstats`, `statsmodels`, `scipy` added to `pyproject.toml`.

## Phase 15 — UI Fidelity Match (2026-07-04)

- **Scope:** Frontend-only pass per `command-center/15_UI_MATCH_AND_RAILWAY_DEPLOY.md`. No backend/agent/risk/validation logic changes.
- **Design source:** Packaged PNG mockups + `MOCKUP_REFERENCE.md` + logo/X icon from `MarinerX_Labs_SuperGrok_UI_Match_Final_Package.zip`.
- **Architecture:** Single-page app with hash routing in `static/index.html`, `pages.js`, `app.js`, shared `design-tokens.css` + `app.css`.
- **Server change:** `server.py` root route serves `static/index.html` (fallback to legacy `_DASHBOARD_HTML`). `/health` and `/ws` unchanged.
- **Light theme:** Replaced Phase 14 dark Tailwind dashboard with institutional light theme per mockup spec.
- **Sample data:** Static mockup data in `pages.js` (not live backend feeds) — acceptable for UI fidelity gate.
- **Charts:** Plotly.js with white-background config matching mockup chart styling.
- **Deploy:** GitHub push to `marinerxcapital/marinerx-quant-cc` master triggers Railway auto-deploy.