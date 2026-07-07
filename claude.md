# MarinerX Labs — Claude Project Memory

**Owner:** Skyler B. Brown  
**Last updated:** 2026-07-07

---

## Canonical Workspace

```
C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\
```

Never work in `marinerx-quant-cc-fresh` or other Desktop clones unless explicitly syncing.

---

## Deploy & Git (current)

| Item | Value |
|------|-------|
| **GitHub** | `marinerxcapital/marinerx-quant-cc` branch `master` |
| **HEAD** | `a311447` (pushed, synced with `origin/master`) |
| **Production** | https://marinerx-labs-api.onrender.com |
| **Render SHA** | `a311447+` |

### Commit chain (this build session)

| SHA | What shipped |
|-----|--------------|
| `8cea00c` | Tier 1: persistence, CRUD APIs, backtest/risk/decision engines, Tier 1 frontend JS, schema migration |
| `35aed8b` | Tier 2 page wiring (`tier2-data.js`), e2e replay fix, `main.py login`, AI memory files |
| `a311447` | Playwright `storage_state` compat fix for `tradeify-sync` login |

---

## Architecture Summary

| Layer | Technology |
|-------|------------|
| API | FastAPI (`src/mcc/interface/web/server.py`) |
| Agents | 15-agent supervisor (`src/mcc/runtime/bootstrap.py`) |
| DB | SQLAlchemy — SQLite local, Postgres on Render |
| UI | Static SPA — `pages.js` + data modules |
| Deploy | Docker → Render (`marinerx-labs-api.onrender.com`) |
| Tradeify | `tradeify-sync/` Playwright read-only sync |

---

## API Surface (Complete as of 2026-07-07)

**System:** `/version`, `/config-check`, `/api/system-state`, `/api/data-freshness`, `/api/db-health`  
**Strategies:** `/api/strategies` CRUD + archive  
**Research:** `/api/backtests/run`, `/api/validation/run`  
**Risk:** `/api/risk/state`, kill-switch, check-order  
**Decision:** `/api/decision/evaluate`  
**Data:** `/api/instruments`, `/api/market/bars`, `/api/market/snapshot`, `/api/macro/series`, `/api/data/sync`  
**Regime:** `/api/regime/current`  
**Orders:** `/api/orders`, `/api/orders/paper`, `/api/account/paper`  
**Journal:** `/api/journal` CRUD  
**Performance:** `/api/performance/summary`  
**Reports:** `/api/reports`, generate  
**Agents:** `/api/agents/snapshot`, market-pulse, indicators, journal  

---

## Frontend Data Modules (all 13 pages wired)

| Module | Pages |
|--------|-------|
| system-state.js | Header status |
| agent-data.js | Home agent grid |
| live-data.js | Market live (partial) |
| tradeify-data.js | Tradeify panels |
| strategies-data.js | Strategy Registry |
| backtest-data.js | Research Lab |
| risk-data.js | Risk Command |
| decision-data.js | Trade-or-No-Trade |
| **tier2-data.js** | **8 Tier 2 pages** (see below) |

### tier2-data.js pages (loading / error / empty / stale)

1. **market-pulse** — snapshot + agent fallback
2. **indicators** — regime + indicator agent
3. **validation** — strategy list + run validation
4. **execution** — orders + paper account + submit
5. **journal** — list/create/edit entries
6. **performance** — summary metrics
7. **reports** — list + generate
8. **settings** — config-check, db-health, version

Demo data labeled SIMULATED/DEMO. No fake NOMINAL or hardcoded P&L.

---

## Verification Commands

```powershell
python main.py doctor
python -m pytest tests/ -q
python -m pytest tests/test_end_to_end_replay.py -q
```

**Last verified:** 149 passed (full suite), e2e replay 2/2 green, doctor all green.

---

## Completed Work Log (2026-07-07 build session)

1. Git reconciliation: merged `3b757e0` + Phase 2 `535a9d2` (prior session)
2. **Tier 1 `8cea00c`:** persistence, CRUD, backtest, risk, decision APIs + frontend
3. **Tier 2 APIs:** validation, regime, orders, journal, performance, reports (in `platform_routes.py`)
4. **Tier 2 frontend `35aed8b`:** `tier2-data.js` for 8 remaining pages; `pages.js` mocks removed
5. **E2E replay fix:** NOT timing — was DecisionEngine NO_GO because:
   - Validation metrics defaulted to non-GREEN in replay → fixed with `_REPLAY_GREEN_METRICS`
   - AccountSync marked stale when tradeify DB missing → replay stub with `stale: false`
6. **`main.py login`:** delegates to `tradeify-sync/main.py login`
7. **Playwright fix `a311447`:** persistent context no longer passes `storage_state` at launch
8. **Production `/api/strategies` 500:** legacy Postgres schema → fixed by `_migrate_strategies()` on engine init; verify via `/api/db-health`
9. **Pushed to GitHub** `master`; Render deployed `a311447+`

---

## Production Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `GET /api/strategies` → 500 | Old `strategies` table missing Tier 1 columns | `ensure_schema()` migrates on startup (`8cea00c`); redeploy + check `/api/db-health` |
| Validation page "Strategies unavailable" | Same as above or cold start | Wait for Render boot; check `tier1_column_checks.strategies.missing_columns` |
| Tradeify sync stale | No session / no 2FA login | `python main.py login` (user action) |
| Account sync in prod | Missing Tradovate env | Set Render `TRADOVATE_*` secrets |

---

## Sellable Product Gap Analysis

### P0 — Must-have before selling

| Gap | Notes |
|-----|-------|
| Production-grade market data | Replace demo yfinance; CME/Nasdaq or paid feed |
| User authentication | No multi-user auth exists |
| Billing/subscriptions | Stripe or similar |

### P1 — Required for credible SaaS

| Gap | Notes |
|-----|-------|
| Onboarding wizard | First-run setup, API keys, account linking |
| Historical data warehouse | Bars stored at scale, not ephemeral |
| Walk-forward validation on real data | Current validation uses seeded/demo metrics |
| Tradeify + Tradovate live sync | **Blocked:** Skyler 2FA + Render `TRADOVATE_*` secrets |
| Error monitoring (Sentry) | Production incident response |
| Terms of service / risk disclaimers | Prop trading liability |

### P2 — Differentiators / polish

| Gap | Notes |
|-----|-------|
| Performance attribution from real fills | Not simulated P&L |
| Mobile layout polish | |
| PDF report generation | |
| Team workspaces | |
| API rate limiting | |
| SOC2-ready audit trail | |

### Current product positioning

**Sellable as:** Internal research tool / prop-firm evaluation assistant (beta)  
**Not yet sellable as:** Production trading platform / SaaS without auth, billing, and live data SLAs

**Estimated MVP SaaS:** 4–8 weeks focused engineering  
**Estimated institutional grade:** 3–6 months

---

## User Blockers (cannot be automated)

1. **Skyler** must run `python main.py login` and complete Tradeify **2FA** manually
2. **Render env:** set `TRADOVATE_CID`, `TRADOVATE_SECRET`, `TRADOVATE_USERNAME`, `TRADOVATE_PASSWORD`
3. **Optional:** `FRED_API_KEY`, `ALPHA_VANTAGE_API_KEY`