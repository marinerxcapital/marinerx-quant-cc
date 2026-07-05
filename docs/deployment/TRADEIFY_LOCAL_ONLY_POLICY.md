# Tradeify Local-Only Policy

**Policy:** Tradeify browser automation runs **only on local developer machines**. It is **blocked** in cloud and production runtimes.

## Rationale

- `tradeify-sync/` contains **9 markdown spec files only** — no Python automation ships in this repo.
- Browser automation (Playwright) requires persistent sessions, CAPTCHAs, and desktop-like environments unsuitable for Render/Railway workers.
- Cloud automation increases credential exposure and violates prop-firm ToS risk.
- Account sync in production must use read-only adapters, not browser scrapers.

## Implementation

**Guard module:** `src/mcc/core/tradeify_guard.py`  
**Exception:** `CloudTradeifyAutomationBlockedError` in `src/mcc/core/exceptions.py`

```python
assert_tradeify_automation_allowed(routine_name="tradeify_browser_automation", settings=...)
```

### Block conditions

Automation is blocked when **any** of these apply:

| Condition | Detection |
|-----------|-----------|
| Production/staging env | `settings.is_production` (`APP_ENV` = `production`, `prod`, `staging`) |
| Cloud runtime | `is_cloud_runtime()` — `RENDER`, `RAILWAY_*`, `CF_PAGES`, `VERCEL`, `FLY_APP_NAME` |
| Non-local service mode | `SERVICE_MODE` in `web`/`worker` and `not settings.is_local` |

On block: structured log `tradeify_automation_blocked` + raise `CloudTradeifyAutomationBlockedError`.

### Allowed

```env
APP_ENV=local
# No cloud runtime env markers set
```

Local developers may implement Tradeify automation per specs in `tradeify-sync/` on their machine only.

## What is NOT in the repo

| Item | Status |
|------|--------|
| Playwright / Selenium imports in `src/mcc/` | **Absent** |
| Playwright in `Dockerfile` | **Absent** |
| Python Tradeify scrapers | **Absent** — specs only at `tradeify-sync/` |
| Cloud browser automation | **Explicitly blocked** |

## Safe production paths

- `src/mcc/data/accounts/sync_adapter.py` — read-only consumer adapter (no browser)
- Manual CSV/export ingest locally → upload to R2 if needed
- Future: API-based sync if Tradeify offers official endpoints

## Integration point

Any future Tradeify automation entrypoint **must** call:

```python
from mcc.core.tradeify_guard import assert_tradeify_automation_allowed

def run_tradeify_export():
    assert_tradeify_automation_allowed(routine_name="tradeify_export")
    # ... local-only Playwright code ...
```

## Tests

```bash
python -m pytest tests/deployment/test_tradeify_guard.py -q
```

| Test | Expectation |
|------|-------------|
| `test_blocks_production_env` | Raises on `APP_ENV=production` |
| `test_blocks_cloud_runtime` | Raises when `RENDER=true` |
| `test_allows_local_dev` | Passes on local settings |

## Operations

- **Do not** set env vars to bypass the guard.
- **Do not** add Playwright to production Docker image.
- **Do not** run `tradeify-sync` automation on Render worker.
- If account data is needed in cloud, use pre-synced files in R2 or Postgres snapshots from local runs.

## Override

There is **no** env-var override. Local-only is a hard policy. Changing it requires code review, legal/ToS review, and explicit approval — not a dashboard toggle.