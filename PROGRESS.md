# PROGRESS
Phase: 17
Last: Phase 17 Forecast Extension + Statistical Rigor — forecast_lab (IF/PCA/RF), stat_models VIF/F-test/econ split, reports Seaborn styling, full regression green
Worktrees: 15 (Phase 17 implemented in main tree; two Section 7 roles)
Evidence: pytest_phase17_full.txt, reports_out/diagnostics/phase17_evidence.json, phase17_chart.png, PHASE17_FORECAST_RIGOR.txt
Status: PHASE 17 COMPLETE — gate PASS

---

## CRITICAL PATCH 01 — P2 Risk Veto Pipeline Wiring (2026-07-05)

**Severity:** CRITICAL safety-integration fix (not a feature phase)

**Defect:** `pipeline.py` hardcoded `risk_veto=False` in `DecisionEngineAgent` and `ExecutionGatewayAgent`, so live decisions never consulted `RiskCommand`.

**Fix:** Event-subscription approach — both spine agents subscribe to `RiskCommand` bus publications; `RiskCommandAgent` runs `RiskMonitor` and publishes veto state.

**Files:** `src/mcc/agents/pipeline.py`, `tests/integration/test_pipeline_risk_veto.py`, `docs/deployment/EXECUTION_SAFETY_AUDIT.md`

**Status:** PATCH 01 COMPLETE — gate PASS (73 passed, 2026-07-05)