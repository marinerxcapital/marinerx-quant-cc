# Environment Variables

Central configuration is defined in `.env.example` and loaded by `src/mcc/core/config.py` (`MCCSettings` via pydantic-settings). Copy `.env.example` to `.env` for local development. **Never commit real secrets.**

## Quick reference

| Variable | Default | Required (production) | Description |
|----------|---------|----------------------|-------------|
| `APP_ENV` | `local` | Yes | `local`, `development`, `staging`, or `production` |
| `APP_HOST` | `0.0.0.0` | No | Bind address for web service |
| `APP_PORT` | `8000` | No | App port; overridden by host `PORT` when set |
| `SERVICE_MODE` | `web` | Yes | `web` or `worker` |
| `PUBLIC_FRONTEND_URL` | `http://localhost:8000` | Yes (prod) | Public URL users open in browser |
| `BACKEND_PUBLIC_URL` | `http://localhost:8000` | Yes (prod) | Public API base URL |
| `WEBSOCKET_PUBLIC_URL` | `ws://localhost:8000/ws` | No | WebSocket URL for clients |
| `DATABASE_URL` | *(unset)* | **Yes** (prod/staging) | Postgres connection string; omit for local SQLite |
| `DATABASE_POOL_SIZE` | `5` | No | SQLAlchemy pool size (Postgres only) |
| `DATABASE_MAX_OVERFLOW` | `10` | No | SQLAlchemy max overflow (Postgres only) |
| `DATA_DIR` | `./data` | No | Root data directory (`/data` in production) |
| `LOG_DIR` | `./data/logs` | No | Log output directory |
| `PARQUET_DIR` | `./data/parquet` | No | Parquet analytical files |
| `REPORTS_DIR` | `./data/reports` | No | Local report staging |
| `LOCAL_OBJECT_STORAGE_DIR` | `./data/objects` | No | Local object store root |
| `OBJECT_STORAGE_BACKEND` | `local` | Yes (prod) | `local` or `r2` |
| `R2_ACCOUNT_ID` | — | Yes if `r2` | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | — | Yes if `r2` | R2 API token access key |
| `R2_SECRET_ACCESS_KEY` | — | Yes if `r2` | R2 API token secret |
| `R2_BUCKET_NAME` | — | Yes if `r2` | Target R2 bucket |
| `R2_PUBLIC_BASE_URL` | — | Recommended | Public CDN/custom domain base for object URLs |
| `ENABLE_LIVE_EXECUTION` | `false` | No | **Must stay `false` in cloud** unless explicitly approved |
| `CORS_ALLOWED_ORIGINS` | `*` | Yes (prod) | Comma-separated origins or `*` |
| `STRUCTLOG_LEVEL` | `INFO` | No | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `AGENT_HEARTBEAT_INTERVAL_SECONDS` | `30` | No | Worker heartbeat write interval |
| `WORKER_SHUTDOWN_TIMEOUT_SECONDS` | `30` | No | Graceful supervisor shutdown timeout |
| `HEALTHCHECK_TIMEOUT_SECONDS` | `5` | No | Reserved for health probe timeouts |
| `APP_VERSION` | `0.1.0` | No | Reported in `/health` |

## Host-injected variables (not in `.env.example`)

| Variable | Source | Behavior |
|----------|--------|----------|
| `PORT` | Render, Railway, Docker | Overrides `APP_PORT` via `settings.effective_port` |

Cloud runtime markers detected by `is_cloud_runtime()` (read-only, not configurable):

- `RENDER`, `RENDER_SERVICE_ID`
- `RAILWAY_ENVIRONMENT`, `RAILWAY_PROJECT_ID`
- `CF_PAGES`, `VERCEL`, `FLY_APP_NAME`

## Environment behavior

### Local (`APP_ENV=local` or `development`)

- `DATABASE_URL` unset → SQLite at `{DATA_DIR}/mcc.sqlite`
- `OBJECT_STORAGE_BACKEND=local` → files under `LOCAL_OBJECT_STORAGE_DIR`
- Production validation (`validate_production_requirements`) is skipped

### Production / staging (`APP_ENV=production` or `staging`)

- `DATABASE_URL` **required** — raises `ConfigError` if missing
- `OBJECT_STORAGE_BACKEND=r2` requires all four R2 credential vars
- Data paths default to `/data/*` when not overridden
- `validate_production_requirements()` runs at service startup (`main.py`)

## Boolean parsing

`ENABLE_LIVE_EXECUTION` accepts `1`, `true`, `yes`, `on` (case-insensitive). Any other value defaults to **false**.

## Render blueprint mapping

`render.yaml` sets non-secret defaults and marks secrets with `sync: false`:

- Web: `marinerx-labs-api` — `SERVICE_MODE=web`, `OBJECT_STORAGE_BACKEND=r2`
- Worker: `marinerx-labs-worker` — `SERVICE_MODE=worker`, `OBJECT_STORAGE_BACKEND=r2`

Set these manually in the Render dashboard:

`DATABASE_URL`, `R2_*`, `CORS_ALLOWED_ORIGINS`, `PUBLIC_FRONTEND_URL`, `BACKEND_PUBLIC_URL`

## Validation commands

```bash
python main.py doctor
python -m pytest tests/deployment/test_config.py -q
```

## Security notes

- Keep `ENABLE_LIVE_EXECUTION=false` in all cloud services unless a formal go-live approval exists.
- Restrict `CORS_ALLOWED_ORIGINS` to your Cloudflare/Pages domain in production.
- Rotate R2 API tokens if exposed; never store them in git.