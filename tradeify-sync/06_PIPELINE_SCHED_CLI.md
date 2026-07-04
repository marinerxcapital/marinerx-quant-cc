# PHASE 06 — PIPELINE · SCHEDULER · INTEGRATION · CLI

**CONTEXT:** Phases 01–05 complete (foundation, browser/auth, discovery, scrapers, normalize/storage). Now assemble the orchestration, scheduling, Quant Hub integration, resilience, and the operator CLI.

---

## 1. `src/tradeify_sync/resilience/retry.py`
- `tenacity` policies: `transient_retry` (retry on `NavigationError`/network/timeout, exponential backoff, max 3, jitter) and a `no_retry_on_auth` guard so `AuthError` never retries.

## 2. `src/tradeify_sync/resilience/alerting.py`
- `alert(subject, detail, settings)` → desktop notification if available; email via `SMTP_URL` if configured; always structured-log. Called on `FAILED`/repeated challenge/logout.

## 3. `src/tradeify_sync/pipeline/sync.py` — the orchestrator
`async run_sync(settings, secrets)`:
1. `open_sync_run()`; configure logging with a fresh `run_id`.
2. `async with BrowserManager` → `ensure_authenticated`.
3. `scrape_accounts` → normalize → `upsert_account` (all accounts).
4. For each account:
   a. `since = last_trade_exit_utc(account)`; `scrape_trades(account, since, backfill_days)`; parse (CSV or rows) → normalize → `insert_ignore`.
   b. `scrape_fills` (if available) → normalize → `insert_ignore`.
   c. `scrape_open_positions` → `replace_positions`.
   d. `scrape_payouts` → `insert_ignore`.
   e. publish events to the bus (§4).
5. `export_parquet` if configured.
6. `close_sync_run(status)` where status = OK / PARTIAL (some account errored) / FAILED (auth/global). Per-account errors are caught, `fail_shot`-logged, and downgrade the run to PARTIAL without aborting other accounts.
7. Wrap network/nav steps with `transient_retry`; never retry `AuthError`.

## 4. Integration with the Command Center — no dedicated module needed by default
- **Default (both projects local, or Command Center reads a shared volume):** no integration code required. The Command Center's `AccountSync` agent (part of the MarinerX Quant Command Center package) reads `data/tradeify_sync.db` directly via a read-only SQLite connection in WAL mode. This project's job ends at writing correct, deduplicated, WAL-mode SQLite — nothing to build here.
- **Only if Command Center is deployed to Railway while this service stays local** (the recommended hybrid split — see Command Center `00B_PRE_FLIGHT_ADDENDUM.md` §1): add `src/tradeify_sync/integration/account_state_api.py`, a minimal `fastapi` app exposing `GET /api/account-state` (returns current `Account` rows + `last_synced_utc` as JSON), bound to `127.0.0.1` plus a reverse tunnel of the user's choosing (not directly exposed to the public internet), authenticated via a long random bearer token compared against `remote_read_api_bearer_token` from `.env`. Build this only if `integration.remote_read_api_enabled` is true in `config.yaml`; otherwise this module is not needed and should not be built.

## 5. `src/tradeify_sync/scheduler/runner.py`
- `start_scheduler(settings)` → `apscheduler` background scheduler; job runs `run_sync` every `cadence_minutes` with jitter; if `market_hours_only`, gate on CME RTH/ETH windows in `America/New_York`. Single-flight lock: skip a tick if the previous run is still active. Graceful shutdown on SIGINT.

## 6. `main.py` (Typer) — implement ALL commands
| Command | Behavior |
|---|---|
| `discover [--page P]` | Phase 03 guided discovery (all pages or one). |
| `login` | Establish/refresh persisted session only. |
| `sync` | One full `run_sync` now; print the `SyncRun` summary. |
| `backfill --days N` | Force historical backfill over N days for all accounts. |
| `schedule` | Start the background scheduler in the foreground. |
| `export --fmt parquet\|csv [--table T]` | Dump snapshots. |
| `status` | Last `SyncRun`, per-account `drawdown_headroom`, DB row counts. |
| `doctor` | Validate config + `.env`; check session validity; parse `selectors.yaml` and confirm each `column_map` field exists on its model; confirm DB reachable; print a green/red table. |

Each command loads `Settings`, configures logging, and exits nonzero on failure.

---

## PHASE 06 ACCEPTANCE GATE
- `python main.py doctor` prints an all-green table on a correctly configured environment and a clear red row for any missing piece.
- `python main.py sync` completes a full run against the live dashboard, writing a `SyncRun` row and parquet snapshots; a second immediate `sync` reports `trades_new == 0`.
- `python main.py status` shows per-account headroom.
- `schedule` respects `cadence_minutes`, applies jitter, and skips overlapping ticks (unit-test the single-flight lock with a fake clock).
- `ruff` + `mypy --strict src/` clean.

Deliver all Phase 06 files. Stop and await Phase 07.
