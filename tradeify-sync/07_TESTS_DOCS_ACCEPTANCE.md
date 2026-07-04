# PHASE 07 — TESTS · DOCS · FINAL ACCEPTANCE

**CONTEXT:** Phases 01–06 complete. Now harden with a full test suite, write the operator documentation, and run the master acceptance checklist. Do not consider the project done until every checklist item passes.

---

## 1. Test Suite (`tests/`) — implement all, `pytest` + `pytest-asyncio`

`conftest.py` fixtures: in-memory sqlite engine/session; loaded HTML fixtures; a fake Playwright `Page` (records `.click()`/`.goto()` calls) for guard/pagination tests; a frozen-time helper.

| File | Must assert |
|---|---|
| `test_config.py` | valid `config.yaml` loads; invalid (cadence below min, non-https base_url) raises `ConfigError`. |
| `test_models_hash.py` | each model's `build_hash()` is stable + 64 hex; different inputs differ. |
| `test_guards.py` | allowlist pass/deny; mutating denylist blocks buy/sell/withdraw/reset/close/flatten/liquidate; benign controls pass; scraper code contains **no** direct `.click(` outside `guarded_click` (grep test). |
| `test_session.py` | valid marker ⇒ session valid; missing marker ⇒ invalid; no mutation occurs. |
| `test_table_sniffer.py` | intended table ranked #1; ≥ 80% column-map accuracy on fixture. |
| `test_selector_resolution.py` | primary-miss/fallback-hit returns locator; all-miss raises `SelectorResolutionError`. |
| `test_scrapers_parsing.py` | row counts + keyed fields correct; pagination union; export-first path skips DOM extraction. |
| `test_normalize.py` | money/qty cleaners; symbol roots (CL/NQ/ES/GC + micros); ET→UTC across DST. |
| `test_repository_dedup.py` | second identical batch ⇒ `trades_new == 0`; `replace_positions` leaves only current snapshot. |
| `test_pipeline_partial.py` | one account raising ⇒ run status `PARTIAL`, others still persisted; `AuthError` ⇒ `FAILED`, no retry. |
| `test_scheduler_lock.py` | overlapping tick skipped via single-flight lock (fake clock). |

Target ≥ 70% coverage on `src/tradeify_sync/` core modules.

## 2. `README.md` (write in full)
Sections: Overview & read-only safety posture; Prerequisites; Install (`uv sync`, `playwright install chromium`); Configure (`config.yaml` `base_url`, `.env` from `.env.example`); **First run** (`python main.py discover` → walk-through, then `python main.py sync`); Scheduling (`python main.py schedule`); Operating commands (`status`, `doctor`, `backfill`, `export`); **Repairing selectors after a Tradeify UI change** (`discover --page X` updates only that page — no code edits); Quant Hub integration (enable bus, event schema); Data locations (sqlite, parquet, screenshots, logs); Troubleshooting (2FA/manual-assist, session expiry, Cloudflare/challenge → run headed `login`, then `sync`); Limitations & compliance note (read-only, local-only, respects platform; verify automated access aligns with your account agreement).

## 3. Quality config
Ensure `ruff` and `mypy --strict src/` are clean across the whole tree; `pyproject.toml` includes `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`.

---

## MASTER ACCEPTANCE CHECKLIST (run and report PASS/FAIL per line)
- [ ] `uv sync && playwright install chromium` succeeds from clean.
- [ ] `python main.py doctor` → all green.
- [ ] `python main.py discover` → valid `selectors.yaml`, all `column_map` fields exist on models.
- [ ] `python main.py sync` → full read-only sync; `SyncRun` = OK; parquet written.
- [ ] Second `python main.py sync` → `trades_new == 0` (idempotent).
- [ ] `python main.py status` → per-account `drawdown_headroom` shown.
- [ ] `pytest` green; read-only guard + dedup + partial-failure tests included.
- [ ] `ruff` clean; `mypy --strict src/` clean.
- [ ] No `.click(` in scrapers outside `guarded_click`; no credentials/HTML in logs.
- [ ] README enables a new operator to reach a first successful sync unaided.

When every box is checked, output a final build report: file tree actually produced, test results summary, coverage %, and any deviations from this package with justification.
