# Production Deployment Runbook

End-to-end procedure for deploying MarinerX Quant Command Center to **Render + managed Postgres (Neon/Supabase) + Cloudflare R2**, with Railway as fallback.

**Target stack:** Render (web + worker) · Neon or Supabase · Cloudflare R2 · Mode A frontend (FastAPI static)

---

## 0. Roles and prerequisites

| Role | Responsibility |
|------|----------------|
| Deployer | Runs commands, sets Render secrets |
| DBA | Provisions Postgres, shares `DATABASE_URL` |
| Cloud admin | R2 bucket, API tokens, optional DNS |

**Repo:** `marinerxcapital/marinerx-quant-cc`  
**Branch:** `master` (or approved release tag)  
**Python:** 3.11+  
**Safety default:** `ENABLE_LIVE_EXECUTION=false`

---

## 1. Pre-flight checklist

- [ ] Read `EXECUTION_SAFETY_AUDIT.md` — confirm no live execution
- [ ] Read `TRADEIFY_LOCAL_ONLY_POLICY.md` — no cloud browser automation
- [ ] Local verification complete per `DEPLOYMENT_VERIFICATION.md`
- [ ] `pytest tests/` green (73 tests as of CRITICAL PATCH 01)
- [ ] `python main.py doctor` green
- [ ] Docker image builds locally
- [ ] Secrets available (never commit): `DATABASE_URL`, `R2_*`, domain URLs

---

## 2. Provision Postgres (Neon or Supabase)

1. Create project and database (e.g. `mcc`).
2. Enable SSL (`?sslmode=require` for Neon).
3. Copy connection string:

   ```
   postgresql://user:password@host:5432/mcc?sslmode=require
   ```

4. Save as `DATABASE_URL` — **same value for web and worker**.

No manual schema migration — app runs `create_all` on startup.

---

## 3. Provision Cloudflare R2

1. Create bucket (e.g. `marinerx-mcc-prod`).
2. Create API token (Object Read & Write).
3. Record: Account ID, Access Key, Secret, Bucket name.
4. Optional: custom domain → `R2_PUBLIC_BASE_URL`.

See `R2_STORAGE.md`.

---

## 4. Create Render services

### Option A — Blueprint (recommended)

1. Render Dashboard → **New** → **Blueprint**
2. Connect repo; select `render.yaml`
3. Review services:
   - `marinerx-labs-api` (web)
   - `marinerx-labs-worker` (worker)

### Option B — Manual

Mirror `render.yaml` settings: Docker runtime, free plan for dev/smoke, health path `/health`, commands as documented in `RENDER_WEB_SERVICE.md` and `RENDER_WORKER.md`. Upgrade to `starter` for production traffic.

---

## 5. Configure environment variables

### Web service (`marinerx-labs-api`)

| Variable | Value |
|----------|-------|
| `APP_ENV` | `production` |
| `SERVICE_MODE` | `web` |
| `ENABLE_LIVE_EXECUTION` | `false` |
| `OBJECT_STORAGE_BACKEND` | `r2` |
| `DATABASE_URL` | *(secret)* |
| `R2_ACCOUNT_ID` | *(secret)* |
| `R2_ACCESS_KEY_ID` | *(secret)* |
| `R2_SECRET_ACCESS_KEY` | *(secret)* |
| `R2_BUCKET_NAME` | *(secret)* |
| `R2_PUBLIC_BASE_URL` | `https://assets.yourdomain.com` |
| `CORS_ALLOWED_ORIGINS` | `https://your-domain.com` |
| `PUBLIC_FRONTEND_URL` | `https://your-domain.com` |
| `BACKEND_PUBLIC_URL` | `https://marinerx-labs-api.onrender.com` |
| `DATA_DIR` | `/data` |
| `LOG_DIR` | `/data/logs` |
| `PARQUET_DIR` | `/data/parquet` |
| `REPORTS_DIR` | `/data/reports` |
| `LOCAL_OBJECT_STORAGE_DIR` | `/data/objects` |

### Worker service (`marinerx-labs-worker`)

Same as web for: `APP_ENV`, `SERVICE_MODE=worker`, `ENABLE_LIVE_EXECUTION`, `OBJECT_STORAGE_BACKEND`, `DATABASE_URL`, `R2_*`, `DATA_DIR`, `LOG_DIR`.

---

## 6. Deploy sequence

```
1. Deploy worker first (validates DB + R2 without user traffic)
2. Confirm worker logs: worker_started, worker_heartbeat
3. Query agent_heartbeats — rows appearing
4. Deploy web service
5. Wait for Render health check on /health
6. Smoke test endpoints
7. Optional DNS cutover
```

**Do not** enable live execution at any step.

---

## 7. Post-deploy verification

```bash
# Web health
curl -s https://<RENDER_WEB_HOST>/health | jq .

# Dashboard
curl -s -o /dev/null -w "%{http_code}\n" https://<RENDER_WEB_HOST>/

# Worker (via DB)
# SELECT * FROM agent_heartbeats ORDER BY ts_utc DESC LIMIT 3;
```

**Pass criteria:**

| Check | Expected |
|-------|----------|
| `/health` HTTP status | 200 |
| `status` | `ok` |
| `live_execution_enabled` | `false` |
| `database.status` | `ok`, `backend`: `postgres` |
| `object_storage.status` | `ok`, `backend`: `r2` |
| `agents` | 15 entries, none `error` |
| Worker heartbeats | Fresh rows < 60s old |

Full checklist: `DEPLOYMENT_VERIFICATION.md`.

---

## 8. DNS and Cloudflare (optional cutover)

**Mode A (current):** Single host serves API + SPA.

1. Create `CNAME` → Render web hostname.
2. Enable Cloudflare proxy if desired (WebSocket compatible).
3. Update `PUBLIC_FRONTEND_URL` and `BACKEND_PUBLIC_URL` to custom domain.
4. Update `CORS_ALLOWED_ORIGINS` to match.

**Mode B (future):** See `CLOUDFLARE_FRONTEND.md` for Pages split.

---

## 9. Railway fallback (keep warm)

- Do **not** delete `railway.json`
- Verify https://marinerx-quant-cc-production.up.railway.app/health periodically
- Rollback: point DNS to Railway — see `RAILWAY_FALLBACK_PLAN.md`

---

## 10. Monitoring setup

| Signal | Source |
|--------|--------|
| Web liveness | Render `/health` |
| Worker liveness | `agent_heartbeats` + logs |
| Errors | Render log stream (JSON structlog) |
| Safety | Alert if `live_execution_enabled: true` |

See `HEALTHCHECKS_AND_OBSERVABILITY.md`.

---

## 11. Rollback procedure

### Application rollback

1. Render → service → **Rollback** to previous deploy.
2. Or redeploy last known-good git SHA.

### Full traffic rollback

1. DNS → Railway production URL.
2. Confirm Railway `/health`.
3. Post-mortem before re-attempting cutover.

**Data:** Postgres and R2 are external — rollback does not destroy data.

---

## 12. Post-deploy tasks

- [ ] Log deploy evidence in team channel (pytest output, health JSON, heartbeat query)
- [ ] Confirm `ENABLE_LIVE_EXECUTION=false` on both services
- [ ] Schedule 30-day Railway soak before decommission
- [ ] Plan `agent_heartbeats` retention if volume grows

---

## 13. Explicitly out of scope

| Item | Policy |
|------|--------|
| Live broker execution | `ENABLE_LIVE_EXECUTION` stays false |
| Tradeify Playwright in cloud | Blocked by guard |
| Cloudflare Pages split | Mode B — future |
| Alembic migrations | `create_all` only until schema complexity warrants |

---

## 14. Quick reference commands

```bash
# Local pre-deploy
pip install -e ".[dev,deploy]"
python -m pytest tests/ -q
python main.py doctor
docker build -t marinerx-mcc .

# Production smoke
curl -s https://<host>/health
python main.py doctor   # against prod env vars locally (careful with secrets)
```

---

## 15. Support matrix

| Component | Doc |
|-----------|-----|
| Env vars | `ENVIRONMENT_VARIABLES.md` |
| Database | `DATABASE_MIGRATION.md` |
| R2 | `R2_STORAGE.md` |
| Render web | `RENDER_WEB_SERVICE.md` |
| Render worker | `RENDER_WORKER.md` |
| Frontend | `CLOUDFLARE_FRONTEND.md` |
| Safety | `EXECUTION_SAFETY_AUDIT.md` |
| Railway | `RAILWAY_FALLBACK_PLAN.md` |
