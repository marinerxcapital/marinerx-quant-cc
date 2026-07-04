# PHASE 00 — MASTER BRIEF (paste first; shared context for all later phases)

You are building **Tradeify Sync Engine**, a production-grade Python subsystem that authenticates into the user's **own** Tradeify dashboard in a browser (the user has no API access), reads their **own** account and trading data, normalizes it, and persists it for consumption by the MarinerX Quant Hub.

This message establishes shared context. Subsequent messages (Phases 01–07) will build the system in dependency order. Retain everything here for all later phases. Do not begin coding until Phase 01; treat this phase as specification only and reply with a one-paragraph confirmation of the architecture and the build order.

---

## 1. Non-Negotiable Constraints (enforce structurally, not by convention)

| # | Constraint | Enforcement requirement |
|---|-----------|-------------------------|
| C1 | **READ-ONLY** | Navigate and read only. Never place/modify/cancel orders, change settings, request withdrawals, or reset accounts. Implement a URL allowlist and a mutating-interaction denylist that raises before any such click. |
| C2 | **SESSION-PERSISTENT** | Reuse a persisted `storage_state.json`; log in only when the session is invalid. |
| C3 | **HUMAN-PACED** | Randomized delays between actions (default 800–2500 ms); never concurrent requests to the dashboard; default cadence ≥ 5 min, human-realistic. |
| C4 | **LOCAL-ONLY** | Runs on the user's machine. Credentials in `.env`/keyring only; transmitted solely to the Tradeify login form over HTTPS. Never logged. |
| C5 | **EXPORT-FIRST** | If a page exposes a native CSV/statement export, download it instead of scraping the DOM. DOM extraction is the fallback. |
| C6 | **MULTI-ACCOUNT** | Enumerate and iterate all accounts; tag every record with `account_id`. |
| C7 | **IDEMPOTENT** | Re-running a sync inserts zero duplicates; enforced by deterministic `source_hash` UNIQUE constraints. |
| C8 | **OBSERVABLE** | Structured JSON logs; screenshot on every extraction failure; a `SyncRun` audit row per execution. |

---

## 2. Tech Stack (use exactly these; pin versions)

| Layer | Choice |
|-------|--------|
| Language | Python 3.11+, fully type-hinted; `mypy --strict` clean on `src/` |
| Packaging | `pyproject.toml`, `uv`-compatible, pinned versions |
| Browser | **Playwright** (Python, chromium), persistent context |
| Models | `pydantic` v2 |
| ORM/DB | `sqlalchemy` 2.x + sqlite; `pyarrow`/`pandas` for parquet/CSV |
| Config | `pydantic-settings` + `config.yaml`; DOM map in `selectors.yaml`; secrets in `.env` |
| Scheduler | `apscheduler` |
| Retries | `tenacity` |
| Logging | `structlog` + rotating file handler |
| Secrets | `python-dotenv` (+ optional `keyring`); TOTP via `pyotp` |
| CLI | `typer` |
| Tests | `pytest`, `pytest-asyncio` |
| Lint/format | `ruff` |

---

## 3. Canonical File Tree (authoritative; all phases populate this)

```
tradeify-sync/
├── pyproject.toml
├── config.yaml
├── selectors.yaml
├── .env.example
├── .gitignore
├── README.md
├── main.py
├── src/tradeify_sync/
│   ├── __init__.py
│   ├── config.py
│   ├── constants.py
│   ├── models.py
│   ├── auth/            {login.py, session.py}
│   ├── browser/         {manager.py, humanize.py, guards.py}
│   ├── scrapers/        {base.py, accounts.py, trades.py, positions.py, payouts.py, exports.py}
│   ├── discovery/       {recorder.py, table_sniffer.py}
│   ├── storage/         {db.py, schema.py, repository.py, exporters.py}
│   ├── normalize/       {mapper.py, instruments.py}
│   ├── scheduler/       {runner.py}
│   ├── integration/     {account_state_api.py}   # OPTIONAL: minimal authenticated read endpoint, only if Command Center runs on Railway (see Command Center Addendum §1). Default: none needed — Command Center reads data/tradeify_sync.db directly.
│   ├── pipeline/        {sync.py}
│   ├── resilience/      {retry.py, alerting.py}
│   └── utils/           {logging.py, timeparse.py}
├── data/                {sessions/, downloads/, parquet/, tradeify_sync.db}
├── logs/
├── screenshots/
└── tests/               {conftest.py, test_*.py, fixtures/*.html}
```

---

## 4. Coding Standards (apply to every phase)

1. **Typing:** every function and method fully annotated; `Decimal` for all money/prices (never `float`); tz-aware `datetime` only.
2. **Docstrings:** every public class/function has a concise docstring stating purpose, args, returns, raises.
3. **Errors:** custom exception hierarchy in `constants.py` (`TradeifySyncError` → `AuthError`, `NavigationError`, `ExtractionError`, `SelectorResolutionError`, `IntegrityError`). No bare `except`.
4. **No side effects on import.** All I/O behind functions/classes.
5. **Security:** never log credentials, tokens, or full page HTML — log selector keys, row counts, timings only.
6. **Determinism:** all persisted timestamps in UTC; display parsing uses the configured dashboard tz.
7. **Time:** store UTC, parse `America/New_York` (DST-aware) unless config overrides.

---

## 5. Global Acceptance Gates (final system)

- Clean install: `uv sync && playwright install chromium`.
- `python main.py doctor` → all checks green (config valid, `.env` present, session state resolvable, selector file parses, DB reachable).
- `python main.py discover` → writes a valid `selectors.yaml` with confirmed column maps.
- `python main.py sync` → full read-only sync; a second immediate `sync` inserts **0** duplicate trades/fills/payouts.
- `pytest` green, including `test_guards.py` (read-only) and `test_repository_dedup.py` (idempotency).
- `ruff` clean; `mypy --strict src/` clean.

---

## 6. Build Order

01 Scaffold/Config/Models → 02 Browser/Auth → 03 Discovery → 04 Scrapers/Exports → 05 Normalize/Storage → 06 Pipeline/Scheduler/CLI → 07 Tests/Docs/Acceptance.

Confirm understanding, then await Phase 01.
