# Healthchecks and Observability

## HTTP health endpoint

**Route:** `GET /health`  
**File:** `src/mcc/interface/web/server.py`  
**Consumers:** Render (`healthCheckPath: /health`), Docker `HEALTHCHECK`, load balancers, `app.js` dashboard poll

### Response schema

```json
{
  "status": "ok | degraded | error",
  "app_env": "production",
  "service_mode": "web",
  "version": "0.1.0",
  "live_execution_enabled": false,
  "database": {
    "status": "ok | error",
    "backend": "postgres | sqlite",
    "url_scheme": "postgresql",
    "error": "..."
  },
  "object_storage": {
    "status": "ok | error",
    "backend": "r2 | local",
    "bucket": "...",
    "root": "...",
    "error": "..."
  },
  "agents": {
    "Overseer": "idle",
    "DataOps": "working",
    "ValidationEngine": "idle"
  },
  "ts": "2026-07-05T12:00:00+00:00"
}
```

### Overall status logic

| `status` | Condition |
|----------|-----------|
| `ok` | Agents, database, and storage all `ok` |
| `degraded` | No component `error`, but at least one not `ok` |
| `error` | Any component reports `error` |

Agent health: `ok` if no agent status is `error`; else `degraded`.

### Fallback supervisor

If `_SUP` is unset (e.g. import-only test), health creates `create_supervisor(replay=True)` temporarily.

## Docker healthcheck

`Dockerfile`:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
  CMD python -c "urllib.request.urlopen('http://127.0.0.1:{PORT}/health', timeout=5)"
```

Aligns with `HEALTHCHECK_TIMEOUT_SECONDS=5` in config.

## Worker observability (no HTTP)

Background worker does not expose `/health`. Use:

### 1. Structured logs

Configured in `main.py`:

```python
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    ...
)
```

**Key events:**

| Event | Service | Fields |
|-------|---------|--------|
| `service_starting` | web/worker | `service_mode`, `app_env`, `live_execution` |
| `worker_started` | worker | `agents` count |
| `worker_heartbeat` | worker | `healthy`, `total`, `kill_active` |
| `object_store_put` | both | `backend`, `key`, `size` |
| `tradeify_automation_blocked` | guard | `reasons`, `routine` |
| `shutdown_signal_received` | both | `signal` |

**Log level:** `STRUCTLOG_LEVEL` (default `INFO`).

### 2. Database heartbeats

Table `agent_heartbeats` — see `RENDER_WORKER.md`.

```sql
SELECT ts_utc, healthy_count, agent_count, status, kill_active
FROM agent_heartbeats ORDER BY ts_utc DESC LIMIT 5;
```

Alert if latest row older than **60 seconds** (2× default interval).

## CLI doctor

```bash
python main.py doctor
```

Rich table checks:

- Config + `ENABLE_LIVE_EXECUTION` state
- Production config validation
- Database connectivity
- Object storage health
- Supervisor + 15 agents
- Safety module imports (lifecycle, guardrails, decision, tradeify guard)

Exit code `1` on failure.

## Dashboard integration

`static/app.js` polls `GET /health` for status badge. WebSocket `/ws` provides live agent updates independent of health interval.

## Render monitoring

| Service | Probe |
|---------|-------|
| Web | Automatic `/health` every few minutes |
| Worker | Log stream + manual DB heartbeat query |

## Recommended alerts (manual setup)

1. Web `/health` `status != ok` for > 5 min
2. `live_execution_enabled == true` in production (should never fire)
3. No `agent_heartbeats` row in 2 min
4. `database.status == error` in health JSON
5. Spike in `tradeify_automation_blocked` logs

## Local verification

```bash
# Start web
python main.py run --interface web &
curl -s http://localhost:8000/health | python -m json.tool

# Doctor
python main.py doctor
```