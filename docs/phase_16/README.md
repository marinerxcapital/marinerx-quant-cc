# Phase 16 — Riskfolio-Lib + QuantStats + statsmodels Upgrade

## Purpose

Phase 16 refactors three deployed MCC agents to wrap mature statistical libraries instead of hand-rolled code:

| Agent | Module | Library |
|---|---|---|
| **RiskCommand** | `src/mcc/risk/` | Riskfolio-Lib (portfolio optimization, CVaR, Kelly) |
| **PerformanceAnalyst** | `src/mcc/performance/` | QuantStats (tearsheets, Sharpe/Sortino/Calmar) |
| **RegimeMonitor** | `src/mcc/regime/` | statsmodels MarkovRegression (replaces hmmlearn) |

A new shared `src/mcc/analytics/` package enforces the Decimal↔float conversion boundary and input validation for all three integrations.

## Bus contracts preserved

- `RiskState` — unchanged dataclass in `risk/monitor.py`
- `RegimeEvent` — `{type, symbol, state, confidence}` on LOG topic
- `DecisionEvent` — `{symbol, decision, reason, size}` on DECISION topic

## Quick verification

```bash
cd C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc
pip install -e ".[dev]"
pytest tests/ -q
```

## Report outputs

- `reports_out/tear_sheets/` — QuantStats HTML tearsheets
- `reports_out/allocations/` — Riskfolio portfolio JSON (Section 8.1)
- `reports_out/diagnostics/` — regime old-vs-new comparison JSON

## Further reading

- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) — module walkthrough + runnable examples
- [API_CONTRACTS.md](API_CONTRACTS.md) — interface stability
- [TESTING_GUIDE.md](TESTING_GUIDE.md) — full test commands