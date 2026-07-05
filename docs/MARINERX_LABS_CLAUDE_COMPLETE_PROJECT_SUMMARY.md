# MarinerX Labs — Complete Project Summary for Claude

**Document purpose:** Single authoritative handoff for Claude Code / Claude.ai when continuing work on MarinerX Quant Command Center (MCC). Covers what exists, what is true today, what is stale, deployment migration status, known bugs, and safe operating rules.

**Prepared:** 2026-07-05  
**Owner:** Skyler B. Brown  
**Product:** MarinerX Quant Command Center (MCC)  
**Organization:** MarinerX Capital

**This file location:**
`C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\04_DOCUMENTATION\MARINERX_LABS_CLAUDE_COMPLETE_PROJECT_SUMMARY.md`

**Companion docs (do not replace this file):**
- General AI reference: `MARINERX_LABS_COMPLETE_REFERENCE.md` (v1.1, 2026-07-04 — partly stale on tests/deployment)
- Audit report: `MARINERX_LABS_AUDIT_REPORT.md`
- **Stale — do not use as primary:** `MarinerX_Quant_CC_Complete_Build_Status_for_Claude.md` (Phase 13/14 era, wrong paths)
- Live deployment tracker: `01_ACTIVE_PROJECT/marinerx-quant-cc/docs/deployment/SETUP_STATUS.md`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [What to Read First](#2-what-to-read-first)
3. [Canonical Paths (Use These Only)](#3-canonical-paths-use-these-only)
4. [Stale Paths and Claims to Reject](#4-stale-paths-and-claims-to-reject)
5. [What MarinerX Labs Is](#5-what-marinerx-labs-is)
6. [Mission and Governing Principles (P1 / P2 / P3)](#6-mission-and-governing-principles-p1--p2--p3)
7. [15-Agent Architecture](#7-15-agent-architecture)
8. [Hub Layout](#8-hub-layout)
9. [Active Codebase Structure](#9-active-codebase-structure)
10. [Technology Stack](#10-technology-stack)
11. [Phase History and Current Build Status](#11-phase-history-and-current-build-status)
12. [Testing (Verified Live)](#12-testing-verified-live)
13. [Safety Spine and Known Code Gaps](#13-safety-spine-and-known-code-gaps)
14. [UI / Frontend (Phase 15)](#14-ui--frontend-phase-15)
15. [Research Stack (Phases 16–17)](#15-research-stack-phases-1617)
16. [Deployment: Current State (Option 1 Migration)](#16-deployment-current-state-option-1-migration)
17. [Environment Variables and Secrets](#17-environment-variables-and-secrets)
18. [How to Run Locally](#18-how-to-run-locally)
19. [How Claude Should Work on This Project](#19-how-claude-should-work-on-this-project)
20. [Immediate Next Actions (Human + Agent)](#20-immediate-next-actions-human--agent)
21. [Glossary](#21-glossary)
22. [Quick Reference Tables](#22-quick-reference-tables)

---

## 1. Executive Summary

**MarinerX Labs** is Skyler B. Brown's organized Desktop hub for **MarinerX Quant Command Center (MCC)** — a validation-first, risk-first quantitative trading operating system for futures (primarily NQ, ES, CL, GC).

### Truth table as of 2026-07-05

| Item | Value |
|------|-------|
| **Build phase** | Phase 17 COMPLETE (gate PASS) |
| **Post-17 work** | Option 1 deployment migration (Cloudflare + Render + Neon + R2) — **in progress** |
| **Automated tests** | **70 passing** (verified live 2026-07-05: `70 passed in 41.27s`) |
| **Tests at Phase 17 gate** | 60 passing (10 deployment tests added in migration) |
| **GitHub** | https://github.com/marinerxcapital/marinerx-quant-cc.git |
| **Git HEAD** | `43e58db` — `deploy: Render blueprint env groups + R2/Render combined setup script` |
| **Canonical local path** | `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\` |
| **Railway (fallback, live)** | https://marinerx-quant-cc-production.up.railway.app/ — **older code**, do not delete until Render passes |
| **Render (target)** | Blueprint prepared (`render.yaml`), **not yet applied** in dashboard |
| **Neon Postgres** | **DONE** — project `summer-star-19798293`, branch `production` |
| **Cloudflare R2** | **BLOCKED** — error `10042`, must enable in dashboard |
| **Docker local smoke** | **BLOCKED** — Docker Desktop not installed |
| **Live execution** | **DISABLED** by default (`ENABLE_LIVE_EXECUTION=false`) |

MCC is an **evolving platform**, not a finished product. The master brief describes the full aspirational system; implementation is phase-progressive. Many modules are specified but not yet in the main `src/mcc/` tree.

---

## 2. What to Read First

When resuming work, read in this order:

1. **This file** — current truth for Claude
2. `01_ACTIVE_PROJECT/marinerx-quant-cc/PROGRESS.md` — phase tracker (ends at Phase 17; does not mention deployment migration)
3. `01_ACTIVE_PROJECT/marinerx-quant-cc/docs/deployment/SETUP_STATUS.md` — live deployment step tracker
4. `01_ACTIVE_PROJECT/marinerx-quant-cc/command-center/00_MASTER_BRIEF.md` — constitutional spec (aspirational)
5. `04_DOCUMENTATION/FOLDER_MAP.txt` — hub directory map

Before claiming anything about tests or deployment, run:

```powershell
cd "C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc"
python -m pytest tests/ -q
python main.py doctor
```

---

## 3. Canonical Paths (Use These Only)

| What | Path |
|------|------|
| Hub root | `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\` |
| **Active codebase** | `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\` |
| Master brief | `...\marinerx-quant-cc\command-center\00_MASTER_BRIEF.md` |
| Python package | `...\marinerx-quant-cc\src\mcc\` |
| Tests | `...\marinerx-quant-cc\tests\` |
| Web UI static | `...\marinerx-quant-cc\src\mcc\interface\web\static\` |
| Web server | `...\marinerx-quant-cc\src\mcc\interface\web\server.py` |
| CLI entry | `...\marinerx-quant-cc\main.py` |
| Deployment docs | `...\marinerx-quant-cc\docs\deployment\` |
| Render blueprint | `...\marinerx-quant-cc\render.yaml` |
| Phase evidence (hub) | `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\06_DEPLOYMENT_AND_OPS\evidence\` |
| UI design handoff | `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\05_UI_DESIGN_AND_MOCKUPS\UI_Match_Package\` |
| This document | `C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\04_DOCUMENTATION\MARINERX_LABS_CLAUDE_COMPLETE_PROJECT_SUMMARY.md` |

**Rule:** All development happens in `01_ACTIVE_PROJECT\marinerx-quant-cc\` (or an appropriate `wt/` worktree). Never edit archived build variants unless explicitly asked.

---

## 4. Stale Paths and Claims to Reject

| Wrong | Correct |
|-------|---------|
| `Desktop\MarinerX_SuperGrok_Build\` as active code | Use `MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\` |
| `MarinerX_Quant_CC_Complete_Build_Status_for_Claude.md` as primary | Use **this file** |
| "11 tests passing" or "60 tests" without verification | **70 tests** as of migration (run pytest to confirm) |
| `src/mcc/api/` exists | Use `src/mcc/interface/web/` |
| `uvicorn mcc.api.main:app` | `python main.py run --interface web` |
| `requirements.txt` | `pyproject.toml` — `pip install -e ".[dev]"` or `uv sync` |
| `railway.toml` | `railway.json` (Railway fallback only) |
| Agent names like DataAgent, ValidationAgent | Runtime names: **DataOps, ValidationEngine, DecisionEngine**, etc. |
| `internals/`, `journal/`, `indicators/` exist in main tree | **Not in main tree** — may exist as worktree scaffolds |
| tradeify-sync is implemented Python | **9 markdown specs only** at `tradeify-sync/` |
| Railway has latest migration code | Railway is **fallback** with older deploy; Render is target |
| `PROGRESS.md` mentions deployment migration | It does not — check `docs/deployment/SETUP_STATUS.md` |
| Execution is fully live | `ENABLE_LIVE_EXECUTION=false` by default; paper/replay only |

---

## 5. What MarinerX Labs Is

### What it IS

- A **folder-based program office** grouping active code, archives, docs, UI assets, and deployment evidence
- The **home of MCC** — quant research + operational command center for futures trading discipline
- A **phase-gated build program** (Phases 0–17 documented) with pytest evidence and phase gate files
- A **Git-backed deployable service** (Railway today; migrating to Render + Neon + R2)

### What it is NOT

- **Not** the stale `Desktop\MarinerX_SuperGrok_Build\` folder (archived to `02_BUILD_VARIANTS\Stale_Desktop_SuperGrok_Build\`)
- **Not** a live broker-connected execution system (ExecutionGateway has guardrails + paper path; live stub inert by default)
- **Not** tradeify-sync as implemented Python (spec-only markdown)
- **Not** fully aligned with every line of the master brief — spec is constitutional; implementation is phase-progressive

---

## 6. Mission and Governing Principles (P1 / P2 / P3)

**Source:** `command-center/00_MASTER_BRIEF.md`

### Mission

Build a **validation-first, risk-first** quant command center — single hub for trading: data, market internals, heatmaps, indicators, regime detection, strategy engineering, validation, quant/ML research, risk, Trade-or-No-Trade decisions, execution (paper-first), journaling, reporting, real-time interface, and production deployment.

### The Three Principles

| Principle | Name | Enforcement |
|-----------|------|-------------|
| **P1** | Validation-first | Strategy lifecycle `DRAFT → REGISTERED → TESTED → GREEN/YELLOW/RED`; execution gateway raises if `status != GREEN` |
| **P2** | Risk-first | RiskCommand / PropGuardian vetoes override signals; DecisionEngine forced to NO-GO on risk veto |
| **P3** | Honest forecasting | Models scored vs naive baseline; models that don't beat baseline labeled `NO_SIGNAL` and cannot feed decision engine |

Phase 17 extends P3 with VIF, joint F-tests, and statistical vs economic significance splits.

---

## 7. 15-Agent Architecture

**Spec:** `command-center/00_MASTER_BRIEF.md` §5  
**Runtime:** `src/mcc/runtime/bootstrap.py` → `src/mcc/agents/pipeline.py`

Each agent is both a runtime async service and a build-subagent identity.

| # | Runtime name | Brief responsibility | Owns (`src/mcc/`) | Status |
|---|--------------|---------------------|-------------------|--------|
| 1 | **Overseer** | Supervisor, kill-switch, health | `core/`, `agents/` | Wired |
| 2 | **DataOps** | Historical/live feeds, calendar | `data/historical/`, `data/live/`, `data/calendar/` | Partial |
| 3 | **AccountSync** | Tradeify Sync output reader | `data/accounts/` | Partial |
| 4 | **MarketPulse** | Internals, microstructure, heatmaps | `internals/`, `microstructure/`, `heatmaps/` | **Missing** — NoOp/minimal |
| 5 | **IndicatorEngine** | Indicator library + engine | `indicators/` | **Missing** — NoOp/minimal |
| 6 | **RegimeMonitor** | HMM + volatility regime | `regime/` | Partial |
| 7 | **StrategyRunner** | Strategy lifecycle, registry | `strategy/` | Partial |
| 8 | **ValidationEngine** | Backtest + validation gauntlet | `backtest/`, `validation/` | Partial |
| 9 | **ResearchLab** | Features + honest forecasting | `research/` | Partial (Phase 17) |
| 10 | **RiskCommand** | Sizing, VaR/ES, PropGuardian | `risk/` | Partial |
| 11 | **DecisionEngine** | Trade-or-No-Trade GO/NO-GO | `decision/` | Implemented |
| 12 | **ExecutionGateway** | Guardrails, paper, live stub | `execution/` | Partial — guardrails tested |
| 13 | **TradeJournal** | Fill ingestion, tagging | `journal/` | **Missing** — NoOp/minimal |
| 14 | **PerformanceAnalyst** | Equity/Sharpe/drawdown analytics | `performance/` | Partial (Phase 16) |
| 15 | **ReportPublisher** | PDF/HTML reports | `reports/` | Partial (Phase 17) |

### Safety spine (actively wired)

```
BAR event → ValidationEngine (verdict) → LOG → DecisionEngine (decide) → DecisionEvent
                                                      ↓
                                            ExecutionGateway (guardrails)
```

Core safety modules: `validation/verdict.py`, `decision/engine.py`, `execution/guardrails.py`, `strategy/lifecycle.py`.

---

## 8. Hub Layout

```
MarinerX_Labs/
├── 01_ACTIVE_PROJECT/
│   └── marinerx-quant-cc/          ★ ONLY active codebase
├── 02_BUILD_VARIANTS/              Archives (Build_Original, Build_Clean, Stale SuperGrok)
├── 03_PACKAGES_AND_ARCHIVES/       Phase zip packages and work orders
├── 04_DOCUMENTATION/               This file + reference docs
├── 05_UI_DESIGN_AND_MOCKUPS/       Phase 15 UI handoff + approved PNGs
└── 06_DEPLOYMENT_AND_OPS/          Synced PROGRESS, evidence, pytest logs
```

---

## 9. Active Codebase Structure

```
marinerx-quant-cc/
├── main.py                         # Typer CLI: doctor, run --interface web|worker
├── pyproject.toml                  # Dependencies (no requirements.txt)
├── Dockerfile                      # Multi-stage, PORT=8080, HEALTHCHECK /health
├── railway.json                    # Railway fallback config
├── render.yaml                     # Render Blueprint (web + worker)
├── command-center/                 # Phase 00–15 specs
├── tradeify-sync/                  # 9 markdown spec files (no Python)
├── src/mcc/                        # Main Python package
├── tests/                          # 15 test modules, 70 tests
├── docs/phase_16/, docs/phase_17/
├── docs/deployment/                # Option 1 migration runbooks
├── reports_out/                      # tear_sheets, allocations, diagnostics
├── wt/                             # 15 git worktrees (per-agent isolation)
├── PROGRESS.md                     # Phase 17 COMPLETE (no deployment section)
└── README.md
```

### `src/mcc/` module map (main tree)

| Package | Key files | Status |
|---------|-----------|--------|
| `agents/` | `pipeline.py`, `registry.py` | 15 roster agents |
| `analytics/` | `validation.py`, `conversion.py`, `benchmark.py` | Implemented |
| `backtest/` | `costs.py` | Phase 17 |
| `core/` | `supervisor.py`, `bus.py`, `base_agent.py`, `clock.py`, `events.py`, `config.py` | Core infra |
| `data/` | `historical/`, `live/`, `calendar/`, `accounts/` | Partial |
| `decision/` | `engine.py` | Implemented |
| `execution/` | `guardrails.py` | Implemented |
| `interface/web/` | `server.py`, `static/` | FastAPI + Phase 15 SPA |
| `performance/` | `analytics.py`, `quantstats_adapter.py` | Phase 16 |
| `regime/` | `hmm.py`, `volatility_regime.py` | Partial |
| `reports/` | `generator.py` | Phase 17 |
| `research/` | `forecast_lab.py`, `stat_models.py` | Phase 17 |
| `risk/` | `sizing.py`, `var_es.py`, `portfolio.py`, `prop_guardian.py`, `riskfolio_adapter.py`, `monitor.py` | Partial |
| `runtime/` | `bootstrap.py` | Supervisor factory |
| `storage/` | `relational.py`, `analytical.py`, `buffers.py`, `database.py`, `object_store.py` | Implemented + migration additions |

### Modules in master brief but MISSING from main tree

- `internals/` — TICK/TRIN/ADD breadth
- `microstructure/` — CVD, OBI, volume profile
- `heatmaps/` — orderbook, correlation, volatility, sector
- `indicators/` — library + engine
- `journal/` — trade journal

These may exist as worktree scaffolds under `wt/` but are **not** in the main `src/mcc/` tree.

---

## 10. Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Packaging | `pyproject.toml`, uv-compatible |
| CLI | Typer (`main.py`) |
| API / Web | FastAPI + Uvicorn |
| Async core | asyncio + in-process MessageBus |
| Data | pandas, polars, numpy, scipy |
| Analytical store | duckdb |
| Relational state | SQLAlchemy + aiosqlite (local) / psycopg + Neon (production) |
| Object storage | Local filesystem (local) / Cloudflare R2 (production target) |
| Statistics | statsmodels |
| Portfolio risk | Riskfolio-Lib |
| Performance analytics | QuantStats |
| ML / forecast | scikit-learn (IsolationForest, PCA, RandomForest) |
| Visualization | Seaborn, Matplotlib, Plotly |
| Tests | pytest, pytest-asyncio, ruff, mypy |
| Deploy (current) | Docker, Railway (fallback) |
| Deploy (target) | Render (web + worker), Neon Postgres, Cloudflare R2 |

---

## 11. Phase History and Current Build Status

| Phase | Focus | Status |
|-------|-------|--------|
| 00 | Master brief constitution | Spec in `command-center/` |
| 01 | Core infra (Overseer, bus, supervisor) | Complete |
| 02 | Data layer (DataOps, AccountSync) | Partial |
| 03–04 | Internals, indicators, regime | Regime partial; internals/indicators missing |
| 05–06 | Strategy, validation gauntlet | Verdict + lifecycle partial |
| 07 | Research lab | Extended in Phase 17 |
| 08 | Risk engine | Partial — riskfolio Phase 16 |
| 09–10 | Decision + execution | Decision + guardrails implemented |
| 11 | Journal, perf, reports | Performance partial; journal missing |
| 12 | Interface (web + TUI) | Web SPA Phase 15 |
| 13 | Tests / acceptance | Ongoing |
| 14 | Railway deployment | PASS (fallback still live) |
| 15 | UI match + light theme | Complete — 13-page SPA |
| 16 | Riskfolio, QuantStats, statsmodels | **COMPLETE** |
| 17 | Forecast lab, stat rigor, Seaborn | **COMPLETE** — gate PASS |
| **Post-17** | Option 1 infra migration | **IN PROGRESS** |

**Source of truth for phases:** `PROGRESS.md` → `Status: PHASE 17 COMPLETE — gate PASS`

**Source of truth for deployment:** `docs/deployment/SETUP_STATUS.md`

### Recent git history (migration)

```
43e58db deploy: Render blueprint env groups + R2/Render combined setup script
01b67da chore: commit Neon project link (.neon)
6b20ab6 feat: wire Neon Postgres (psycopg, URL normalize, project link)
dee5ac8 docs: add deployment setup status tracker
a280475 deploy: migrate infrastructure to cloudflare render postgres r2
cf2f3b1 Phase 17 - tests docs evidence 60 passed - gate PASS
```

---

## 12. Testing (Verified Live)

### Run tests

```powershell
cd "C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc"
python -m pytest tests/ -q
# Expected: 70 passed
```

**Verified 2026-07-05:** `70 passed, 27 warnings in 41.27s`

### Test modules (15 files)

| Module | Covers |
|--------|--------|
| `test_safety_gates.py` | P1/P2 safety spine |
| `test_end_to_end_replay.py` | BAR → verdict → decide flow |
| `analytics/test_validation.py`, `test_conversion.py` | Analytics |
| `performance/test_quantstats_adapter.py` | QuantStats |
| `risk/test_riskfolio_adapter.py` | Riskfolio |
| `regime/test_hmm_statsmodels.py` | Regime |
| `research/test_stat_models_extended.py` | Stat models |
| `research/test_stat_models_rigor.py` | VIF, F-test, costs |
| `research/test_forecast_lab_extended.py` | IF, PCA, RF |
| `reports/test_generator_styling.py` | Seaborn reports |
| `integration/test_phase16_end_to_end.py` | Phase 16 integration |
| `deployment/test_config.py` | Deployment config |
| `deployment/test_object_store.py` | Object storage backends |
| `deployment/test_tradeify_guard.py` | Tradeify local-only guard |

**Gate culture:** Evidence in `06_DEPLOYMENT_AND_OPS/evidence/phase_gates/` and `pytest_logs/`.

---

## 13. Safety Spine and Known Code Gaps

### What works

- `decision/engine.py` — `decide()` correctly hard-vetoes on `risk_veto=True`
- `execution/guardrails.py` — `check_pre_trade()` blocks non-GREEN and risk veto
- `strategy/lifecycle.py` — GREEN only via passing verdict (P1)
- Unit tests in `test_safety_gates.py` cover veto paths

### Known gap: P2 not fully wired in pipeline (Priority 2)

In `src/mcc/agents/pipeline.py`, the replay spine **hardcodes** `risk_veto=False`:

```python
# DecisionEngineAgent._listen (line ~78)
risk_veto = False  # integrated from RiskCommandAgent in full flow (veto events)
d = decide(has_green_strategy=has_green, risk_veto=risk_veto)

# ExecutionGatewayAgent._listen (line ~119)
check_pre_trade(StrategyStatus.GREEN, risk_veto=False, size_ok=True)
```

**Impact:** RiskCommand / PropGuardian modules exist (`risk/monitor.py`, `get_risk_veto()`) but are **not subscribed** into the live BAR→verdict→decide→execute bus flow. P2 is enforced in unit tests and module APIs, not end-to-end in pipeline replay.

**Documented in:** `docs/deployment/EXECUTION_SAFETY_AUDIT.md`

**Fix direction:** Subscribe DecisionEngine to RiskCommand veto events (or call `get_risk_veto()` from monitor state) before `decide()`. Add integration test proving LOCKOUT forces NO_GO through pipeline.

### Live execution guard

- `ENABLE_LIVE_EXECUTION=false` by default in all deployment configs
- Tradeify sync is **local-only** per `docs/deployment/TRADEIFY_LOCAL_ONLY_POLICY.md`
- Do not enable live execution without explicit human approval and full audit

---

## 14. UI / Frontend (Phase 15)

| Item | Detail |
|------|--------|
| Theme | Light, professional quant dashboard |
| Pages | 13 navigable views |
| Location | `src/mcc/interface/web/static/` |
| Entry | `static/index.html` |
| Mock data | `static/pages.js` — **not live API-fed** |
| Design handoff | `05_UI_DESIGN_AND_MOCKUPS/UI_Match_Package/` |

Distinguish **"UI shell with mock data"** from **"live operational dashboard fed by bus events."**

---

## 15. Research Stack (Phases 16–17)

### Phase 16

- `performance/analytics.py`, `quantstats_adapter.py`
- `risk/riskfolio_adapter.py`
- `regime/hmm.py`, `volatility_regime.py`
- `research/stat_models.py`

### Phase 17

- `research/forecast_lab.py` — Isolation Forest, PCA, Random Forest (P3 baseline discipline)
- `research/stat_models.py` — VIF, joint F-test, statistical vs economic significance
- `backtest/costs.py` — economic significance pairing
- `reports/generator.py` — Seaborn styling, outputs to `reports_out/diagnostics/`

**Evidence:** `reports_out/diagnostics/phase17_evidence.json`, `phase17_chart.png`, `PHASE17_FORECAST_RIGOR.txt`

---

## 16. Deployment: Current State (Option 1 Migration)

**Strategy:** Migrate from Railway-only to **Render (web + worker) + Neon Postgres + Cloudflare R2**. Keep Railway as fallback until Render smoke passes.

### Status matrix

| Component | Status | Notes |
|-----------|--------|-------|
| Code migration | **DONE** | Commit `a280475` |
| GitHub push | **DONE** | HEAD `43e58db` on `master` |
| Local pytest (70) | **DONE** | Verified |
| Local doctor | **DONE** | All green, live execution DISABLED |
| Local web smoke | **DONE** | `/health` ok, 15 agents |
| Neon Postgres | **DONE** | Project `summer-star-19798293`, `.neon` linked, `.env` has `DATABASE_URL` |
| Wrangler / Cloudflare auth | **DONE** | Account MarinerX Capital |
| Cloudflare R2 | **BLOCKED** | Error `10042` — enable in dashboard |
| Render Blueprint | **IN PROGRESS** | `render.yaml` ready, not applied |
| Docker local smoke | **BLOCKED** | Docker Desktop not installed |
| Railway fallback | **ACTIVE** | https://marinerx-quant-cc-production.up.railway.app/ |

### Render blueprint (`render.yaml`)

Creates two services from `marinerxcapital/marinerx-quant-cc` on `master`:

| Service | Type | Command |
|---------|------|---------|
| `marinerx-labs-api` | web (Docker) | `python main.py run --interface web` |
| `marinerx-labs-worker` | worker (Docker) | `python main.py run --interface worker` |

Secrets via env group `marinerx-production-secrets`: `DATABASE_URL`, `R2_*`, CORS/URL vars.

**Apply:** Render Dashboard → New → Blueprint → connect repo → set secrets when prompted.

**Post-deploy smoke:**
```bash
curl https://marinerx-labs-api.onrender.com/health
```

### Neon Postgres

| Item | Value |
|------|-------|
| Org | MarinerX Labs (`org-square-wave-40095229`) |
| Project | MarinerX Labs (`summer-star-19798293`) |
| Branch | `production` |
| Region | `aws-us-east-1` |
| Local link | `.neon` in repo root |

Refresh local env:
```powershell
npx neonctl@latest checkout production
npx neonctl@latest env pull --file .env
```

### R2 (blocked — human action required)

1. Open Cloudflare R2 dashboard for account `b31d3d49151af98fe1125aa40c5fa6c8`
2. Click **Enable R2**
3. Create bucket `marinerx-mcc-prod`
4. Create API token (Object Read & Write)
5. Set `R2_*` env vars on Render (never commit)

See `docs/deployment/RENDER_R2_COMBINED_SETUP.md` for full steps.

### Railway fallback

- URL: https://marinerx-quant-cc-production.up.railway.app/
- Config: `railway.json` + `Dockerfile`
- **Do not delete** until Render health check passes
- See `docs/deployment/RAILWAY_FALLBACK_PLAN.md`

### Deployment doc index

All under `docs/deployment/`:

- `SETUP_STATUS.md` — live step tracker (update as steps complete)
- `PRODUCTION_DEPLOYMENT_RUNBOOK.md`
- `ENVIRONMENT_VARIABLES.md`
- `DATABASE_MIGRATION.md`
- `R2_STORAGE.md`
- `RENDER_WEB_SERVICE.md`, `RENDER_WORKER.md`
- `EXECUTION_SAFETY_AUDIT.md`
- `TRADEIFY_LOCAL_ONLY_POLICY.md`

---

## 17. Environment Variables and Secrets

**Never commit secrets.** Use `.env` locally (gitignored) and Render/Neon dashboards for production.

Key variables (see `ENVIRONMENT_VARIABLES.md` for full list):

| Variable | Purpose |
|----------|---------|
| `APP_ENV` | `local` / `production` |
| `SERVICE_MODE` | `web` / `worker` |
| `PORT` | HTTP port (8080 in Docker/Render) |
| `DATABASE_URL` | Neon Postgres (pooled) in production |
| `ENABLE_LIVE_EXECUTION` | Must stay `false` unless explicitly approved |
| `OBJECT_STORAGE_BACKEND` | `local` or `r2` |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` | Cloudflare R2 |
| `CORS_ALLOWED_ORIGINS`, `PUBLIC_FRONTEND_URL`, `BACKEND_PUBLIC_URL` | Frontend integration |

---

## 18. How to Run Locally

```powershell
cd "C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc"

# Install
pip install -e ".[dev]"
# or: uv sync

# Pull Neon env (if using Postgres locally)
npx neonctl@latest env pull --file .env

# Health check
python main.py doctor

# Tests
python -m pytest tests/ -q

# Web dashboard (supervisor + FastAPI)
python main.py run --interface web

# Worker mode (no HTTP)
python main.py run --interface worker
```

Open the URL printed by the server (typically `http://localhost:8000`).

---

## 19. How Claude Should Work on This Project

### Do

1. **Work only** in `01_ACTIVE_PROJECT/marinerx-quant-cc/` unless asked otherwise
2. **Read** `PROGRESS.md`, `SETUP_STATUS.md`, and `00_MASTER_BRIEF.md` before large changes
3. **Run** `python main.py doctor` and `pytest` before claiming PASS
4. **Follow P1 → P2 → P3** for any forecast or strategy code
5. **Add tests** for every new module
6. **Update** `docs/deployment/SETUP_STATUS.md` when completing deployment steps
7. **Use** `python main.py` commands — not generic uvicorn paths
8. **Distinguish** spec (`command-center/`) from implementation (`src/mcc/`)
9. **Respect** `ENABLE_LIVE_EXECUTION=false` and Tradeify local-only policy
10. **Verify paths** against `04_DOCUMENTATION/FOLDER_MAP.txt`

### Do not

1. Reference `MarinerX_SuperGrok_Build` or stale Claude build status doc as truth
2. Claim modules exist without checking `src/mcc/`
3. Enable live execution or commit secrets
4. Delete Railway before Render smoke passes
5. Assume UI `pages.js` data is live backend data
6. Skip tests or doctor after substantive changes

### Suggested Claude session startup

```powershell
cd "C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc"
git status
git log --oneline -3
python main.py doctor
python -m pytest tests/ -q
```

Then read `docs/deployment/SETUP_STATUS.md` for the next incomplete deployment step.

---

## 20. Immediate Next Actions (Human + Agent)

### Human-required (blocked)

| # | Action | Owner |
|---|--------|-------|
| 1 | Enable Cloudflare R2 in dashboard (fix error `10042`) | Human |
| 2 | Create R2 bucket `marinerx-mcc-prod` + API token | Human |
| 3 | Apply Render Blueprint + set secret env vars | Human |
| 4 | Install Docker Desktop (optional local smoke) | Human |

### Agent-can-do (after human unblocks)

| # | Action |
|---|--------|
| 1 | Update `SETUP_STATUS.md` as each step completes |
| 2 | Wire `risk_veto` from RiskCommand into `pipeline.py` (P2 gap) |
| 3 | Add integration test for pipeline risk veto |
| 4 | Sync `PROGRESS.md` with deployment migration section |
| 5 | Run Render post-deploy smoke and document in `DEPLOYMENT_VERIFICATION.md` |
| 6 | Build missing modules per master brief (internals, indicators, journal) — phase-gated |

### Post-Render activation checklist

1. `curl` Render `/health` — expect `status: ok`, `live_execution_enabled: false`
2. Verify `database.status: ok` (Neon)
3. Verify object storage when R2 enabled
4. Keep Railway running until Render stable for 48h
5. Review `EXECUTION_SAFETY_AUDIT.md` before any live execution discussion

---

## 21. Glossary

| Term | Definition |
|------|------------|
| **MCC** | MarinerX Quant Command Center |
| **Hub** | `MarinerX_Labs/` folder on Desktop |
| **Active repo** | `marinerx-quant-cc` under `01_ACTIVE_PROJECT/` |
| **command-center/** | In-repo spec package (master brief + phases 01–15) |
| **Phase gate** | Acceptance checkpoint with tests + evidence file |
| **P1/P2/P3** | Validation-first, Risk-first, Honest forecasting |
| **Safety spine** | ValidationEngine → DecisionEngine → ExecutionGateway guardrails |
| **Option 1 migration** | Cloudflare + Render + Neon + R2 (post-Phase 17) |
| **Mock UI** | Phase 15 SPA with static `pages.js` data |
| **wt/** | 15 git worktrees for per-agent isolation |

---

## 22. Quick Reference Tables

### URLs

| Resource | URL |
|----------|-----|
| GitHub | https://github.com/marinerxcapital/marinerx-quant-cc.git |
| Railway (fallback, live) | https://marinerx-quant-cc-production.up.railway.app/ |
| Render (target, not live yet) | https://marinerx-labs-api.onrender.com/ (after Blueprint) |
| Cloudflare R2 | https://dash.cloudflare.com/b31d3d49151af98fe1125aa40c5fa6c8/r2/overview |
| Render dashboard | https://dashboard.render.com/ |

### Key commands

```powershell
python main.py doctor
python main.py run --interface web
python main.py run --interface worker
python -m pytest tests/ -q
npx neonctl@latest env pull --file .env
wrangler r2 bucket list
```

### Phase 17 + migration deliverables

- [x] Phase 17 forecast lab, stat rigor, Seaborn reports
- [x] 60 tests at Phase 17 gate → 70 after deployment tests
- [x] Neon Postgres wired (`6b20ab6`, `01b67da`)
- [x] `render.yaml` Blueprint (`43e58db`)
- [x] Deployment docs package (`docs/deployment/`)
- [ ] R2 enabled + bucket created
- [ ] Render Blueprint applied + smoke PASS
- [ ] Pipeline `risk_veto` wired to RiskCommand
- [ ] `PROGRESS.md` updated for post-17 deployment

---

## Instructions for Claude (summary)

You are continuing an **in-progress** quant platform build, not starting from scratch.

1. **Canonical workspace:** `MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\`
2. **Build status:** Phase 17 complete; deployment migration in progress
3. **Tests:** 70 passing (verify before claiming)
4. **Production:** Railway is live fallback; Render is the migration target
5. **Blocked items:** R2 (human), Render Blueprint apply (human), Docker (optional)
6. **Known bug:** `pipeline.py` hardcodes `risk_veto=False` — P2 not fully wired in replay spine
7. **Safety:** Never enable live execution without explicit approval
8. **Ignore:** `MarinerX_SuperGrok_Build`, old `MarinerX_Quant_CC_Complete_Build_Status_for_Claude.md`

Resume from `SETUP_STATUS.md` for deployment next steps, or from `PROGRESS.md` + master brief for feature phases.

---

*End of MarinerX Labs Complete Project Summary for Claude. Version 1.0 — 2026-07-05.*