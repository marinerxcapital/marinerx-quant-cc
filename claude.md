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

**System:** `/version`, `/config-check`, `/api/system-state`, `/api/data-freshness`  
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

## Frontend Data Modules

| Module | Pages |
|--------|-------|
| system-state.js | Header status |
| agent-data.js | Home agent grid |
| live-data.js | Market live |
| tradeify-data.js | Tradeify panels |
| strategies-data.js | Strategy Registry |
| backtest-data.js | Research Lab |
| risk-data.js | Risk Command |
| decision-data.js | Trade-or-No-Trade |
| tier2-data.js | Markets, Indicators, Validation, Execution, Journal, Performance, Reports, Settings |

All wired pages must show: loading, error, empty, stale states. Demo data labeled SIMULATED/DEMO.

---

## Verification Commands

```powershell
python main.py doctor
python -m pytest tests/ -q
```

Last verified: **149 passed** (after e2e fix), doctor all green.

---

## Completed Work Log

1. Git reconciliation: merged `3b757e0` + Phase 2 `535a9d2`
2. Tier 1 platform `8cea00c`: persistence, CRUD, backtest, risk, decision
3. Tier 2 APIs: validation, regime, orders, journal, performance, reports
4. Tier 2 frontend: `tier2-data.js` for 8 remaining pages
5. E2E replay fix: replay mode uses GREEN validation metrics + fresh AccountSync stub
6. `main.py login` delegates to `tradeify-sync/main.py login`

---

## Sellable Product Gap Analysis

### Must-have before selling

| Gap | Priority | Notes |
|-----|----------|-------|
| Production-grade market data | P0 | Replace demo yfinance; CME/Nasdaq or paid feed |
| User authentication | P0 | No multi-user auth exists |
| Billing/subscriptions | P0 | Stripe or similar |
| Onboarding wizard | P1 | First-run setup, API keys, account linking |
| Historical data warehouse | P1 | Bars stored at scale, not ephemeral |
| Walk-forward validation on real data | P1 | Current validation uses seeded metrics |
| Tradeify + Tradovate live sync | P1 | User 2FA + Render secrets |
| Error monitoring (Sentry) | P1 | Production incident response |
| Terms of service / risk disclaimers | P1 | Prop trading liability |
| Performance attribution from real fills | P2 | Not simulated P&L |

### Nice-to-have

- Mobile layout polish
- PDF report generation
- Team workspaces
- API rate limiting
- SOC2-ready audit trail

### Current product positioning

**Sellable as:** Internal research tool / prop-firm evaluation assistant (beta)  
**Not yet sellable as:** Production trading platform / SaaS without auth, billing, and live data SLAs

---

## User Blockers

- Skyler must run `python main.py login` and complete Tradeify 2FA manually
- Render env: set TRADOVATE_* for account sync in production