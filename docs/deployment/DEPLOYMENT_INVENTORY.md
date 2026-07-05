# Deployment Inventory — MarinerX Quant Command Center

**Generated:** 2026-07-04  
**Purpose:** Repository discovery baseline for Option 1 migration (Cloudflare + Render + Postgres + R2)  
**Auditor:** Grok Build deployment migration work order

---

## 1. Repository Root

| Item | Value |
|------|-------|
| **Canonical path** | `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\` |
| **Hub path** | `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\` |
| **Package name** | `marinerx-cc` (pyproject.toml) |
| **Git remote** | `https://github.com/marinerxcapital/marinerx-quant-cc.git` |
| **Current branch** | `master` (ahead of origin) |
| **Latest commit** | `5d330f3` — Organize repo root |
| **Phase status** | Phase 17 COMPLETE — 60 tests passing |

---

## 2. Application Entrypoint

| Item | Detail |
|------|--------|
| **CLI entry** | `main.py` (Typer) |
| **Doctor** | `python main.py doctor` |
| **Web run** | `python main.py run --interface web` |
| **Worker run** | `python main.py run --interface worker` (added in migration) |
| **Packaged script** | `mcc = "main:cli"` in pyproject.toml |

### `main.py` behavior (pre-migration)

- Inserts `src/` on `sys.path`
- `doctor`: init_db, create_supervisor (15 agents), safety module imports
- `run --interface web`: bootstrap supervisor, start_all agents, patch `web_server._SUP`, uvicorn on `0.0.0.0:$PORT`
- `run --interface worker` (legacy): supervisor loop only, no HTTP (migration adds structured worker mode)

---

## 3. pyproject.toml

| Item | Detail |
|------|--------|
| **Python** | `>=3.11` |
| **Key deps** | FastAPI, uvicorn, SQLAlchemy, duckdb, pandas, polars, riskfolio-lib, quantstats, statsmodels, scikit-learn, seaborn, typer, structlog |
| **Dev deps** | pytest, pytest-asyncio, ruff, mypy |
| **No requirements.txt** | Install via `pip install -e ".[dev]"` or `uv sync` |
| **pytest** | `asyncio_mode = auto`, `pythonpath = ["src"]` |

---

## 4. Docker / Railway (Current)

| File | Behavior |
|------|----------|
| `Dockerfile` | Multi-stage Python 3.11-slim; `pip install .`; `PORT=8080`; HEALTHCHECK on `/health`; CMD `python main.py run --interface web` |
| `railway.json` | Docker builder; startCommand `python main.py run --interface web`; restart ON_FAILURE |
| **Production URL** | https://marinerx-quant-cc-production.up.railway.app/ |
| **Hard-coded Railway URLs** | None in Python source; references in docs only |
| **PORT handling** | `os.environ.get("PORT", "8000")` in main.py (Docker sets 8080) |

---

## 5. Health / API / WebSocket

| Endpoint | Location | Behavior |
|----------|----------|----------|
| `GET /health` | `src/mcc/interface/web/server.py` | Agent snapshot; creates supervisor if `_SUP` unset |
| `GET /` | same | Serves `static/index.html` (Phase 15 SPA) or fallback inline dashboard |
| `WS /ws` | same | Agent snapshot + bus event bridge |
| **Static assets** | `src/mcc/interface/web/static/` | index.html, app.js, app.css, pages.js, design-tokens.css |
| **CORS** | Not configured (migration adds env-driven CORS) |
| **Frontend build** | No separate npm build — static files served by FastAPI (Mode A) |

---

## 6. Runtime Architecture

| Component | Path |
|-----------|------|
| Supervisor | `src/mcc/core/supervisor.py` |
| Bootstrap | `src/mcc/runtime/bootstrap.py` — registers 15 agents |
| Agent pipeline | `src/mcc/agents/pipeline.py` |
| Message bus | `src/mcc/core/bus.py` (in-process pub/sub) |
| Events | `src/mcc/core/events.py` |
| Config (new) | `src/mcc/core/config.py` |

### 15 runtime agent names (bootstrap.py)

Overseer, DataOps, AccountSync, MarketPulse, IndicatorEngine, RegimeMonitor, StrategyRunner, ValidationEngine, ResearchLab, RiskCommand, DecisionEngine, ExecutionGateway, TradeJournal, PerformanceAnalyst, ReportPublisher

---

## 7. Storage Layer (Pre-Migration)

| Layer | Path | State |
|-------|------|-------|
| Relational | `src/mcc/storage/relational.py` | SQLAlchemy; sqlite in-memory default; tables: strategies, account_states, trades |
| Analytical | `src/mcc/storage/analytical.py` | DuckDB |
| Buffers | `src/mcc/storage/buffers.py` | Ring buffers |
| **SQLite path** | Default `sqlite:///:memory:` in init_db | No persistent local path wired |
| **DuckDB** | Via analytical module | Local |
| **Parquet** | Spec in master brief under `data/parquet` | Not centrally configured |
| **Reports** | `reports_out/` at repo root | diagnostics, tear_sheets, allocations |

---

## 8. Environment Variables (Pre-Migration)

| Variable | Used? |
|----------|-------|
| `PORT` | Yes — main.py, Dockerfile |
| `DATABASE_URL` | No — not wired pre-migration |
| `.env` / `.env.example` | Missing pre-migration |
| Secrets in repo | None committed |

---

## 9. Tradeify-Related Paths

| Path | Type | Cloud risk |
|------|------|------------|
| `tradeify-sync/` | 9 markdown spec files only | Low — no Python automation in repo |
| `src/mcc/data/accounts/sync_adapter.py` | Read-only consumer adapter | Medium — must not invoke browser automation |
| Master brief `00B_PRE_FLIGHT_ADDENDUM.md` | Documents Playwright on Railway as optional | **Policy override: local-only per migration work order** |
| Playwright in Dockerfile | **Not present** | Safe |

No Playwright imports found in `src/mcc/`.

---

## 10. Safety-Critical Modules

| Module | Path | Gate |
|--------|------|------|
| Strategy lifecycle | `src/mcc/strategy/lifecycle.py` | GREEN requires passing verdict |
| Execution guardrails | `src/mcc/execution/guardrails.py` | Blocks non-GREEN, risk veto |
| Decision engine | `src/mcc/decision/engine.py` | Hard vetoes → NO_GO |
| Exceptions | `src/mcc/core/exceptions.py` | ExecutionBlocked, RiskVeto |

`ENABLE_LIVE_EXECUTION` not present pre-migration — added in migration config (defaults false).

---

## 11. Tests

| Item | Value |
|------|-------|
| **Command** | `python -m pytest tests/ -q` |
| **Count** | 60 passing (12 modules) |
| **Safety tests** | `tests/test_safety_gates.py` |
| **E2E replay** | `tests/test_end_to_end_replay.py` |
| **CI config** | None in repo (.github/workflows not present) |

---

## 12. Worktrees

| Path | Purpose |
|------|---------|
| `wt/` | 15 git worktrees for per-agent isolation |
| **Note** | Untracked in git status; Phase 17 work in main tree |

---

## 13. Spec Package

| Path | Contents |
|------|----------|
| `command-center/` | `00_MASTER_BRIEF.md` through `15_UI_MATCH_AND_RAILWAY_DEPLOY.md` |
| `docs/phase_16/`, `docs/phase_17/` | Phase documentation |

---

## 14. Migration Gaps Identified

| Gap | Migration action |
|-----|------------------|
| No centralized config | Add `src/mcc/core/config.py` |
| No DATABASE_URL support | Add `src/mcc/storage/database.py` + Postgres |
| No object storage abstraction | Add `src/mcc/storage/object_store.py` + R2 |
| No worker service mode | Extend `main.py` `--interface worker` |
| No CORS | Add to FastAPI server |
| Health check minimal | Extend `/health` with db/storage/env |
| No `.env.example` | Create |
| No Render config | Create `render.yaml` |
| Railway-only deploy docs | Add Render/Cloudflare/R2 docs + Railway fallback |
| Tradeify cloud guard | Add `CloudTradeifyAutomationBlockedError` + guard |

---

## 15. Frontend Deployment Mode

**Current:** Mode A — FastAPI serves static SPA from `src/mcc/interface/web/static/`.

**Target:** Mode B documented for Cloudflare Pages extraction after backend stabilization on Render. Not forced in this migration (per work order §12).

---

*Inventory complete. Implementation may proceed.*