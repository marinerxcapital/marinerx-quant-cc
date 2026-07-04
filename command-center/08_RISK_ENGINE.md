# PHASE 08 — RISK ENGINE · PROPGUARDIAN · REAL-TIME MONITOR

**CONTEXT:** Data, internals, strategy, validation, research complete. Build the risk layer. Principle P2: risk vetoes override signals. Every sizing and limit decision is explainable and logged.

---

## 1. `risk/sizing.py`
- Position sizing methods: fixed, fractional **Kelly (capped)**, and **volatility targeting** (scale contracts to a target dollar-vol using recent realized vol). Inputs: account equity, per-trade risk budget, instrument tick value, current vol. Output: contract count + the reasoning. Never exceed configured per-trade and per-instrument caps.

## 2. `risk/var_es.py`
- Portfolio Value-at-Risk (historical simulation) and Expected Shortfall (CVaR) across open positions; rolling estimation; expose current VaR/ES vs. configured limits.

## 3. `risk/portfolio.py`
- Aggregate exposure, net/gross, correlation-adjusted risk using the Phase-03 correlation matrix (optionally a t-copula for tail dependence); flag concentration and correlated-cluster risk.

## 4. `risk/prop_guardian.py`
- Consume account state from the account-sync adapter (Phase 02). Track per account: trailing drawdown floor, `drawdown_headroom`, daily loss limit, daily P&L, consistency metric, and payout eligibility. Emit tiered `RiskEvent`s: `OK → CAUTION (reduce size) → LOCKOUT (no new risk)` as headroom shrinks. LOCKOUT is a hard veto to the decision engine and execution gateway.

## 5. `risk/monitor.py`
- Real-time monitoring loop (owned by the **RiskCommand** agent, per the Master Brief's 15-agent roster — RiskCommand unifies sizing, VaR/ES, PropGuardian, and this monitor into one runtime service and one dashboard panel): subscribes to fills/positions/prices, recomputes live exposure, VaR/ES, and PropGuardian state on each update; publishes a consolidated `RiskState` snapshot for the decision engine and interface; owns the risk kill-switch path.

---

## PHASE 08 ACCEPTANCE GATE
- Kelly sizing is capped; vol-targeting produces smaller size as realized vol rises (assert on a fixture); all outputs include reasoning.
- VaR/ES computed correctly on a historical fixture vs. hand calculation; limits breach flagged.
- PropGuardian transitions OK→CAUTION→LOCKOUT at configured headroom thresholds; LOCKOUT emits a hard veto event.
- RiskCommand's monitoring loop updates `RiskState` on a simulated fill stream within the throttle interval.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-DECISION (Phase 09) per the dependency graph — no user interaction.
