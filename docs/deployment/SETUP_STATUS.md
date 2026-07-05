# Deployment Setup Status — 2026-07-05

Live tracker for Option 1 migration (Cloudflare + Render + Neon + R2). Current Render Blueprint is a **free web-service smoke deploy**; background worker is deferred because Render does not offer free background workers.

---

## Completed

| Step | Status | Evidence |
|------|--------|----------|
| Code migration committed | **DONE** | Infra migration through `a280475`; Render free-tier + Codex handoff through `a93383b` |
| Pushed to GitHub | **DONE** | `master` → `origin/master` through `a93383b` before this tracker sync |
| Local pytest | **DONE** | `73 passed` (includes CRITICAL PATCH 01 integration tests) |
| Local doctor | **DONE** | All green, live execution DISABLED |
| Codex startup verification | **DONE** | 2026-07-05: `python main.py doctor` all green; `python -m pytest tests/ -q` → `73 passed, 28 warnings` |
| Local web smoke test | **DONE** | `/health` → `status: ok`, `live_execution_enabled: false`, 15 agents |
| Wrangler auth (Cloudflare) | **DONE** | Account: MarinerX Capital (`b31d3d49151af98fe1125aa40c5fa6c8`) |

### Local smoke test output (2026-07-05)

```json
{
  "status": "ok",
  "app_env": "local",
  "service_mode": "web",
  "live_execution_enabled": false,
  "database": { "status": "ok", "backend": "sqlite" },
  "object_storage": { "status": "ok", "backend": "local" }
}
```

`GET /` → HTTP 200

---

## Blocked / Needs Human Action

| Step | Status | Action required |
|------|--------|-----------------|
| Docker build smoke test | **BLOCKED** | Docker Desktop not installed (`docker` not in PATH). Install Docker Desktop, then run commands in § Docker below. |
| Cloudflare R2 | **BLOCKED** | R2 not enabled on account (error `10042`; rechecked 2026-07-05 with `wrangler r2 bucket list`). **You must click Enable R2** in dashboard — see `RENDER_R2_COMBINED_SETUP.md` Part A. |
| Neon Postgres | **DONE** | Project `MarinerX Labs` (`summer-star-19798293`), branch `production`. Postgres verified. |
| Render deploy | **IN PROGRESS** | `render.yaml` on **free web tier** ($0/mo web smoke). Worker intentionally deferred until paid-worker approval. Apply Blueprint in dashboard. Recheck 2026-07-05: `https://marinerx-labs-api.onrender.com/health` returns Render `404 Not Found` / `x-render-routing: no-server`, so service is not live yet. |

---

## Step-by-step: Enable R2 (Cloudflare)

1. Open: https://dash.cloudflare.com/b31d3d49151af98fe1125aa40c5fa6c8/r2/overview
2. Click **Enable R2** / purchase (free tier available)
3. Create bucket: `marinerx-mcc-prod`
4. **R2 → Manage R2 API Tokens** → Create token (Object Read & Write)
5. Record and set on Render (never commit):
   - `R2_ACCOUNT_ID=b31d3d49151af98fe1125aa40c5fa6c8`
   - `R2_ACCESS_KEY_ID=...`
   - `R2_SECRET_ACCESS_KEY=...`
   - `R2_BUCKET_NAME=marinerx-mcc-prod`

Verify:

```powershell
wrangler r2 bucket list
wrangler r2 bucket create marinerx-mcc-prod
```

---

## Neon Postgres — configured

| Item | Value |
|------|-------|
| Org | MarinerX Labs (`org-square-wave-40095229`) |
| Project | MarinerX Labs (`summer-star-19798293`) |
| Branch | `production` (`br-delicate-voice-aiyzlz6h`) |
| Region | `aws-us-east-1` |
| Local link | `.neon` in repo root |
| Secrets | `.env` — `DATABASE_URL` (pooled), `DATABASE_URL_UNPOOLED` |

**Refresh local env after branch changes:**

```powershell
npx neonctl@latest checkout production
npx neonctl@latest env pull --file .env
```

**Render:** copy `DATABASE_URL` from `.env` into **both** web and worker services (use pooled URL).

---

## Step-by-step: Render (Web + Worker)

1. Open: https://dashboard.render.com/
2. **New → Blueprint**
3. Connect GitHub → `marinerxcapital/marinerx-quant-cc` → branch `master`
4. Render reads `render.yaml` → creates:
   - `marinerx-labs-api` (web, free tier)
   - Worker is deferred; Render free tier does not support background workers.
5. When prompted, set secret env vars:
   - `DATABASE_URL` (from Neon)
   - `R2_*` (from Cloudflare)
   - `CORS_ALLOWED_ORIGINS`, `PUBLIC_FRONTEND_URL`, `BACKEND_PUBLIC_URL`
6. Deploy the web service

Smoke after deploy:

```bash
curl https://marinerx-labs-api.onrender.com/health
```

Expected: `status: ok`, `live_execution_enabled: false`, `database.status: ok`

---

## Docker build smoke (after Docker Desktop install)

```powershell
cd "C:\Users\Skyler B. Brown\Desktop\MarinerX_Labs\01_ACTIVE_PROJECT\marinerx-quant-cc"
docker build -t marinerx-mcc:smoke .
docker run --rm -d -p 8080:8080 -e APP_ENV=local -e PORT=8080 --name mcc-smoke marinerx-mcc:smoke
Start-Sleep -Seconds 12
Invoke-RestMethod http://127.0.0.1:8080/health
docker stop mcc-smoke
```

---

## Railway fallback (still active)

https://marinerx-quant-cc-production.up.railway.app/

Do not delete Railway until Render smoke passes. See `RAILWAY_FALLBACK_PLAN.md`.

---

*Update this file as each step completes.*
