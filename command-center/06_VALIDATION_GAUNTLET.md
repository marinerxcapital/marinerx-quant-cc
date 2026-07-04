# PHASE 06 — VALIDATION GAUNTLET (the discipline, enforced in code)

**CONTEXT:** Strategy framework + backtesting complete. Build the gauntlet that alone can promote a strategy to `GREEN`. This encodes the pre-registration → purged walk-forward → Deflated Sharpe → verdict protocol so no strategy reaches execution on the strength of an overfit backtest.

---

## 1. `validation/prereg.py`
- `Hypothesis` model: statement, exact rules, parameter grid, cost model, sample window/exclusions (decided before data contact), and locked verdict thresholds. `register()` hashes + timestamps the doc and writes it immutable to the `hypotheses` table.
- **Trial counter:** every backtest run against a hypothesis (vectorized or event-driven) increments its `trial_count`. Silent re-testing is impossible; DSR uses the true count.
- **No-resurrection clause:** a `RED` hypothesis cannot be re-registered with tweaked rules under the same id; a variant is a new hypothesis at the back of the queue.

## 2. `validation/walkforward.py`
- Purged, embargoed walk-forward: expanding or rolling folds with a configurable purge gap and embargo to prevent leakage across the train/test boundary. In-sample selects parameters from the pre-registered grid only; each OOS fold is scored once. Aggregate OOS trades.

## 3. `validation/statistics.py`
- Deflated Sharpe Ratio (using true `trial_count`), Probabilistic Sharpe Ratio, net profit factor, expectancy, OOS fold win-rate, max drawdown. Implement DSR/PSR per López de Prado; document formulas.

## 4. `validation/montecarlo.py`
- 10,000-path bootstrap/permutation of the OOS trade sequence → drawdown and terminal-PnL distributions; reported for context (and available as a decision-engine input) but not the sole pass/fail gate.

## 5. `validation/verdict.py`
- Apply locked thresholds → `GREEN | YELLOW | RED` with a written rationale memo. Example defaults (overridable per hypothesis): GREEN = OOS net PF ≥ 1.25 · DSR>0 @95% · PSR ≥ 0.90 · ≥4/5 OOS folds net-positive · ≥100 OOS trades; YELLOW = marginal, one pre-specified sample-extension follow-up permitted; RED = archive. Writing a `GREEN` verdict is the **only** path that flips a strategy's status to `GREEN` (Phase 05 guard checks for a verdict row).
- Wrapped by the **ValidationEngine** agent (per the Master Brief's 15-agent roster — ValidationEngine owns both `backtest/` and all of `validation/`); emits `DecisionEvent`-adjacent verdict events and persists memos.

---

## PHASE 06 ACCEPTANCE GATE
- Registering a hypothesis writes an immutable, hashed row; attempting to modify it raises `IntegrityError`.
- A known-overfit toy strategy earns `RED` (DSR ≈ 0); a constructed genuine-edge synthetic series earns `GREEN` — proving the gauntlet discriminates.
- Trial count reflects total combinations tested; DSR shrinks as trial count grows (assert monotonic relationship on a fixture).
- A strategy's status flips to `GREEN` only after a passing verdict row exists; direct promotion raises.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-RESEARCH (Phase 07) per the dependency graph — no user interaction.
