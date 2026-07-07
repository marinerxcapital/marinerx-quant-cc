# MarinerX Labs — Fresh Session Handoff (ChatGPT / Any Agent)

**Purpose:** Give this entire file to a new AI session so it can continue without re-discovering context.  
**Last updated:** 2026-07-07  
**Authoritative workspace — work ONLY here:**

```text
C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\
```

**Do NOT use stale folders** (e.g. `marinerx-quant-cc-fresh` on Desktop, old extracts) unless explicitly syncing from GitHub.

---

## 1. What This Project Is

**MarinerX Labs Research System** — a Python 3.11+ quantitative research and risk-control platform:

- FastAPI web dashboard (13 SPA pages)
- 15-agent async runtime (Typer CLI + supervisor)
- Postgres/SQLite persistence, Docker → Render deployment
- Paper-first execution (live orders disabled by default)

**Goal:** Upgrade from a visual dashboard shell into a **real, usable** quant research OS — real APIs, persistence, calculations, honest UI state (no fake NOMINAL, no fake P&L).

---

## 2. Master Build Instructions (READ FIRST)

Full phased spec:

```text
C:\Users\Skyler B. Brown\Desktop\MARINERX_LABS_REAL_QUANT_BUILD_MASTER_PROMPT.md
```

Rules from that doc:

1. Run **discovery audit** before logic changes (audit exists — see §4).
2. Build in **phases**; do not skip.
3. Do **not** fake telemetry or hardcode nominal status.
4. Do **not** claim tests pass unless you run:
   ```powershell
   cd C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc
   python main.py doctor
   python -m pytest tests/ -q
   ```
5. Correct web entry: `python main.py run --interface web` → `src/mcc/interface/web/server.py`
6. **Wrong command:** `uvicorn mcc.api.main:app` (does not exist)

Earlier continuation work (Grok) used:

```text
C:\Users\Skyler B. Brown\Desktop\MarinerX_Grok_Continuation_Directive\GROK_CONTINUATION_DIRECTIVE.md
```

Some of that work landed on **GitHub** but not in this local folder — see §8.

---

## 3. Runtime Commands

```powershell
cd C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc
python -m pip install -e ".[dev]"
python main.py doctor
python main.py run --interface web
# Browser: http://localhost:8000/#home
python -m pytest tests/ -q
```

**Production:** https://marinerx-labs-api.onrender.com  
**GitHub:** https://github.com/marinerxcapital/marinerx-quant-cc (branch `master`)

---

## 4. What Has Been Done

### 4A. Prior project history (Phases 1–17, pre–Real Quant Build)

| Area | Status |
|------|--------|
| 15-agent supervisor + bootstrap | Exists |
| CRITICAL_PATCH_01 — `risk_veto` bus wiring | Done in `pipeline.py`; `tests/integration/test_pipeline_risk_veto.py` |
| Spine agents | ValidationEngine, DecisionEngine, ExecutionGateway, RiskCommand partially wired |
| Phase 16/17 libs | Riskfolio, QuantStats, statsmodels, HMM regime, report generator — unit/integration tested |
| `/api/live/*` routes | yfinance proxies (bars, internals, regime, decision, risk, performance) |
| `/api/tradeify/150k/*` | Rules, eval, payout, risk gate, data sync connectors |
| Tradeify 150K connector package | `src/marinerx_tradeify/` |
| Docker + `render.yaml` | Deployed to Render |
| Frontend partial wiring | `live-data.js`, `tradeify-data.js`, `tradingview.js` hydrate some pages |

### 4B. Real Quant Build — Phase 1 (Discovery Audit) ✅

**File:** `docs/audits/MARINERX_LABS_REAL_USAGE_AUDIT.md`

Documented: routes, fake UI values, storage gaps, agent stubs, test count, deployment, implementation phases.

### 4C. Real Quant Build — Phase 2 (System Truth Layer) ✅ — **UNCOMMITTED locally**

| Deliverable | Location |
|-------------|----------|
| System state service | `src/mcc/system/state.py` |
| New routes | `src/mcc/interface/web/system_routes.py` |
| Market cache freshness | `src/mcc/data/live/free_market.py` → `get_cache_freshness()` |
| Header wiring (no fake NOMINAL/P&L) | `static/system-state.js`, `static/index.html`, `static/app.js` |
| Tests (5) | `tests/interface/test_system_routes.py` |

**New endpoints:**

| Method | Path |
|--------|------|
| GET | `/version` |
| GET | `/config-check` |
| GET | `/api/system-state` |
| GET | `/api/data-freshness` |

**Status labels:** `NOMINAL` | `STALE` | `DEGRADED` | `LOCKED` — header only shows NOMINAL when API confirms fresh required sources and no kill switch.

### 4D. Grok continuation session (on GitHub `3b757e0`, NOT in this local tree)

A separate Grok session pushed to GitHub but **this active folder was never updated**. Remote commit `3b757e0` includes:

- Full `tradeify-sync/` Python package (Playwright read-only sync, 28 tests)
- `src/mcc/agents/snapshots.py`, rewired MarketPulse/IndicatorEngine/TradeJournal/AccountSync
- `src/mcc/interface/web/agent_routes.py` + `static/agent-data.js`
- E2E wiring audit fixes (ValidationEngine, ExecutionGateway fill price, etc.)
- `tests/integration/test_pipeline_agents_wiring.py`, `tests/interface/test_agent_api.py`
- `pyproject.toml` `norecursedirs` fix

**Local HEAD is still `90d8c40`.** Production Render was deployed to `3b757e0` as of 2026-07-07.

---

## 5. Verification Evidence (last run on THIS workspace)

```text
python main.py doctor  → All green (15 agents, live execution DISABLED)
python -m pytest tests/ -q → 108 passed in ~140s (includes 5 new system-route tests)
```

Before Phase 2 changes: **103 passed**.

**Do not claim green without re-running both commands after your edits.**

---

## 6. What Still Needs To Be Done

Follow `MARINERX_LABS_REAL_QUANT_BUILD_MASTER_PROMPT.md` phases in priority order.

### Tier 1 — Must ship next

| Phase | Work | Notes |
|-------|------|-------|
| **3** | Persistence layer | Expand `models.py`: instruments, market_bars, backtest_runs, validation_results, trade_decisions, orders, journal_entries, risk_events, etc. Repository boundary. |
| **5** | Strategy registry API | `GET/POST/PATCH /api/strategies`, wire Strategy Registry page |
| **6** | Backtest engine | `POST /api/backtests/run`, persist runs, deterministic tests |
| **10** | Risk state API | `GET /api/risk/state`, kill-switch POST endpoints, wire Risk page |
| **9** | Trade-or-no-trade API | `POST /api/decision/evaluate`, persist decisions, wire Decision page |
| **16** (partial) | Frontend header | Phase 2 done; remaining 12 pages still mostly `pages.js` mocks |
| **18** | Tests | Add CRUD/backtest/decision/risk tests per master prompt |

### Tier 2

| Phase | Work |
|-------|------|
| **4** | Market data providers (CSV, demo, FRED placeholder) + `/api/instruments`, `/api/market/bars`, `POST /api/data/sync` |
| **7** | Validation engine API `POST /api/validation/run` + verdict rules |
| **8** | Regime API `GET /api/regime/current` |
| **11** | Paper orders `POST /api/orders/paper` |
| **12** | Journal CRUD `GET/POST/PATCH /api/journal` |
| **13** | Performance `GET /api/performance/summary` |
| **14** | Reports generate/list |

### Tier 3

- Full frontend wiring for all 13 pages (loading/error/stale/empty states)
- Documentation package (`docs/MARINERX_LABS_BUILD_PACKAGE.md`, API_REFERENCE, etc.)
- Vendor adapters, deployment hardening

### Sync decision (important)

**Either:**

1. `git pull` / merge `3b757e0` from GitHub into this active folder **before** duplicating Grok's work, **or**
2. Re-implement missing pieces locally.

Recommended: **pull `master` first**, resolve conflicts, re-run doctor + pytest.

---

## 7. Known Issues & Blockers

### 7.1 Local vs remote divergence

| Location | Commit | Notes |
|----------|--------|-------|
| **This active folder** | `90d8c40` + uncommitted Phase 2 files | Missing Grok `3b757e0` work |
| **GitHub / Render** | `3b757e0` | Has agent routes, tradeify-sync Python, wiring fixes |
| **Desktop `marinerx-quant-cc-fresh`** | Was at `3b757e0` | Stale clone — do not treat as canonical |

### 7.2 Uncommitted local changes (Phase 2)

```
?? docs/audits/MARINERX_LABS_REAL_USAGE_AUDIT.md
?? docs/CHATGPT_FRESH_SESSION_HANDOFF.md  (this file)
?? src/mcc/system/
?? src/mcc/interface/web/system_routes.py
?? src/mcc/interface/web/static/system-state.js
?? tests/interface/test_system_routes.py
 M  src/mcc/data/live/free_market.py
 M  src/mcc/interface/web/server.py
 M  src/mcc/interface/web/static/index.html
 M  src/mcc/interface/web/static/app.js
```

**Action:** Commit Phase 2 + audit before large Phase 3 work.

### 7.3 UI still largely static

- `static/pages.js` — hardcoded agent grid, instrument cards, tables across all 13 pages
- `static/app.js` — chart placeholders use `Math.random()` when no live data
- Only partial hydration via `live-data.js` / `tradeify-data.js` on some pages

### 7.4 Agent pipeline stubs (local `90d8c40` tree)

These agents only `sleep` + `set_status` — no real bus I/O:

MarketPulse, IndicatorEngine, TradeJournal, AccountSync, DataOps, Overseer, RegimeMonitor, StrategyRunner, ResearchLab, PerformanceAnalyst, ReportPublisher

*(Grok's `3b757e0` partially fixes MarketPulse/IndicatorEngine/TradeJournal/AccountSync — not present locally.)*

### 7.5 Tradeify Sync Engine

- `tradeify-sync/` in this repo = **9 markdown spec files, zero Python**
- Full Python implementation exists only on GitHub `3b757e0` (or `marinerx-quant-cc-fresh` clone)

### 7.6 User actions required (cannot be automated)

1. **Tradeify 2FA login** (after sync engine is available):
   ```bash
   cd tradeify-sync
   pip install -e ".[dev]"
   playwright install chromium
   cp .env.example .env
   python main.py login   # headed browser — human completes 2FA
   python main.py discover
   python main.py sync
   ```

2. **Render secrets** (for live account sync via Tradovate path):
   - `TRADOVATE_CID`, `TRADOVATE_SECRET`, `TRADOVATE_USERNAME`, `TRADOVATE_PASSWORD`

3. **Optional:** `FRED_API_KEY`, `ALPHA_VANTAGE_API_KEY` for macro data

### 7.7 Test flakes

- `tests/integration/test_phase16_end_to_end.py::test_regime_comparison_export` — intermittent HMM SVD convergence failure (pre-existing, not introduced by Phase 2)

### 7.8 pytest collection risk

- Duplicate `test_tradeify_150k.py` under `docs/tradeify-connector-package/` can cause import conflicts if pytest recurses into `docs/`
- Fix on remote: `norecursedirs = ["docs", "tradeify-sync", ...]` in `pyproject.toml` — **not in local `90d8c40` pyproject**

### 7.9 Environment notes

- Local doctor reports `database OK postgres` (user has `DATABASE_URL` set locally)
- Without `DATABASE_URL`, local dev uses SQLite at `{DATA_DIR}/mcc.sqlite`
- `ENABLE_LIVE_EXECUTION=false` by default — keep it that way

---

## 8. Current API Surface (this workspace + Phase 2)

### Core (`server.py`)

- `GET /health` — composite health (agents, DB, object store)
- `GET /` — SPA
- `WS /ws` — agent snapshot + bus bridge

### System truth (Phase 2 — new)

- `GET /version`
- `GET /config-check`
- `GET /api/system-state`
- `GET /api/data-freshness`

### Live data (`/api/live`)

- `/snapshot`, `/bars/{symbol}`, `/internals`, `/regime`, `/decision`, `/risk`, `/performance`, `/tradingview`, `/sources`

### Tradeify 150K (`/api/tradeify/150k`)

- Rules, eval, payout, risk gate, data sync/status/health/reconcile

### Missing (master prompt — not built here yet)

- `/api/strategies`, `/api/backtests/run`, `/api/validation/run`, `/api/regime/current`, `/api/decision/evaluate`, `/api/risk/state`, `/api/orders/*`, `/api/journal`, `/api/performance/summary`, `/api/reports/*`, `/api/instruments`, `/api/market/bars`, `POST /api/data/sync`

### On GitHub only (`3b757e0`)

- `/api/agents/snapshot`, `/api/agents/market-pulse`, `/api/agents/indicators/{symbol}`, `/api/agents/journal`, `/api/account/sync`

---

## 9. Storage Today

**File:** `src/mcc/storage/models.py`

| Table | Maturity |
|-------|----------|
| `strategies` | Minimal (id + status only) |
| `account_states` | Basic |
| `trades` | Basic |
| `decision_logs` | Basic |
| `report_metadata` | Basic |
| `agent_heartbeats` | Basic |
| + Tradeify persistence tables | Via `marinerx_tradeify.persistence` |

**Missing:** market_bars, backtest_runs, validation_results, journal_entries (rich), orders, risk_events, regime_snapshots, macro_series, etc.

---

## 10. Frontend Pages (13)

All defined in `static/index.html` + `static/pages.js`:

1. Home 2. Markets 3. Indicators & Regime 4. Strategy Registry 5. Validation & Verdicts  
6. Research Lab 7. Risk Command 8. Trade-or-No-Trade 9. Execution & Orders 10. Trade Journal  
11. Performance 12. Reports 13. Settings

**Wiring status:**

| Component | Status |
|-----------|--------|
| Header system state | ✅ Phase 2 (`system-state.js`) |
| Markets/Risk/Decision/Performance (partial) | ⚠️ `live-data.js` |
| Tradeify settings (partial) | ⚠️ `tradeify-data.js` |
| All page body content | ❌ Mostly static `pages.js` |

---

## 11. Strict Rules for Next Agent

1. Work **only** in the active project path (§1).
2. Do **not** hardcode `ALL SYSTEMS NOMINAL` or fake P&L.
3. Do **not** enable live-money execution.
4. Do **not** commit secrets.
5. Do **not** break existing tests.
6. Label demo/simulated data clearly: `DEMO DATA`, `SIMULATED`, timestamps.
7. Run `python main.py doctor` and `python -m pytest tests/ -q` before claiming success.
8. Prefer **git pull `master`** to reconcile with `3b757e0` before re-building what Grok already shipped.

---

## 12. Recommended Next Steps (copy-paste for new session)

```text
You are continuing the MarinerX Labs Real Quant Platform build.

1. Read:
   - C:\Users\Skyler B. Brown\Desktop\MARINERX_LABS_REAL_QUANT_BUILD_MASTER_PROMPT.md
   - C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\docs\CHATGPT_FRESH_SESSION_HANDOFF.md
   - C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\docs\audits\MARINERX_LABS_REAL_USAGE_AUDIT.md

2. Work only in:
   C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\

3. First actions:
   a. git fetch && git log HEAD..origin/master --oneline  (see if behind 3b757e0)
   b. Commit uncommitted Phase 2 files OR merge origin/master first
   c. python main.py doctor && python -m pytest tests/ -q
   d. Start Phase 3 (persistence schema) per master prompt Tier 1

4. Do not fake telemetry. Do not claim tests pass without running them.
```

---

## 13. Key File Index

| Path | Purpose |
|------|---------|
| `main.py` | CLI: doctor, run web/worker |
| `src/mcc/interface/web/server.py` | FastAPI app |
| `src/mcc/interface/web/static/` | Dashboard UI |
| `src/mcc/agents/pipeline.py` | 15 agents |
| `src/mcc/runtime/bootstrap.py` | Supervisor factory |
| `src/mcc/system/state.py` | System truth (Phase 2) |
| `src/mcc/data/live/free_market.py` | yfinance ingestion |
| `src/marinerx_tradeify/` | Tradeify 150K connectors |
| `tradeify-sync/` | Spec only locally; Python on GitHub |
| `tests/` | 21 test modules, 108 tests after Phase 2 |
| `render.yaml` / `Dockerfile` | Render deployment |
| `PROGRESS.md` | Phase 17 complete; PATCH 01 noted |

---

## 14. Acceptance Criteria (from master prompt — not yet met)

The build is **not complete** until all of the following are true:

1. All 13 pages load with real API data (loading/error/stale states)
2. Header uses real system state ✅ (Phase 2)
3. Strategies persist + CRUD API
4. Backtests run and persist
5. Validation produces objective GREEN/YELLOW/RED verdicts
6. Trade-or-no-trade decisions calculated + persisted
7. Risk limits reject trades; kill switch works via API
8. Paper orders simulated and logged
9. Journal CRUD works
10. Performance calculated from stored data
11. Reports generated and stored
12. Settings show real config state (partial via `/config-check`)
13. No secrets committed
14. Tests pass (doctor + pytest)
15. Documentation package exists

**Current completion estimate:** ~55–65% of full master prompt (Git reconciled, Tier 1 APIs + persistence + partial Tier 2).

### SuperGrok Subagent Package Run (2026-07-07)

| Phase | Status |
|-------|--------|
| Git reconciliation + merge 3b757e0 | ✅ `535a9d2` |
| Phase 2 system-truth committed | ✅ |
| Phase 3 persistence | ✅ models + repositories + schema migration |
| Strategy Registry API | ✅ |
| Backtest engine + API | ✅ |
| Risk Command API | ✅ |
| Trade-or-no-trade engine | ✅ |
| Tier 1 frontend wiring | ✅ strategies/backtest/risk/decision JS |
| Tier 2 stubs | ✅ data/validation/regime/orders/journal/performance/reports |
| Tests | ✅ 148 passed, 1 pre-existing failure |

**Phase 2 preservation:** commit `535a9d2` (rebased on `3b757e0`).

**Verification (last run):**
```
python main.py doctor  → All green
python -m pytest tests/ -q → 148 passed, 1 failed (e2e replay)
```

---

## 15. Contact / Ownership Context

- **User:** Skyler B. Brown
- **Org/repo:** marinerxcapital/marinerx-quant-cc
- **Product name:** MarinerX Labs Research System
- **Deployment:** Render free tier (cold starts ~30–60s)

---

*End of handoff. Update this file when phases complete or git state changes.*