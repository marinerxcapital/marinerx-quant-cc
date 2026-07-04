# PHASE 03 — DISCOVERY ENGINE (self-configuring selector layer)

**CONTEXT:** Phases 01–02 complete (config/models/schema; browser manager, guards, session, login). The live Tradeify DOM is unknown, so this phase builds the mechanism that discovers and records selectors instead of hard-coding them. This is the phase that keeps the whole system from being brittle.

---

## 1. `selectors.yaml` schema (define and document)
Each selector entry: `{ primary: str, fallbacks: list[str], wait: "visible"|"attached"|"enabled" }`. Pages: `login`, `accounts`, `trades`, `positions`, `payouts`. Each data page also carries a `column_map: { field_name: {index: int} | {selector: str} }` linking table columns to model fields, and an optional `export_button` entry. Ship the file pre-seeded with reasonable guesses (as in Master Brief examples) that discovery overwrites with confirmed values.

## 2. `src/tradeify_sync/discovery/table_sniffer.py`
Heuristic DOM analysis (operate on the rendered page via Playwright, read-only):
- `async find_repeating_structures(page)` → detect candidate data containers: (a) `<table>` elements ranked by row count; (b) repeating card/grid clusters (siblings sharing class signatures, count ≥ 3). Return ranked candidates with a CSS path, row count, and inferred column count.
- `async infer_headers(candidate)` → read `<thead>`/`<th>` or first-row labels; if absent, emit positional `col_0..col_n`.
- `propose_column_map(headers)` → fuzzy-match headers to model fields using a synonym table (e.g. `symbol|instrument|contract → symbol_raw`; `p/l|pnl|net → net_pnl`; `qty|size|contracts → qty`; `entry|open → entry_*`; `exit|close → exit_*`; `date|time → *_time`). Return a proposed `column_map` plus a confidence score per mapping.
- `async detect_export_control(page)` → search for elements whose text/attrs match `export|download|csv|statement`; return a candidate selector or `None`.
- Never click during sniffing; analysis only.

## 3. `src/tradeify_sync/discovery/recorder.py`
Interactive terminal workflow, invoked by `python main.py discover`:
1. Launch headed browser; run `ensure_authenticated` (manual login/2FA as needed); persist session.
2. For each page in `[accounts, trades, positions, payouts]`:
   - Prompt: "Navigate to your **{page}** page in the browser, then press Enter."
   - Run `table_sniffer` on the current page; print the top candidate, its inferred headers, and the proposed `column_map` with confidences.
   - Let the user (a) accept, (b) pick a different candidate by number, or (c) manually enter a CSS selector for the row container and/or override individual column indices.
   - Capture `pagination_next` and `export_button` candidates; ask the user to confirm.
   - Write confirmed `primary` selectors (with the pre-seeded guesses demoted to `fallbacks`), `wait` conditions, and `column_map` into `selectors.yaml`.
3. Re-runnable per page: `python main.py discover --page trades` updates only that page.
4. Validate the written YAML parses and every referenced field exists on the corresponding model; raise `SelectorResolutionError` otherwise.

## 4. Selector resolution utility (shared, put in `browser/` or `discovery/` — your call, export it)
- `async resolve(page, page_key, selector_key, selectors)` → try `primary`, then each `fallback` in order, honoring the `wait` mode with the config timeout. Return a Playwright `Locator`. Raise `SelectorResolutionError(page_key, selector_key)` with a `fail_shot` if none resolve. Log which selector won (key only).

---

## PHASE 03 ACCEPTANCE GATE
- `python main.py discover` runs the full guided flow against a real login and writes a `selectors.yaml` whose `column_map` fields all exist on the target models.
- Given a saved HTML fixture, `table_sniffer.find_repeating_structures` returns the intended data table as the top candidate and `propose_column_map` maps ≥ 80% of columns correctly (assert in `tests/test_table_sniffer.py`).
- `resolve()` falls back correctly: unit test where `primary` is absent but a `fallback` matches returns the locator; all-miss raises `SelectorResolutionError`.
- `ruff` + `mypy --strict src/` clean.

Deliver all Phase 03 files. Stop and await Phase 04.
