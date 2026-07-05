# Render Web Service

The MarinerX API and dashboard run as a **Docker web service** on Render.

## Service definition

| Item | Value |
|------|-------|
| Blueprint | `render.yaml` |
| Service name | `marinerx-labs-api` |
| Type | `web` |
| Runtime | `docker` |
| Plan | `free` |
| Health check path | `/health` |
| Start command | `python main.py run --interface web` |

## What the web service does

`main.py run --interface web`:

1. Sets `SERVICE_MODE=web`
2. Validates production config (`validate_production_requirements`)
3. Initializes database (`init_db()` → idempotent `create_all`)
4. Starts supervisor with 15 agents (`create_supervisor` + `start_all`)
5. Patches `web_server._SUP` with live supervisor
6. Serves FastAPI via uvicorn on `0.0.0.0:{PORT}`

## Endpoints

| Route | Purpose |
|-------|---------|
| `GET /health` | Liveness/readiness — DB, storage, agents, env |
| `GET /` | Phase 15 SPA from `static/index.html` |
| `GET /static/*` | CSS, JS, assets |
| `WS /ws` | Live agent snapshot + event bridge |

## Docker image

Built from repo-root `Dockerfile`:

- Python 3.11-slim multi-stage build
- `pip install .` into venv
- `EXPOSE 8080`, `PORT=8080` default
- Built-in `HEALTHCHECK` probes `http://127.0.0.1:{PORT}/health`
- Default `CMD` matches Render command

Render injects `PORT`; app reads it via `settings.effective_port`.

## Required environment variables

Set in Render dashboard (secrets marked `sync: false` in blueprint):

```env
APP_ENV=production
SERVICE_MODE=web
ENABLE_LIVE_EXECUTION=false
OBJECT_STORAGE_BACKEND=r2
DATA_DIR=/data
LOG_DIR=/data/logs
PARQUET_DIR=/data/parquet
REPORTS_DIR=/data/reports
LOCAL_OBJECT_STORAGE_DIR=/data/objects
DATABASE_URL=<neon-or-supabase-url>
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
R2_PUBLIC_BASE_URL=...
CORS_ALLOWED_ORIGINS=https://your-frontend-domain
PUBLIC_FRONTEND_URL=https://your-frontend-domain
BACKEND_PUBLIC_URL=https://marinerx-labs-api.onrender.com
```

## Deploy steps

1. Connect GitHub repo `marinerxcapital/marinerx-quant-cc` to Render.
2. Apply blueprint from `render.yaml` (or create web service manually with same settings).
3. Add secret env vars in dashboard.
4. Deploy; wait for health check on `/health` to pass.
5. Confirm `status: ok` and `live_execution_enabled: false`.

## Health check expectations

Render polls `GET /health`. Service is healthy when HTTP 200 and JSON `status` is `ok` or `degraded` (Render typically wants `ok` — fix `error` components before promoting).

Example healthy response:

```json
{
  "status": "ok",
  "app_env": "production",
  "service_mode": "web",
  "version": "0.1.0",
  "live_execution_enabled": false,
  "database": {"status": "ok", "backend": "postgres"},
  "object_storage": {"status": "ok", "backend": "r2", "bucket": "..."},
  "agents": {"Overseer": "idle", "...": "..."},
  "ts": "2026-07-05T12:00:00+00:00"
}
```

## CORS

FastAPI CORSMiddleware uses `CORS_ALLOWED_ORIGINS` (comma-separated or `*`). Restrict to your Cloudflare frontend origin in production.

## Logs

Structlog JSON to stdout — view in Render log stream. Filter on `service_starting`, `object_store_put`, agent events.

## Verification

```bash
curl -s https://<your-render-host>/health | jq .
python main.py doctor
docker build -t marinerx-mcc .
docker run --rm -p 8080:8080 -e APP_ENV=local marinerx-mcc
curl -s http://localhost:8080/health
```

## Notes

- Web service runs replay adapter by default — no live market keys required.
- Do **not** enable Tradeify browser automation on Render (see `TRADEIFY_LOCAL_ONLY_POLICY.md`).
- Railway remains fallback until DNS cutover (see `RAILWAY_FALLBACK_PLAN.md`).
- Free tier is suitable for dev/smoke and may spin down after idle; upgrade to `starter` for production traffic.
