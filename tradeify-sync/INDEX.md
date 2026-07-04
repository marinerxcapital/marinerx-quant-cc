# MarinerX Tradeify Sync Engine — SuperGrok Build Package

A phased, dependency-ordered prompt package for building a production-grade, **read-only** Tradeify dashboard data-ingestion system in Python. Feeds the MarinerX Quant Hub (`PropGuardian`, `TradeJournal`, `PerformanceAnalyst`).

---

## How To Use This Package

1. Paste **`00_MASTER_BRIEF.md`** into SuperGrok first. It is shared context every later phase assumes. Do not skip it.
2. Then paste phases **01 → 07 in order**, one at a time. Wait for each phase to complete and its acceptance gate to pass before pasting the next.
3. Each phase prompt opens with a `CONTEXT` block restating what already exists, so the builder never loses the thread between messages.
4. If a phase's acceptance gate fails, paste the failing item back to SuperGrok and have it repair *within that phase* before advancing. Do not proceed on a failed gate.

---

## Build Order & Dependencies

```
00_MASTER_BRIEF            (context for all)
        │
01_SCAFFOLD_CONFIG_MODELS  (foundation: config, models, ORM, logging)
        │
02_BROWSER_AUTH            (Playwright, guards, session, login)  ── depends on 01
        │
03_DISCOVERY               (selectors.yaml generation)           ── depends on 01,02
        │
04_SCRAPERS_EXPORTS        (data extraction)                     ── depends on 01,02,03
        │
05_NORMALIZE_STORAGE       (mapping, dedup, persistence)         ── depends on 01,04
        │
06_PIPELINE_SCHED_CLI      (orchestration, scheduler, CLI)       ── depends on 01–05
        │
07_TESTS_DOCS_ACCEPTANCE   (test suite, README, final gate)      ── depends on all
```

---

## Global Success Definition

The build is complete only when, from a clean checkout:
- `uv sync && playwright install chromium` succeeds
- `python main.py doctor` reports all green
- `python main.py discover` produces a valid `selectors.yaml` against a real login
- `python main.py sync` performs a full read-only sync and a second `sync` inserts **zero** duplicate rows
- `pytest` passes, including the read-only guard test and the idempotency test
- `ruff` and `mypy --strict src/` are clean

---

## Two Inputs Only You Can Supply

1. **Dashboard domain** — one line in `config.yaml` (`tradeify.base_url`).
2. **First-run discovery pass** — `python main.py discover` (you log in manually once; the tool captures selectors and persists the session).

---

## Files In This Package

| File | Phase |
|------|-------|
| `INDEX.md` | This guide |
| `00_MASTER_BRIEF.md` | Shared context |
| `01_SCAFFOLD_CONFIG_MODELS.md` | Foundation |
| `02_BROWSER_AUTH.md` | Browser + auth |
| `03_DISCOVERY.md` | Selector discovery |
| `04_SCRAPERS_EXPORTS.md` | Extraction |
| `05_NORMALIZE_STORAGE.md` | Normalize + persist |
| `06_PIPELINE_SCHED_CLI.md` | Orchestration |
| `07_TESTS_DOCS_ACCEPTANCE.md` | Tests + final gate |
