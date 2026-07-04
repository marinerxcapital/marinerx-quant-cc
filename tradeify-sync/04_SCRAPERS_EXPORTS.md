# PHASE 04 — SCRAPERS · EXPORTS (data extraction)

**CONTEXT:** Phases 01–03 complete (models/schema; browser+guards+session+login; discovery + `selectors.yaml` + `resolve()`). Now build the extraction layer. Every navigation goes through the allowlist; every click through `guarded_click`; every page prefers native export over DOM scraping (C5).

---

## 1. `src/tradeify_sync/scrapers/base.py`
`class BaseScraper` (constructed with `page`, `settings`, `selectors`, logger):
- `async goto(page_key)` → build URL from config, `assert_navigable`, navigate, `human_pause`.
- `async wait(page_key, selector_key)` → delegate to `resolve()`.
- `async try_export(page_key)` → if an `export_button` is configured/detected: `guarded_click` it, await the Playwright `download` event, save to `data/downloads/{page_key}_{timestamp}.csv`, return the file path; else return `None`.
- `async extract_rows(page_key)` → resolve `table_rows`; for each row, read cells per `column_map` (by index or relative selector); follow `pagination_next` via `guarded_click` until it disappears/disabled; return `list[dict]` of raw string cells keyed by field name. Enforce a max-page safety cap.
- `async fail_shot(context)` → screenshot to `screenshots/{page_key}_{ts}.png` + structured error log; raise `ExtractionError`.
- Scrapers return **raw dict rows**; normalization (Phase 05) converts to models. Keep extraction and normalization separate.

## 2. `src/tradeify_sync/scrapers/accounts.py`
- `async scrape_accounts()` → enumerate account rows/cards; for each account, collect the raw fields needed for the `Account` model, including drawdown/limit fields where displayed. If accounts are on separate detail pages, navigate into each (allowlist-checked) and back. Return `list[dict]`.

## 3. `src/tradeify_sync/scrapers/trades.py`
- `async scrape_trades(account_id, since_utc | None, backfill_days)`:
  - Set the date-range control if present: `since_utc` on incremental runs, else `today - backfill_days`.
  - `try_export` first; if a CSV is produced, return its path (parser in `exports.py` reads it). Else `extract_rows` with pagination.
  - Return either `{"csv": path}` or `{"rows": [...]}` so the pipeline knows the source.
- Also expose `async scrape_fills(account_id, ...)` if the dashboard exposes an executions/fills view; otherwise return empty and log that fills are unavailable.

## 4. `src/tradeify_sync/scrapers/positions.py`
- `async scrape_open_positions(account_id)` → snapshot current open positions as raw rows.

## 5. `src/tradeify_sync/scrapers/payouts.py`
- `async scrape_payouts(account_id)` → payout history + eligibility as raw rows.

## 6. `src/tradeify_sync/scrapers/exports.py`
- `read_export_csv(path, page_key, column_map)` → load via pandas, map columns using the same `column_map` semantics (header-name match preferred for CSVs), return `list[dict]` of raw string cells aligned to model field names. Handle encoding, thousands separators, currency symbols, and parenthesized negatives.

---

## PHASE 04 ACCEPTANCE GATE
- Against saved HTML fixtures (`tests/fixtures/*.html`), each scraper's `extract_rows` returns the expected number of rows with correctly keyed fields (`tests/test_scrapers_parsing.py`).
- Pagination test: a two-page fixture yields the union of both pages and stops when `pagination_next` is disabled.
- Export-first test: when an `export_button` resolves, `try_export` is used and `extract_rows` is **not** called (assert via a spy/mock).
- All clicks in tests are shown to pass through `guarded_click` (no direct `.click()` in scraper code — grep-assertable).
- `ruff` + `mypy --strict src/` clean.

Deliver all Phase 04 files. Stop and await Phase 05.
