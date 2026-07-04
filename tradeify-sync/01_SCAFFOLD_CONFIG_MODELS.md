# PHASE 01 — SCAFFOLD · CONFIG · MODELS · SCHEMA

**CONTEXT:** You have the Master Brief (Phase 00). Now build the foundation of `tradeify-sync/`. Produce complete, runnable code for every file in this phase. At the end, the package must import cleanly and create its DB tables.

Build the following, in full.

---

## 1. `pyproject.toml`
- Project metadata; Python `>=3.11`.
- Pinned dependencies: `playwright`, `pydantic>=2`, `pydantic-settings`, `sqlalchemy>=2`, `pandas`, `pyarrow`, `apscheduler`, `tenacity`, `structlog`, `python-dotenv`, `keyring`, `pyotp`, `typer`, `pyyaml`.
- Dev deps: `pytest`, `pytest-asyncio`, `ruff`, `mypy`.
- `[tool.ruff]` (line length 100, select E/F/I/UP/B) and `[tool.mypy]` (`strict = true`, `files = ["src"]`).

## 2. `.gitignore`
Exclude: `.env`, `data/sessions/`, `data/downloads/`, `data/*.db`, `logs/`, `screenshots/`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `*.parquet`.

## 3. `.env.example`
```
TRADEIFY_USERNAME=
TRADEIFY_PASSWORD=
TRADEIFY_TOTP_SECRET=        # optional; blank => manual-assist 2FA
ALERT_EMAIL=                 # optional
SMTP_URL=                    # optional
```

## 4. `config.yaml`
Fully commented, with these blocks and defaults: `tradeify` (base_url placeholder, login_path), `browser` (headless:false, persist_session:true, session_path, humanize min/max delay, timeout_ms:30000), `sync` (cadence_minutes:20, market_hours_only:true, timezone_display:"America/New_York", timezone_store:"UTC", backfill_days_on_first_run:90, min_cadence_minutes:5), `storage` (sqlite_path, parquet_dir, export_after_each_sync:true), `integration` (remote_read_api_enabled:false — see comment in the config for the Railway hybrid case), `instruments` (NQ 0.25/5.00, ES 0.25/12.50, CL 0.01/10.00, GC 0.10/10.00), `logging` (level:INFO, json:true, dir:"logs").

## 5. `src/tradeify_sync/config.py`
- `pydantic-settings` models mirroring `config.yaml` + a `Secrets` model from `.env`.
- `Settings.load()` classmethod: read YAML, merge env, **validate** (e.g. `cadence_minutes >= min_cadence_minutes`, base_url is https, session_path parent exists or is created). Raise `ConfigError` on invalid.
- Expose a cached `get_settings()` singleton.

## 6. `src/tradeify_sync/constants.py`
- Exception hierarchy (per Master Brief §4.3).
- `URL_ALLOWLIST_PATTERNS: list[str]` — regex of navigable dashboard paths (accounts, trades/history, positions, payouts, dashboard root, login). Everything else is denied.
- `MUTATING_INTERACTION_DENYLIST: list[str]` — case-insensitive substrings/regex for text or attributes that indicate state-mutating controls: `buy`, `sell`, `submit order`, `place order`, `close position`, `flatten`, `liquidate`, `withdraw`, `request payout`, `reset account`, `delete`, `save settings`, `confirm`. Used by `browser/guards.py`.
- `INSTRUMENT_ROOTS: dict[str, tuple[Decimal, Decimal]]` — root → (tick_size, tick_value), seeded from config at runtime (constant holds the fallback defaults).

## 7. `src/tradeify_sync/utils/logging.py`
- `configure_logging(level, json, dir)` → structlog with a rotating file handler (`logs/tradeify_sync.log`, 10 MB × 5) plus console renderer. Bind a `run_id` contextvar. Provide `get_logger(name)`.
- Redaction processor that drops keys named `password`, `token`, `secret`, `cookie`, `html`.

## 8. `src/tradeify_sync/utils/timeparse.py`
- `to_utc(dt_or_str, display_tz)` and `parse_dashboard_timestamp(raw, display_tz)` handling common formats (`MM/DD/YYYY HH:MM:SS`, ISO, epoch ms), DST-aware via `zoneinfo`. Always return tz-aware UTC.
- `canonical_iso(dt)` for hashing.

## 9. `src/tradeify_sync/models.py` (Pydantic v2 — implement ALL, with validators)

Use `Decimal` for money/prices, tz-aware UTC datetimes, and a `source_hash` computed via a `@computed_field` or explicit `build_hash()` method (SHA-256 of the canonical string defined per model). Enums: `Phase(EVAL,FUNDED,PA)`, `Side(LONG,SHORT)`, `OrderSide(BUY,SELL)`, `SyncStatus(OK,PARTIAL,FAILED)`.

- **Account**: `account_id, nickname, program, phase, size_usd, platform, status, balance, equity, high_water_mark, trailing_dd_amount, trailing_dd_floor, drawdown_headroom, daily_loss_limit, daily_pnl, days_traded, consistency_metric, payout_eligible, last_synced_utc`. Validator: if `equity` and `trailing_dd_floor` present, compute `drawdown_headroom = equity - trailing_dd_floor`.
- **Trade**: `trade_id, account_id, symbol_raw, symbol, side, qty, entry_time_utc, entry_price, exit_time_utc, exit_price, gross_pnl, fees, net_pnl, duration_sec, source_hash`. Hash string: `account_id|symbol_raw|side|qty|entry_iso|entry_price|exit_iso|exit_price`.
- **Fill**: `fill_id, account_id, symbol_raw, side(OrderSide), qty, price, timestamp_utc, order_id, source_hash`. Hash: `account_id|symbol_raw|side|qty|price|ts_iso|order_id`.
- **Position**: `account_id, symbol, side, qty, avg_price, unrealized_pnl, snapshot_utc`.
- **PayoutRecord**: `account_id, request_date_utc, amount, status, processed_date_utc, source_hash`. Hash: `account_id|request_iso|amount`.
- **DailyPnLSnapshot**: `account_id, trade_date, starting_balance, ending_balance, realized_pnl, source_hash`. Hash: `account_id|trade_date_iso`.
- **SyncRun**: `run_id, started_utc, finished_utc, accounts_synced, trades_new, fills_new, errors, status`.

## 10. `src/tradeify_sync/storage/db.py` & `schema.py`
- `schema.py`: SQLAlchemy 2.x `DeclarativeBase` + one table per persisted model (`accounts, trades, fills, positions, payouts, daily_pnl, sync_runs`). UNIQUE constraints on `source_hash` for `trades, fills, payouts, daily_pnl`. `accounts.account_id` primary key. Proper column types (`Numeric` for Decimal, `DateTime(timezone=True)`).
- `db.py`: engine factory from `Settings`, `init_db()` (create_all), `session_scope()` context manager.

---

## PHASE 01 ACCEPTANCE GATE
- `python -c "from tradeify_sync.config import get_settings; get_settings()"` succeeds against the default `config.yaml`.
- `python -c "from tradeify_sync.storage.db import init_db; init_db()"` creates `data/tradeify_sync.db` with all tables.
- Each model's `build_hash()` returns a stable 64-char hex for fixed inputs (include a tiny inline self-check or a `tests/test_models_hash.py`).
- `ruff` clean; `mypy --strict src/` clean.

Deliver all Phase 01 files complete. Then stop and await Phase 02.
