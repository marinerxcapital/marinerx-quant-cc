# Deployment Verification

Commands and checks to validate the migration. **Evidence was captured at migration implementation time** (pytest, doctor, config tests). Re-run before each production deploy and paste results into your deploy log.

## Prerequisites

```bash
cd MarinerX_Labs/01_ACTIVE_PROJECT/marinerx-quant-cc
python --version   # >= 3.11
```

## 1. Install

```bash
pip install -e ".[dev,deploy]"
```

**Expected:** No install errors; `boto3` available for R2 tests.

## 2. Unit and safety tests

```bash
python -m pytest tests/ -q
```

**Migration evidence (2026-07-04):**

```
python -m pytest tests/ -q
70 passed, 25 warnings in 91.15s
```

Deployment-specific subset:

```bash
python -m pytest tests/deployment/ tests/test_safety_gates.py -q
```

**Expected:** All pass (config, object store, tradeify guard, safety gates).

## 3. Doctor

```bash
python main.py doctor
```

**Expected:**

- `config` OK
- `live execution` DISABLED (default)
- `database` OK sqlite (local) or postgres (with `DATABASE_URL`)
- `object storage` ok (local)
- `supervisor + 15 agents` OK
- Safety modules OK
- Exit 0, `All green`

## 4. Local web smoke

```bash
python main.py run --interface web
# Separate terminal:
curl -s http://localhost:8000/health
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
```

**Expected:**

- `/health` → JSON `status` in `ok`/`degraded`, `live_execution_enabled: false`
- `/` → HTTP 200 (SPA HTML)

## 5. Local worker smoke

```bash
python main.py run --interface worker
```

**Expected:** Log lines `worker_started`, `worker_heartbeat` every ~30s. Rows in `./data/mcc.sqlite` → `agent_heartbeats`.

```bash
sqlite3 ./data/mcc.sqlite "SELECT COUNT(*) FROM agent_heartbeats;"
```

## 6. Docker build

```bash
docker build -t marinerx-mcc:verify .
docker run --rm -d -p 8080:8080 --name mcc-verify marinerx-mcc:verify
sleep 20
curl -s http://localhost:8080/health
docker stop mcc-verify
```

**Expected:** Image builds; container healthcheck passes; `/health` returns 200.

## 7. Production config dry-run (local)

```bash
set APP_ENV=production
set DATABASE_URL=postgresql://user:pass@localhost:5432/mcc_test
set OBJECT_STORAGE_BACKEND=r2
set R2_ACCOUNT_ID=test
set R2_ACCESS_KEY_ID=test
set R2_SECRET_ACCESS_KEY=test
set R2_BUCKET_NAME=test
python -c "from mcc.core.config import MCCSettings; s=MCCSettings(_env_file=None); s.validate_production_requirements(); print('production config OK')"
```

**Expected:** No `ConfigError` when all required vars set.

## 8. Render post-deploy (manual)

Replace `<RENDER_HOST>` with your service URL:

```bash
curl -s https://<RENDER_HOST>/health
curl -s -o /dev/null -w "%{http_code}" https://<RENDER_HOST>/
```

**Expected:**

- `app_env`: `production`
- `service_mode`: `web`
- `live_execution_enabled`: `false`
- `database.status`: `ok`
- `object_storage.backend`: `r2`

## 9. Worker heartbeat (production)

```sql
-- Run against Neon/Supabase
SELECT ts_utc, healthy_count, agent_count, status
FROM agent_heartbeats
ORDER BY ts_utc DESC
LIMIT 5;
```

**Expected:** Rows within last 60 seconds while worker is running.

## 10. Railway fallback check

```bash
curl -s https://marinerx-quant-cc-production.up.railway.app/health
```

**Expected:** HTTP 200 while Railway remains warm.

## Evidence log (migration time)

| Check | Result | Notes |
|-------|--------|-------|
| `pytest tests/` | **70 tests** | Includes `tests/deployment/*` |
| `main.py doctor` | **PASS** | Local SQLite + local storage |
| `test_config.py` | **PASS** | `ENABLE_LIVE_EXECUTION` defaults false |
| `test_tradeify_guard.py` | **PASS** | Cloud/production blocked |
| `test_object_store.py` | **PASS** | Key sanitize + local roundtrip |
| `render.yaml` | **Present** | Web + worker services |
| `railway.json` | **Kept** | Fallback start command |

> **Action:** Update the evidence table after each production deploy with timestamp, operator, and command output snippets.

## Failure escalation

| Failure | Action |
|---------|--------|
| pytest red | Block deploy; fix tests first |
| doctor database FAIL | Check `DATABASE_URL` / network |
| `/health` error on Render | Check R2 creds + Postgres |
| No worker heartbeats | Verify worker service running, shared `DATABASE_URL` |
| `live_execution_enabled: true` | **Stop deploy** — reset env var |