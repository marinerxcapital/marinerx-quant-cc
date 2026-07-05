# Render Background Worker

The agent supervisor runs as a **Docker background worker** on Render — no HTTP server, persistent heartbeat loop.

**Current deployment status:** deferred. Render's free tier is not available for background workers, so the active `render.yaml` provisions only the free web service for smoke testing. Add this worker later on a paid plan after explicit cost approval.

## Service definition

| Item | Value |
|------|-------|
| Blueprint | `render.yaml` |
| Service name | `marinerx-labs-worker` |
| Type | `worker` |
| Runtime | `docker` |
| Plan | `starter` or approved production tier |
| Start command | `python main.py run --interface worker` |

## What the worker does

`main.py run --interface worker`:

1. Sets `SERVICE_MODE=worker`
2. Validates production config and initializes DB (same as web)
3. Starts supervisor + 15 agents
4. Enters `_worker_loop()`:
   - Writes heartbeat to `agent_heartbeats` table
   - Logs structured `worker_heartbeat` event
   - Sleeps `AGENT_HEARTBEAT_INTERVAL_SECONDS` (default 30s)
5. On `SIGTERM`/`SIGINT`: graceful shutdown via `supervisor.kill_switch()` (timeout `WORKER_SHUTDOWN_TIMEOUT_SECONDS`)

## Heartbeat schema

Table: `agent_heartbeats` (`src/mcc/storage/models.py`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | Auto-increment |
| `ts_utc` | DateTime TZ | Heartbeat timestamp |
| `service_mode` | String | `worker` |
| `agent_count` | Integer | Total registered agents |
| `healthy_count` | Integer | Agents not in `error` status |
| `kill_active` | Boolean | Supervisor kill-switch state |
| `status` | String | `ok` if all healthy, else `degraded` |

Written by `_write_worker_heartbeat()` in `main.py` each loop iteration.

## Query recent heartbeats

```sql
SELECT ts_utc, agent_count, healthy_count, kill_active, status
FROM agent_heartbeats
ORDER BY ts_utc DESC
LIMIT 10;
```

Stale workers: no new rows within `2 × AGENT_HEARTBEAT_INTERVAL_SECONDS`.

## Required environment variables

Worker shares database and R2 config with web service:

```env
APP_ENV=production
SERVICE_MODE=worker
ENABLE_LIVE_EXECUTION=false
OBJECT_STORAGE_BACKEND=r2
DATA_DIR=/data
LOG_DIR=/data/logs
DATABASE_URL=<same-as-web>
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
```

Worker does not need `PUBLIC_FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, or `R2_PUBLIC_BASE_URL` unless you add features that read them.

## Deploy steps

1. Deploy worker from same repo/branch as web service.
2. Ensure `DATABASE_URL` matches web service exactly.
3. Scale to 1 instance (multiple workers would duplicate agent loops — not supported without leader election).
4. Confirm log lines: `worker_started`, recurring `worker_heartbeat`.
5. Confirm rows appearing in `agent_heartbeats`.

## Observability

**Logs (Render worker stream):**

```json
{"event": "worker_heartbeat", "healthy": 15, "total": 15, "kill_active": false, "level": "info"}
```

**Database:** Query `agent_heartbeats` for historical liveness.

**No `/health` on worker** — Render workers are not HTTP-scraped. Use logs + DB heartbeats.

## Failure modes

| Symptom | Likely cause |
|---------|--------------|
| Worker restarts loop | DB connection failure — check `DATABASE_URL` |
| `healthy < total` | Agent in `error` — check supervisor logs |
| No heartbeat rows | DB permissions or wrong `DATABASE_URL` |
| Immediate exit | `validate_production_requirements()` failure (missing R2/DB) |

## Verification

```bash
# Local worker smoke test
python main.py run --interface worker
# Ctrl+C after seeing worker_heartbeat logs

# Check SQLite heartbeats locally
sqlite3 ./data/mcc.sqlite "SELECT * FROM agent_heartbeats ORDER BY id DESC LIMIT 3;"
```

## Safety

- `ENABLE_LIVE_EXECUTION=false` in `render.yaml` for worker.
- Tradeify browser automation blocked in cloud (see `TRADEIFY_LOCAL_ONLY_POLICY.md`).
- Worker uses replay supervisor — no live execution keys required.
- Render free tier is not available for background workers.
