# MarinerX Labs — Codex Project Memory

**Owner:** Skyler B. Brown  
**Last updated:** 2026-07-07  
**Repo:** marinerxcapital/marinerx-quant-cc

---

## Working Directory

```
C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\
```

---

## Implementation Map

### Storage (`src/mcc/storage/`)
- `models.py` — 17+ tables
- `repositories.py` — Strategy, Backtest, Decision, Risk, Journal, Order, Report repos
- `schema.py` — lightweight ALTER TABLE migration
- `database.py` — engine singleton + `reset_engine()`
- `session.py` — `session_scope()`, `reset_session_factory()`

### Routes (`src/mcc/interface/web/`)
- `system_routes.py` — Phase 2 truth
- `agent_routes.py` — agent snapshot APIs
- `strategy_routes.py`, `backtest_routes.py`, `risk_routes.py`, `decision_routes.py`
- `platform_routes.py` — Tier 2 bundle
- `server.py` — mounts all routers

### Engines
- `src/mcc/research/backtesting.py` — deterministic ORB-style backtest
- `src/mcc/research/validation_engine.py` — verdict rules
- `src/mcc/regime/classifier.py` — vol/trend regime
- `src/mcc/risk/command.py` — kill switch, order check
- `src/mcc/decision/engine.py` — factor scoring + vetoes
- `src/mcc/data/providers.py` — demo/FRED/paper providers

### Agents (`src/mcc/agents/pipeline.py`)
- Replay fix: `_REPLAY_GREEN_METRICS` when `replay=True` on ValidationEngine
- AccountSync replay stub when DB missing

### Tests (`tests/`)
- `storage/test_research_persistence.py`
- `interface/test_strategy_routes.py`, `test_backtest_routes.py`, `test_risk_routes.py`, `test_decision_routes.py`, `test_frontend_smoke.py`
- `research/test_backtest_engine.py`
- `risk/test_risk_command.py`
- `decision/test_trade_decision_engine.py`
- `test_end_to_end_replay.py` — **FIXED** (was NO_GO veto, not timing)

### Frontend (`src/mcc/interface/web/static/`)
- `tier2-data.js` — 8 page hydrators
- `pages.js` — loading placeholder divs for API-backed content

---

## Git History (Recent)

```
8cea00c  Tier 1 quant platform
535a9d2  Phase 2 system truth
3b757e0  Tradeify sync + agent APIs
```

Pending local: Tier 2 wiring, e2e fix, login command, memory files.

---

## Deploy

- **Render:** https://marinerx-labs-api.onrender.com
- Auto-deploy on push to `master` (if Render webhook connected)
- Dockerfile in repo root

---

## CLI Commands

```powershell
python main.py doctor
python main.py run --interface web
python main.py login          # tradeify-sync headed browser + 2FA
python -m pytest tests/ -q
```

---

## Coding Rules

1. Repository pattern — no business logic in route handlers
2. SQLite tests use `memory_db` fixture in `tests/conftest.py`
3. Never hardcode NOMINAL or fake P&L in UI
4. Label demo data explicitly
5. `ENABLE_LIVE_EXECUTION=false` default

---

## Sellable Product — Engineering Gaps

| Area | Status | To Ship |
|------|--------|---------|
| Auth (OAuth/JWT) | ❌ | Required for SaaS |
| Multi-tenant DB | ❌ | Row-level tenant isolation |
| Payment (Stripe) | ❌ | Subscription tiers |
| Real market data pipeline | ⚠️ Demo only | Paid feed + ETL |
| Historical bar store | ⚠️ Schema exists | Populate + query at scale |
| Live Tradeify sync | ⚠️ Package exists | User login + cron |
| E2E browser tests | ❌ | Playwright for 13 pages |
| CI/CD gate | ⚠️ | GitHub Actions on PR |
| Rate limiting | ❌ | API protection |
| Secrets rotation | ⚠️ | Render env management |

**Estimated completion for MVP SaaS:** 4–8 weeks focused engineering  
**Estimated completion for institutional grade:** 3–6 months

---

## Related Docs

- `docs/CHATGPT_FRESH_SESSION_HANDOFF.md`
- `docs/API_REFERENCE.md`
- `docs/DATA_MODEL.md`
- `grok.md`, `claude.md` (this memory set)