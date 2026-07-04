# PHASE 07 — QUANT MODELING & RESEARCH LAB

**CONTEXT:** Validation gauntlet complete. Build the research tooling for feature engineering, forecasting, and statistical modeling. Principle P3 (honest forecasting) is enforced here: nothing that fails to beat a naive baseline may feed the decision engine.

---

## 1. `research/features.py`
- Feature pipeline over historical + internals + microstructure data: returns, vol, indicator values, regime labels, internals z-scores, event-proximity flags, calendar features. Strict point-in-time construction (no leakage); a `FeatureSet` carries its as-of timestamps. Cache feature matrices to parquet keyed by config hash.

## 2. `research/forecast_lab.py`
- Train/evaluate predictive models (gradient boosting via `lightgbm`, logistic/linear baselines, simple time-series) for defined targets (e.g., sign/magnitude of forward return over horizon H).
- **Mandatory baselines:** naive persistence and random. Score with Brier (probabilistic), hit-rate vs. baseline, and economic value (return net of costs from acting on the signal). A model is tagged `SIGNAL` only if it beats baselines out-of-sample by a configured margin; otherwise `NO_SIGNAL`. Only `SIGNAL` models can be referenced by the decision engine.
- Use purged/embargoed CV consistent with Phase 06; report with honest error bars.

## 3. `research/stat_models.py`
- Pairs/cointegration (ADF, Johansen) for relative-value ideas (e.g., ES/NQ spread); regime-switching models; stationarity tests. Each returns diagnostics, not just point estimates.

## 4. `research/experiments.py`
- Lightweight experiment tracker: log each run's config hash, dataset window, metrics, and artifacts to the `experiments` table + parquet; make results queryable and diffable. Prevents "I think this worked once" — every claim is reproducible from a logged config.

---

## PHASE 07 ACCEPTANCE GATE
- Feature pipeline passes a leakage test (a feature built with future data is detected/blocked; as-of timestamps enforced).
- `forecast_lab` correctly labels a pure-noise target `NO_SIGNAL` and a constructed learnable target `SIGNAL`, each with baseline comparisons and Brier scores.
- `stat_models` recovers a known cointegrating relationship on a synthetic pair (Johansen rank > 0) and rejects it on independent random walks.
- Every experiment run is reconstructable from its logged config hash.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-RISK (Phase 08) per the dependency graph — no user interaction.
