# Deployment Setup Status — 2026-07-05

Live tracker for Option 1 migration (Cloudflare + Render + Neon + R2).

---

## Completed

| Step | Status | Evidence |
|------|--------|----------|
| Code migration committed | **DONE** | `a280475` — `deploy: migrate infrastructure to cloudflare render postgres r2` |
| Pushed to GitHub | **DONE** | `master` → `origin/master` (`469115a..a280475`) |
| Local pytest | **DONE** | `70 passed` |
| Local doctor | **DONE** | All green, live execution DISABLED |
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
| Cloudflare R2 | **BLOCKED** | R2 not enabled on account. Error `10042`: enable at dashboard link below. |
| Neon Postgres | **PENDING** | No `NEON_API_KEY` in environment. Create project at Neon console; copy `DATABASE_URL`. |
| Render deploy | **PENDING** | No `RENDER_API_KEY`. Connect GitHub repo via Render Blueprint (`render.yaml`). |

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

## Step-by-step: Neon Postgres

1. Open: https://console.neon.tech/
2. Sign in (GitHub OK)
3. **New Project** → name `marinerx-mcc`, region nearest to Render (e.g. US East)
4. Copy connection string (with `?sslmode=require`)
5. Set on **both** Render services:

```
DATABASE_URL=postgresql://user:pass@ep-xxx.region.aws.neon.tech/mcc?sslmode=require
```

---

## Step-by-step: Render (Web + Worker)

1. Open: https://dashboard.render.com/
2. **New → Blueprint**
3. Connect GitHub → `marinerxcapital/marinerx-quant-cc` → branch `master`
4. Render reads `render.yaml` → creates:
   - `marinerx-labs-api` (web)
   - `marinerx-labs-worker` (worker)
5. When prompted, set secret env vars:
   - `DATABASE_URL` (from Neon)
   - `R2_*` (from Cloudflare)
   - `CORS_ALLOWED_ORIGINS`, `PUBLIC_FRONTEND_URL`, `BACKEND_PUBLIC_URL`
6. Deploy both services

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