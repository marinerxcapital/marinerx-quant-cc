# MarinerX Labs — Real Usage Discovery Audit

**Audit date:** 2026-07-07  
**Auditor:** Grok (Real Quant Platform Build — Phase 1)  
**Active project path:** `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\`  
**Git HEAD:** `90d8c40` — *Implement Tradeify 150K Select Flex data connector*  
**Remote:** `https://github.com/marinerxcapital/marinerx-quant-cc.git` (branch `master`)  
**Note:** Local tree is **behind** remote `3b757e0` (continuation work exists on GitHub but not merged into this active folder).

---

## 1. Runtime Commands (verified)

| Command | Purpose | Status |
|---------|---------|--------|
| `python main.py doctor` | Preflight checks | **Ran 2026-07-07 — All green** |
| `python main.py run --interface web` | Web server (uvicorn via Typer) | Expected entry; serves `src/mcc/interface/web/server.py` |
| `python -m pytest tests/ -q` | Test suite | **Ran 2026-07-07 — 103 passed in 133.28s** |

**Incorrect command (do not use):** `uvicorn mcc.api.main:app` — no such module.

---

## 2. Doctor Output (captured)

```
config                       OK env=local mode=web
live execution               DISABLED (default)
production config            OK
database                     OK postgres
object storage               ok (local)
supervisor + 15 agents       OK (15 registered)
strategy lifecycle (P1)      OK
execution guardrails (P1/P2) OK
decision vetoes              OK
tradeify guard               OK
replay adapter (default)     OK (no keys needed)
All green
```

---

## 3. Test Inventory

| Metric | Value |
|--------|-------|
| Test files under `tests/` | 20 |
| Tests collected & passed | **103** |
| Warnings | 26 (CVXPY deprecation, statsmodels convergence) |

**Not present locally (on remote `3b757e0`):** `test_agent_api.py`, `test_pipeline_agents_wiring.py`, `tradeify-sync` package tests (+11 tests).

---

## 4. Backend Routes (current)

### Core (`server.py`)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | Agent + DB + object-store composite health |
| GET | `/` | SPA `static/index.html` |
| WS | `/ws` | WebSocket agent snapshot + bus bridge |

### Live data (`live_routes.py` — prefix `/api/live`)

| Method | Path | Data source |
|--------|------|-------------|
| GET | `/api/live/snapshot` | yfinance proxies via `free_market.py` |
| GET | `/api/live/bars/{symbol}` | yfinance |
| GET | `/api/live/internals` | Computed proxies (labeled) |
| GET | `/api/live/regime` | Regime snapshot |
| GET | `/api/live/decision` | Decision engine output |
| GET | `/api/live/risk` | Riskfolio + prop guardian proxies |
| GET | `/api/live/performance` | Performance proxy |
| GET | `/api/live/tradingview` | TV symbol map |
| GET | `/api/live/sources` | Source attribution |

### Tradeify 150K (`marinerx_tradeify/router.py` — prefix `/api/tradeify/150k`)

Rules, eval/payout/risk gates, data sync/status/health/reconcile endpoints.

### Missing (required by Real Quant Build master prompt)

| Endpoint | Phase |
|----------|-------|
| `GET /version` | 2 |
| `GET /config-check` | 2 |
| `GET /api/system-state` | 2 |
| `GET /api/data-freshness` | 2 |
| `GET /api/instruments` | 4 |
| `GET /api/market/bars` | 4 |
| `GET /api/strategies` (+ CRUD) | 5 |
| `POST /api/backtests/run` | 6 |
| `POST /api/validation/run` | 7 |
| `GET /api/regime/current` | 8 |
| `POST /api/decision/evaluate` | 9 |
| `GET /api/risk/state` (+ kill-switch) | 10 |
| Paper orders / journal / performance / reports APIs | 11–14 |

---

## 5. Frontend Routes (SPA hash pages)

All 13 pages defined in `static/index.html` sidebar + `static/pages.js`:

1. `#home` 2. `#market-pulse` 3. `#indicators` 4. `#strategy` 5. `#validation`  
6. `#research` 7. `#risk` 8. `#decision` 9. `#execution` 10. `#journal`  
11. `#performance` 12. `#reports` 13. `#settings`

**Scripts loaded:** `pages.js`, `tradingview.js`, `live-data.js`, `tradeify-data.js`, `app.js`  
**Missing:** `agent-data.js`, `system-state.js` (Phase 2 target)

---

## 6. Storage Behavior

| Layer | Implementation |
|-------|----------------|
| ORM | SQLAlchemy in `src/mcc/storage/models.py` |
| DB URL | `DATABASE_URL` → Postgres; else `sqlite:///{DATA_DIR}/mcc.sqlite` |
| Tables today | `strategies` (id+status only), `account_states`, `trades`, `decision_logs`, `report_metadata`, `agent_heartbeats` + Tradeify persistence tables |
| Object store | Local dir or Cloudflare R2 |
| Init | `init_db()` / `get_engine()` auto `create_all` |

**Gap:** Master prompt tables (market_bars, backtest_runs, validation_results, journal_entries, orders, risk_events, etc.) **not implemented**.

---

## 7. Data Sources

| Source | Status | Labeling |
|--------|--------|----------|
| yfinance (NQ=F, ES=F, CL=F, GC=F, ^VIX) | **Working** via `/api/live/*` | Labeled `yfinance_proxy` in responses |
| Alpha Vantage | Optional env key | Stub path in `free_market.py` |
| Tradovate API | Connector exists; creds often missing | Error surfaced in tradeify data health |
| Tradeify dashboard | Playwright connector; session env required | Disabled by default |
| Tradeify Sync Engine | **Spec only** (9 markdown files in `tradeify-sync/`, zero Python) | N/A |
| Replay adapter | Default for agent bus BAR events | Demo/replay |

---

## 8. Fake / Static / Demo Values (must remove or label)

### `static/index.html` (CRITICAL)

- Header: **`ALL SYSTEMS NOMINAL`** — hardcoded, not API-backed
- Header P&L: **`+$1,240` / `+$3,870` / `$4,620`** — hardcoded fake live P&L
- Clock: static placeholder `2025-05-30 14:32:18 UTC` (overwritten by `app.js` timer only)

### `static/pages.js` (CRITICAL)

- Entire **agent grid** — fabricated metrics (Uptime 99.98%, Events/min 1,842, etc.)
- **Instrument Decision Center** — hardcoded prices/decisions (NQ GO @ 18,742.75, etc.)
- All 13 page templates contain static tables, badges, and numbers

### `static/app.js`

- Chart init uses **`Math.random()`** for sparklines and synthetic candlesticks when live data absent
- `pollHealth()` updates agent dot colors only — not metrics text

### `static/live-data.js`

- Partial hydration for market-pulse, indicators, risk, decision, performance from `/api/live/*`
- Fallback comment: `/* keep mock */` on fetch failure

### `static/tradeify-data.js`

- Polls real `/api/tradeify/150k/data/*` but shows **"Awaiting synced account snapshot"** when creds missing

### Agent pipeline (`src/mcc/agents/pipeline.py`)

- **Spine agents wired:** ValidationEngine, DecisionEngine, ExecutionGateway, RiskCommand (PATCH 01)
- **Stub agents (sleep + set_status only):** MarketPulse, IndicatorEngine, TradeJournal, AccountSync, DataOps, Overseer, RegimeMonitor, StrategyRunner, ResearchLab, PerformanceAnalyst, ReportPublisher

---

## 9. Deployment Config

| File | Target |
|------|--------|
| `Dockerfile` | Python 3.11 slim, `python main.py run --interface web` |
| `render.yaml` | `marinerx-labs-api`, Docker, free tier, `/health`, auto-deploy `master` |
| `railway.json` | Present (Railway fallback) |
| Production URL | `https://marinerx-labs-api.onrender.com` |

---

## 10. Health Endpoints

| Endpoint | Returns |
|----------|---------|
| `/health` | `status`, `app_env`, `agents{}`, `database`, `object_storage`, `live_execution_enabled`, `ts` |

No `/version`, `/config-check`, `/api/system-state`, or honest stale/NOMINAL gating.

---

## 11. Gaps Blocking Real Usage

1. **No system truth layer** — header lies about NOMINAL and P&L  
2. **No persistence for research workflow** — strategies are a single-column table; no backtest/validation/decision persistence APIs  
3. **UI is mostly static templates** — only 5 pages partially hydrated via `/api/live/*`  
4. **9 of 15 agents are no-op stubs** — bus events do not flow to UI for most agents  
5. **Tradeify Sync Engine not built** — AccountSync has nothing real to read  
6. **No paper order / journal CRUD APIs** — journal page is static HTML  
7. **No `/api/decision/evaluate`** — decisions computed in agent bus, not exposed as persisted API  
8. **Local tree behind GitHub** — missing `agent_routes`, `tradeify-sync` Python, wiring fixes from `3b757e0`  
9. **pytest `norecursedirs`** not set — duplicate test in `docs/tradeify-connector-package/` can cause collection conflicts if discovered

---

## 12. Existing Strengths (reuse, do not rewrite)

- FastAPI + Typer CLI + 15-agent supervisor architecture  
- CRITICAL_PATCH_01 risk_veto bus wiring (`tests/integration/test_pipeline_risk_veto.py`)  
- Phase 16/17 quant libraries: Riskfolio, QuantStats, statsmodels, HMM regime, report generator  
- `free_market.py` yfinance ingestion with cache + source labeling  
- Tradeify 150K rules/eval/risk connector package  
- Docker/Render deployment pipeline  
- 103 passing tests on current tree  

---

## 13. Files To Modify (by phase)

### Phase 2 — System Truth (immediate)

| File | Action |
|------|--------|
| `src/mcc/system/state.py` | **Create** — system state + freshness service |
| `src/mcc/interface/web/system_routes.py` | **Create** — `/version`, `/config-check`, `/api/system-state`, `/api/data-freshness` |
| `src/mcc/interface/web/server.py` | Wire system router |
| `src/mcc/data/live/free_market.py` | Export cache timestamps |
| `static/system-state.js` | **Create** — header hydration |
| `static/index.html` | Remove hardcoded NOMINAL/P&L; load system-state.js |
| `tests/interface/test_system_routes.py` | **Create** |

### Phase 3 — Persistence

| File | Action |
|------|--------|
| `src/mcc/storage/models.py` | Expand schema (instruments, market_bars, backtest_runs, …) |
| `src/mcc/storage/repositories/` | **Create** service boundary |

### Phases 4–14

See master prompt `MARINERX_LABS_REAL_QUANT_BUILD_MASTER_PROMPT.md` — provider interfaces, strategy CRUD, backtest/validation/decision/risk/order APIs, report generation.

### Phase 16 — Frontend

| File | Action |
|------|--------|
| `static/pages.js` | Replace static data with API hydration + empty/stale states |
| `static/live-data.js` | Extend or merge into per-page fetch modules |

---

## 14. Implementation Phases (ordered)

| Phase | Scope | Priority |
|-------|-------|----------|
| **1** | This audit | ✅ Complete |
| **2** | System truth + data freshness + header wiring | **Tier 1 — in progress** |
| **3** | Persistence schema + repositories | Tier 1 |
| **5** | Strategy registry API + UI | Tier 1 |
| **6** | Backtest engine | Tier 1 |
| **10** | Risk state + kill switch API | Tier 1 |
| **9** | Trade-or-no-trade evaluate API | Tier 1 |
| **4** | Market data providers + sync | Tier 2 |
| **7** | Validation engine API | Tier 2 |
| **8** | Regime engine API | Tier 2 |
| **11–14** | Paper orders, journal, performance, reports | Tier 2 |
| **16–18** | Full page wiring, docs, tests | Tier 3 |

---

## 15. Commands Run For This Audit

```powershell
cd C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc
python main.py doctor          # All green
python -m pytest tests/ -q     # 103 passed in 133.28s
git log -3 --oneline           # HEAD 90d8c40
```

---

## 16. Limitations Of This Audit

- Did not start `python main.py run --interface web` for live browser screenshot (Phase 2 will verify header wiring).  
- Production Render state not re-probed during this audit (prior session confirmed `3b757e0` deployed on remote).  
- No logic changes made during Phase 1 (documentation only).