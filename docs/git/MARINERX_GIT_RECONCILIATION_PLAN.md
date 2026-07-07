# MarinerX Git Reconciliation Plan

**Date:** 2026-07-07  
**Active path:** `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\`

## Current State

| Item | Value |
|------|-------|
| Branch | `master` |
| Local HEAD | `90d8c40` — Implement Tradeify 150K Select Flex data connector |
| Remote HEAD (`origin/master`) | `3b757e0` — feat: Tradeify sync engine, agent pipeline wiring, real dashboard APIs |
| Behind remote | 1 commit |
| Ahead of remote | 0 commits |

## Uncommitted Local Work (Phase 2)

**Modified (Phase 2):**
- `src/mcc/data/live/free_market.py` — cache freshness helpers
- `src/mcc/interface/web/server.py` — system router registration
- `src/mcc/interface/web/static/app.js` — SystemState.start()
- `src/mcc/interface/web/static/index.html` — removed hardcoded nominal/P&L

**Untracked (Phase 2):**
- `docs/audits/MARINERX_LABS_REAL_USAGE_AUDIT.md`
- `docs/CHATGPT_FRESH_SESSION_HANDOFF.md`
- `src/mcc/system/` — state.py, __init__.py
- `src/mcc/interface/web/system_routes.py`
- `src/mcc/interface/web/static/system-state.js`
- `tests/interface/test_system_routes.py`

**Incidental (exclude from Phase 2 commit):**
- `__pycache__/*.pyc` — do not commit
- `reports_out/diagnostics/regime_old_vs_new_comparison.json` — generated artifact
- `src/mcc/storage/models.py` — whitespace-only newline change

## Remote-Only Work (3b757e0)

Not present locally until merge:
- `tradeify-sync/` Python package + 28 tests
- `src/mcc/agents/snapshots.py`
- Rewired MarketPulse, IndicatorEngine, TradeJournal, AccountSync
- `src/mcc/interface/web/agent_routes.py`
- `src/mcc/interface/web/static/agent-data.js`
- ValidationEngine wiring fixes
- ExecutionGateway fill price fix
- `tests/integration/test_pipeline_agents_wiring.py`
- `tests/interface/test_agent_api.py`
- `pyproject.toml` norecursedirs fix

## Secret Safety

Diff scanned for `api_key`, `secret`, `token`, `password`, `DATABASE_URL`, etc.  
**Result:** No secret values found. Only env-var name references (e.g. `ALPHA_VANTAGE_API_KEY`).

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Lose Phase 2 uncommitted work | HIGH | Commit Phase 2 before pull |
| Merge conflicts in server.py, index.html, app.js | MEDIUM | Manual merge preserving both routers |
| agent_routes missing until merge | LOW | Expected; merge brings them |
| Stale folder confusion | LOW | Work only in active path |

## Recommended Sequence

1. Commit Phase 2 system-truth layer (this session).
2. `git pull --rebase origin master`
3. Resolve conflicts prioritizing both system_routes and agent_routes.
4. Run `python main.py doctor` and `python -m pytest tests/ -q`.
5. Proceed to Phase 3 persistence build.

## Exact Next Commands

```powershell
cd "C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc"

git add docs/audits/MARINERX_LABS_REAL_USAGE_AUDIT.md docs/CHATGPT_FRESH_SESSION_HANDOFF.md src/mcc/system src/mcc/interface/web/system_routes.py src/mcc/interface/web/static/system-state.js tests/interface/test_system_routes.py src/mcc/data/live/free_market.py src/mcc/interface/web/server.py src/mcc/interface/web/static/index.html src/mcc/interface/web/static/app.js

git commit -m "feat: add system truth and data freshness layer"

git pull --rebase origin master

python main.py doctor
python -m pytest tests/ -q
```