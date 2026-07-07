# Tier 1 Test Report

**Date:** 2026-07-07  
**Git commit:** local (uncommitted Tier 1 build)  
**Python:** 3.14  

## Commands Run

```powershell
python -m pytest tests/interface -q
python -m pytest tests/storage -q
python -m pytest tests/research -q
python -m pytest tests/risk -q
python -m pytest tests/decision -q
python main.py doctor
python -m pytest tests/ -q
```

## Full Suite Result

| Metric | Value |
|--------|-------|
| Total passed | **148** |
| Failed | **0** (was 1 — fixed 2026-07-07) |
| Duration | 142.38s |

## Failure Classification

| Test | Classification |
|------|----------------|
| `tests/test_end_to_end_replay.py::test_e2e_replay_via_bootstrap_green_path` | **fixed** — replay spine wiring (GREEN metrics stub + AccountSync fresh stub when sync DB absent); was pre-existing, not introduced by Tier 1 |

## Tier 1 Tests Added

- `tests/storage/test_research_persistence.py` (4)
- `tests/interface/test_strategy_routes.py` (2)
- `tests/interface/test_backtest_routes.py` (1)
- `tests/interface/test_risk_routes.py` (1)
- `tests/interface/test_decision_routes.py` (1)
- `tests/research/test_backtest_engine.py` (5)
- `tests/risk/test_risk_command.py` (6)
- `tests/decision/test_trade_decision_engine.py` (7)
- `tests/interface/test_frontend_smoke.py` (3)

## Doctor

All green.

## Coverage Gaps

- Browser E2E for wired pages
- Full Tier 2 integration tests for validation/regime/paper orders
- `test_regime_comparison_export` flake not observed this run

## Next Test Priorities

1. Fix or classify `test_e2e_replay_via_bootstrap_green_path`
2. Add Tier 2 API tests (validation, regime, journal CRUD, reports)
3. Playwright smoke for dashboard pages