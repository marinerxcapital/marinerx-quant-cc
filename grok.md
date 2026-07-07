# MarinerX Labs — Grok Project Memory

**Owner:** Skyler B. Brown  
**Last updated:** 2026-07-07  
**Authoritative workspace (ONLY):**

```
C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\
```

**Do NOT use:** `marinerx-quant-cc-fresh`, Desktop stale clones, old zip extracts.

---

## Project Identity

**MarinerX Labs Research System** — Python 3.11+ quant research OS:
- FastAPI dashboard (13 SPA pages)
- 15-agent async supervisor
- SQLite local / Postgres production
- Paper-first (live execution OFF by default)
- Deployed: https://marinerx-labs-api.onrender.com
- GitHub: https://github.com/marinerxcapital/marinerx-quant-cc (`master`)

---

## Git State (2026-07-07)

| Commit | Description |
|--------|-------------|
| `8cea00c` | Tier 1: persistence, APIs, frontend wiring, tests |
| `535a9d2` | Phase 2: system truth + data freshness |
| `3b757e0` | Tradeify sync, agent routes, dashboard APIs |

Post-session additions (local, pending push): Tier 2 page wiring, e2e replay fix, `main.py login`.

---

## Commands (always run from active path)

```powershell
cd C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc
python -m pip install -e ".[dev]"
python main.py doctor
python main.py run --interface web
python -m pytest tests/ -q
python main.py login   # Tradeify 2FA — user must complete in browser
```

**Wrong:** `uvicorn mcc.api.main:app`

---

## What Is Built

### Phase 2 — System Truth ✅
- `GET /version`, `/config-check`, `/api/system-state`, `/api/data-freshness`
- Header uses real API state (no hardcoded NOMINAL/P&L)

### Phase 3 — Persistence ✅
- 17+ SQLAlchemy tables, repositories, schema migration
- SQLite fallback, Postgres compatible

### Tier 1 APIs ✅
- Strategy Registry CRUD
- Backtest engine + `POST /api/backtests/run`
- Risk Command (kill switch, order check)
- Trade-or-no-trade `POST /api/decision/evaluate`

### Tier 2 APIs ✅
- Data: instruments, market bars, snapshot, macro, sync
- Validation, regime, paper orders, journal CRUD, performance, reports

### Frontend Wiring ✅
- Tier 1: strategies-data.js, backtest-data.js, risk-data.js, decision-data.js
- Tier 2: tier2-data.js (8 pages: market-pulse, indicators, validation, execution, journal, performance, reports, settings)

### Agent/Tradeify (3b757e0) ✅
- agent_routes.py, agent-data.js, tradeify-sync package

### Tests ✅
- 148+ passed after Tier 1; e2e replay fixed (replay GREEN metrics + fresh AccountSync stub)
- 1 known flake: HMM regime export (intermittent)

---

## Blockers / User Actions Required

1. **Tradeify live sync:** `python main.py login` — requires Skyler to complete 2FA in headed browser
2. **Render Tradovate secrets:** TRADOVATE_* env vars for live account sync in production
3. **Push to GitHub:** after local commits finalized

---

## What's Left for Sellable Product

See `claude.md` and `codex.md` § Sellable Product Gap Analysis.

High level:
- Real market data feeds (not demo yfinance only)
- Full validation/backtest on historical data stores
- Billing/auth/multi-tenant
- Production observability + SLA
- Legal/compliance packaging for prop-firm traders
- Polished onboarding + documentation site
- Mobile-responsive QA pass
- Customer support workflow

---

## Key Files

| Purpose | Path |
|---------|------|
| Handoff | `docs/CHATGPT_FRESH_SESSION_HANDOFF.md` |
| API docs | `docs/API_REFERENCE.md` |
| Data model | `docs/DATA_MODEL.md` |
| Master prompt | `C:\Users\Skyler B. Brown\Desktop\MARINERX_LABS_REAL_QUANT_BUILD_MASTER_PROMPT.md` |
| Web server | `src/mcc/interface/web/server.py` |

---

## Rules for All Agents

1. Work only in active path
2. Never fake telemetry or hardcode ALL SYSTEMS NOMINAL
3. Never claim tests pass without running doctor + pytest
4. Never enable live-money execution by default
5. Never commit secrets