# MarinerX Labs — Codex Handoff (Grok → Codex)

**Prepared:** 2026-07-05  
**Owner:** Skyler B. Brown  
**From:** Grok (Cursor) — prior session work  
**To:** OpenAI Codex — you are taking over active development

---

## ⚠️ RULE #1 — ONE FOLDER FOR ALL AGENTS

**Grok, Codex, Claude, and any other AI assistant MUST work in the same directory:**

```
C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\
```

| Do this | Do NOT do this |
|---------|----------------|
| `cd` into the path above before any work | Work in `Desktop\MarinerX_SuperGrok_Build\` |
| Commit and push from this repo | Edit only `MarinerX_Labs\04_DOCUMENTATION\` without syncing to repo |
| Open this folder as your Codex workspace root | Use `02_BUILD_VARIANTS\` archives as active code |
| Treat this as the single source of truth | Create parallel copies on Desktop |

**GitHub remote (same repo both agents use):**  
https://github.com/marinerxcapital/marinerx-quant-cc.git  
**Branch:** `master`

**Hub folder** (`MarinerX_Labs\`) is documentation and archives only. All code changes happen inside `01_ACTIVE_PROJECT\marinerx-quant-cc\`.

---

## Session startup (run every time)

```powershell
cd "C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc"
git pull origin master
git status
git log --oneline -5
python main.py doctor
python -m pytest tests/ -q
```

Expected: **73 passed**, doctor all green, `live_execution_enabled: false`.

---

## Current state (truth as of handoff)

| Item | Value |
|------|-------|
| **Phase** | 17 COMPLETE |
| **CRITICAL PATCH 01** | COMPLETE — risk veto wired through pipeline |
| **Tests** | **73 passing** (70 + 3 integration tests for patch) |
| **Git HEAD** | `44f19c4` — risk veto patch (Render free-tier change pending commit) |
| **Neon Postgres** | DONE — project `summer-star-19798293`, `.neon` linked |
| **Render** | Blueprint ready (`render.yaml`), **free tier**, not yet applied in dashboard |
| **Cloudflare R2** | BLOCKED — enable in dashboard (error `10042`) |
| **Railway fallback** | Live at https://marinerx-quant-cc-production.up.railway.app/ — keep until Render smoke passes |
| **Live execution** | DISABLED (`ENABLE_LIVE_EXECUTION=false`) |

---

## What Grok completed this session

1. Created `docs/MARINERX_LABS_CLAUDE_COMPLETE_PROJECT_SUMMARY.md` (Claude handoff)
2. Applied **CRITICAL PATCH 01** — `pipeline.py` risk veto bus wiring + integration tests
3. Pushed to GitHub (`3d0afe9`, `44f19c4`)
4. Changed `render.yaml` from `plan: starter` ($7/mo each) → `plan: free` ($0) for web + worker

---

## Your immediate tasks (Codex)

### Priority 1 — Human-blocked (document, don't fake PASS)

Skyler must do these in browser. Codex prepares docs and verifies after:

1. **Enable Cloudflare R2** — https://dash.cloudflare.com/b31d3d49151af98fe1125aa40c5fa6c8/r2/overview  
   Create bucket `marinerx-mcc-prod`, API token, set `R2_*` secrets.

2. **Apply Render Blueprint** — https://dashboard.render.com/ → New → Blueprint → `marinerxcapital/marinerx-quant-cc`  
   Uses `render.yaml` (free tier). Set secrets: `DATABASE_URL`, `R2_*`, CORS/URL vars.

3. **Smoke test after deploy:**
   ```bash
   curl https://marinerx-labs-api.onrender.com/health
   ```
   Expect: `status: ok`, `live_execution_enabled: false`

Tracker: `docs/deployment/SETUP_STATUS.md` — update as steps complete.

### Priority 2 — Agent work (after deploy or in parallel)

| Task | File(s) |
|------|---------|
| Sync `SETUP_STATUS.md` (73 tests, patch 01, free tier) | `docs/deployment/SETUP_STATUS.md` |
| Wire UI to live API (replace mock `pages.js` data) | `src/mcc/interface/web/static/` |
| Build missing modules per master brief | `internals/`, `indicators/`, `journal/` |
| Tradeify sync Python implementation | spec at `tradeify-sync/` (local-only policy) |

---

## Key files to read first

| Order | File | Why |
|-------|------|-----|
| 1 | **This file** | Codex takeover + folder rule |
| 2 | `PROGRESS.md` | Phase 17 + CRITICAL PATCH 01 |
| 3 | `docs/deployment/SETUP_STATUS.md` | Deployment step tracker |
| 4 | `docs/MARINERX_LABS_CLAUDE_COMPLETE_PROJECT_SUMMARY.md` | Full project context |
| 5 | `command-center/00_MASTER_BRIEF.md` | Constitutional spec (aspirational) |

---

## Architecture quick reference

- **CLI:** `python main.py doctor` | `run --interface web` | `run --interface worker`
- **Package:** `src/mcc/`
- **Web:** `src/mcc/interface/web/server.py` + `static/` (Phase 15 SPA, mock data)
- **Safety spine:** ValidationEngine → DecisionEngine → ExecutionGateway (guardrails)
- **Principles:** P1 validation-first, P2 risk-first, P3 honest forecasting

**15 agents** registered in `src/mcc/runtime/bootstrap.py`. Many are partial/NoOp; spine is wired.

---

## Stale paths — reject these

| Wrong | Correct |
|-------|---------|
| `Desktop\MarinerX_SuperGrok_Build\` | `MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\` |
| `src/mcc/api/` | `src/mcc/interface/web/` |
| `uvicorn mcc.api.main:app` | `python main.py run --interface web` |
| `requirements.txt` | `pyproject.toml` |
| Hub-only doc edits without repo sync | Commit from `marinerx-quant-cc\` |

---

## Render free tier (just changed)

`render.yaml` now uses `plan: free` for both services:

| Service | Plan | Cost |
|---------|------|------|
| `marinerx-labs-api` (web) | free | $0/mo |
| `marinerx-labs-worker` | free | $0/mo |

**Free tier limits:** 512 MB RAM, spins down after ~15 min idle (cold start on wake). Fine for dev/smoke; upgrade to `starter` ($7/mo) for production traffic.

Neon + R2 remain on free tiers at current scale.

---

## Git workflow (both agents)

```powershell
cd "C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc"
git pull origin master
# ... make changes ...
git add <files>
git commit -m "type: description"
git push origin master
```

- Never commit `.env`, secrets, or `__pycache__/`
- Run `pytest` before claiming PASS
- Update `SETUP_STATUS.md` or `PROGRESS.md` when completing gates

---

## Safety rules (non-negotiable)

1. **Never** set `ENABLE_LIVE_EXECUTION=true` without explicit human approval
2. **Never** commit secrets (`DATABASE_URL`, `R2_*`, etc.)
3. **Never** enable Tradeify automation in cloud (see `docs/deployment/TRADEIFY_LOCAL_ONLY_POLICY.md`)
4. **Always** run doctor + pytest before reporting completion
5. **Always** work in `01_ACTIVE_PROJECT\marinerx-quant-cc\` — same folder as Grok

---

## Handoff message for Codex

```
You are continuing MarinerX Quant Command Center (MCC). Grok and you share ONE workspace:

C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc\

Phase 17 is complete. CRITICAL PATCH 01 (risk veto pipeline wiring) is complete — 73 tests passing.
Deployment migration is in progress: Neon done, Render blueprint on FREE tier ready, R2 blocked (human must enable).

Start by: cd to canonical path, git pull, doctor, pytest.
Then read SETUP_STATUS.md and help Skyler finish R2 + Render Blueprint deploy.
Do not work in any other folder. Push all changes to marinerxcapital/marinerx-quant-cc master.
```

---

## URLs

| Resource | URL |
|----------|-----|
| GitHub | https://github.com/marinerxcapital/marinerx-quant-cc.git |
| Railway (fallback) | https://marinerx-quant-cc-production.up.railway.app/ |
| Render dashboard | https://dashboard.render.com/ |
| Cloudflare R2 | https://dash.cloudflare.com/b31d3d49151af98fe1125aa40c5fa6c8/r2/overview |
| Neon console | https://console.neon.tech/ |

---

*End of Codex handoff. Version 1.0 — 2026-07-05. Grok session → Codex takeover.*