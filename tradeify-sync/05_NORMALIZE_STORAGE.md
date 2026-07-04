# PHASE 05 — NORMALIZE · STORAGE (mapping, dedup, persistence)

**CONTEXT:** Phases 01–04 complete. Scrapers now return raw dict rows (or CSV paths already parsed to raw dicts). This phase converts raw data into validated models and persists them idempotently.

---

## 1. `src/tradeify_sync/normalize/instruments.py`
- `root_from_symbol(raw)` → strip contract month/year codes to the root: `CLQ6 → CL`, `MNQU25 → MNQ`, `ESZ2025 → ES`. Handle micro prefixes (`M` → keep as `MNQ`, `MES`, `MCL`, `MGC` distinct from full-size). Use a regex + known-root table.
- `specs_for(root, settings)` → return `(tick_size, tick_value)` from config, defaulting from `INSTRUMENT_ROOTS`.
- `contract_month(raw)` → optional parse of month/year for reference.

## 2. `src/tradeify_sync/normalize/mapper.py`
- `to_account(raw, now_utc)` → `Account`; coerce money strings to `Decimal` (strip `$`, commas, handle `(x)` negatives), compute `drawdown_headroom`.
- `to_trade(raw, account_id, display_tz)` → `Trade`; normalize symbol, parse entry/exit timestamps to UTC, compute `duration_sec` and `net_pnl` if only gross+fees present, then `build_hash()`.
- `to_fill(...)`, `to_position(...)`, `to_payout(...)`, `to_daily_pnl(...)` analogously.
- A shared `money(raw) -> Decimal` and `qty(raw) -> int` cleaner with unit tests.
- Raise `IntegrityError` on unparseable required fields (never silently coerce to 0).

## 3. `src/tradeify_sync/storage/repository.py`
- `upsert_account(session, account)` → merge on `account_id`, always refresh `last_synced_utc`.
- `insert_ignore(session, model_rows)` for `Trade/Fill/PayoutRecord/DailyPnLSnapshot` → INSERT with `ON CONFLICT(source_hash) DO NOTHING`; return count actually inserted (drives `SyncRun.trades_new` / `fills_new`).
- `replace_positions(session, account_id, positions)` → delete existing open snapshot for the account, insert current set (positions are point-in-time).
- Query helpers: `last_trade_exit_utc(session, account_id)` (drives incremental range), `account_headroom(session, account_id)`, `open_sync_run()/close_sync_run()`.
- All writes inside `session_scope()`; commit once per logical batch.

## 4. `src/tradeify_sync/storage/exporters.py`
- `export_parquet(settings)` → dump `accounts, trades, payouts, daily_pnl` to `data/parquet/{table}.parquet` (overwrite) and current `positions` snapshot.
- `export_csv(settings, table)` on demand.

---

## PHASE 05 ACCEPTANCE GATE
- `tests/test_normalize.py`: money/qty cleaners handle `$1,234.50`, `(250.00)` → `-250.00`, `3` → `3`; symbol roots resolve for CL/NQ/ES/GC + micros; timestamps convert ET→UTC across a DST boundary.
- `tests/test_repository_dedup.py`: inserting the same batch twice yields `trades_new > 0` the first time and `== 0` the second (idempotency proof, satisfies C7).
- `replace_positions` leaves exactly the current snapshot (no stale rows).
- `ruff` + `mypy --strict src/` clean.

Deliver all Phase 05 files. Stop and await Phase 06.
