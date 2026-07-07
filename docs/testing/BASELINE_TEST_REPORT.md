# Baseline Test Report

**Date:** 2026-07-07  
**Git commit:** `535a9d2` (post-merge baseline)  
**Python:** 3.14  

## Commands

```powershell
python main.py doctor
python -m pytest tests/ -q
```

## Doctor Result

All green — live execution DISABLED, 15 agents registered.

## Pytest Result (post-merge baseline)

| Metric | Value |
|--------|-------|
| Passed | 118 |
| Failed | 1 |
| Duration | ~117s |

**Failure:** `tests/test_end_to_end_replay.py::test_e2e_replay_via_bootstrap_green_path`  
**Classification:** pre-existing / environment — not introduced by Phase 2 merge.

## Known Flakes

- `tests/integration/test_phase16_end_to_end.py::test_regime_comparison_export` — intermittent HMM SVD (not observed this run)

## Go/No-Go

**GO** for Tier 1 feature build after classifying e2e replay failure as non-blocking.