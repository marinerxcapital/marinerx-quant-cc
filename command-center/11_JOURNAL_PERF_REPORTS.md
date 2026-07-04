# PHASE 11 — JOURNAL · PERFORMANCE · REPORTING

**CONTEXT:** Execution emits fills onto the bus (paper by default). Build the record-keeping, analytics, and reporting layer that closes the feedback loop from live trading back into research.

---

## 1. `journal/journal.py`
- `TradeJournal` agent: auto-ingest fills from the bus into round-turn trades; enrich each with structured tags — setup type, strategy id, regime at entry, internals state at entry, decision-engine reason string, and free-text/emotion notes + optional screenshot path. Also ingest account-sync trades (real executions) so paper and real are both journaled, clearly labeled. Queryable via the relational store.

## 2. `performance/analytics.py`
- `PerformanceAnalyst` agent: equity curve, rolling Sharpe/Sortino, drawdown analysis, win rate, expectancy, profit factor, and **expectancy broken down by setup / regime / instrument / decision-engine confidence band**. Crucially, compute **decision attribution**: were GO calls profitable vs. the NO-GO counterfactual? This feeds back into factor weighting.

## 3. `reports/generator.py` + `reports/templates/`
- Generate MarinerX-branded PDF (matplotlib/`reportlab`) and HTML reports: (a) a validation/verdict memo per hypothesis, (b) a weekly performance report (equity, key metrics, per-setup expectancy, PropGuardian headroom trend, decision attribution), (c) a research report template. Output to `reports_out/`.
- `ReportPublisher` agent runs scheduled/weekly and on demand via CLI.

---

## PHASE 11 ACCEPTANCE GATE
- A simulated fill stream produces correctly assembled round-turn trades with all tags populated.
- Analytics match hand calculations on a fixture (Sharpe, PF, expectancy); per-setup and per-regime breakdowns correct; decision attribution distinguishes profitable vs. unprofitable GO calls.
- `report weekly` produces a valid branded PDF + HTML in `reports_out/`.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-UI (Phase 12) per the dependency graph — no user interaction.
