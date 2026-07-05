# Render + R2 Combined Setup (Do Both)

One checklist for production object storage (Cloudflare R2) and compute (Render web + worker).

**Prerequisites:** Neon Postgres done (`.env` has `DATABASE_URL`), GitHub at `master` with `render.yaml`.

---

## Part A — Cloudflare R2 (do first)

R2 must be **enabled** on your Cloudflare account before buckets or API tokens work.

### A1. Enable R2

1. Open: https://dash.cloudflare.com/b31d3d49151af98fe1125aa40c5fa6c8/r2/overview
2. Click **Enable R2** (free tier available)
3. Wait until dashboard shows R2 buckets UI

### A2. Create bucket

```powershell
wrangler r2 bucket create marinerx-mcc-prod
wrangler r2 bucket list
```

Or in dashboard: **Create bucket** → name `marinerx-mcc-prod`

### A3. Create API token

1. Open: https://dash.cloudflare.com/b31d3d49151af98fe1125aa40c5fa6c8/r2/api-tokens
2. **Create API token** → Object Read & Write → scope to bucket `marinerx-mcc-prod`
3. Save:
   - Access Key ID
   - Secret Access Key

### A4. Add R2 vars to local `.env` (optional local test)

Append to `.env` (never commit):

```env
OBJECT_STORAGE_BACKEND=r2
R2_ACCOUNT_ID=b31d3d49151af98fe1125aa40c5fa6c8
R2_ACCESS_KEY_ID=<from token>
R2_SECRET_ACCESS_KEY=<from token>
R2_BUCKET_NAME=marinerx-mcc-prod
```

Test locally:

```powershell
pip install -e ".[deploy]"
.\scripts\setup_render_r2.ps1 -TestR2
```

---

## Part B — Render Blueprint (web + worker)

### B1. Launch Blueprint

1. Open: https://dashboard.render.com/blueprint/new
2. Connect GitHub → `marinerxcapital/marinerx-quant-cc`
3. Branch: `master`
4. Render loads `render.yaml` → preview:
   - `marinerx-labs-api` (web, Docker, `/health`)
   - `marinerx-labs-worker` (background worker)
   - Env group: `marinerx-production-secrets`

### B2. Set secrets (prompted during Blueprint apply)

Render will ask for values marked `sync: false`. Use:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | From `.env` — **pooled** Neon URL |
| `R2_ACCOUNT_ID` | `b31d3d49151af98fe1125aa40c5fa6c8` |
| `R2_ACCESS_KEY_ID` | From R2 API token |
| `R2_SECRET_ACCESS_KEY` | From R2 API token |
| `R2_BUCKET_NAME` | `marinerx-mcc-prod` |
| `R2_PUBLIC_BASE_URL` | Optional (custom domain for public objects) |
| `CORS_ALLOWED_ORIGINS` | `https://marinerx-labs-api.onrender.com` (update after deploy) |
| `PUBLIC_FRONTEND_URL` | Same as API URL until Cloudflare Pages split |
| `BACKEND_PUBLIC_URL` | `https://marinerx-labs-api.onrender.com` |

**Already set in `render.yaml` (do not override):**

- `APP_ENV=production`
- `ENABLE_LIVE_EXECUTION=false`
- `OBJECT_STORAGE_BACKEND=r2`
- `SERVICE_MODE=web` or `worker`

### B3. Apply Blueprint and wait for deploy

Both services build from `Dockerfile`. First build may take 5–10 minutes.

### B4. Smoke test

```powershell
.\scripts\setup_render_r2.ps1 -RenderHealthUrl "https://marinerx-labs-api.onrender.com/health"
```

Expected JSON:

```json
{
  "status": "ok",
  "app_env": "production",
  "service_mode": "web",
  "live_execution_enabled": false,
  "database": { "status": "ok", "backend": "postgres" },
  "object_storage": { "status": "ok", "backend": "r2" }
}
```

Worker: check Render logs for `worker_started` and `worker_heartbeat`.

---

## Helper script

```powershell
cd "...\marinerx-quant-cc"
.\scripts\setup_render_r2.ps1 -PrintRenderChecklist
.\scripts\setup_render_r2.ps1 -TestPostgres
.\scripts\setup_render_r2.ps1 -TestR2
```

---

## If R2 enable is blocked (error 10042)

Wrangler returns:

```
Please enable R2 through the Cloudflare Dashboard. [code: 10042]
```

**Fix:** Complete Part A1 in browser — CLI cannot enable R2 for you.

---

## Railway fallback

Keep Railway live until Render smoke passes: https://marinerx-quant-cc-production.up.railway.app/

See `RAILWAY_FALLBACK_PLAN.md`.