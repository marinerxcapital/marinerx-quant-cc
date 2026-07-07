# API Reference

Base URL: `http://localhost:8000` (local)

## System Truth (Phase 2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/version` | Service version |
| GET | `/config-check` | Env var presence check |
| GET | `/api/system-state` | NOMINAL/STALE/DEGRADED/LOCKED |
| GET | `/api/data-freshness` | Per-source freshness |

## Strategy Registry

| Method | Path |
|--------|------|
| GET | `/api/strategies` |
| GET | `/api/strategies/{id}` |
| POST | `/api/strategies` |
| PATCH | `/api/strategies/{id}` |
| POST | `/api/strategies/{id}/archive` |

## Backtest

| Method | Path |
|--------|------|
| POST | `/api/backtests/run` |

## Risk Command

| Method | Path |
|--------|------|
| GET | `/api/risk/state` |
| POST | `/api/risk/settings` |
| POST | `/api/risk/kill-switch` |
| POST | `/api/risk/clear-kill-switch` |
| POST | `/api/risk/check-order` |

## Trade Decision

| Method | Path |
|--------|------|
| POST | `/api/decision/evaluate` |

## Tier 2 Platform

| Method | Path |
|--------|------|
| GET | `/api/instruments` |
| GET | `/api/market/bars` |
| GET | `/api/market/snapshot` |
| GET | `/api/macro/series` |
| POST | `/api/data/sync` |
| POST | `/api/validation/run` |
| GET | `/api/regime/current` |
| GET | `/api/orders` |
| POST | `/api/orders/paper` |
| POST | `/api/orders/{id}/cancel` |
| GET | `/api/account/paper` |
| GET/POST/PATCH/DELETE | `/api/journal` |
| GET | `/api/performance/summary` |
| GET/POST | `/api/reports` |
| GET | `/api/reports/{id}` |

## Agent Data (3b757e0)

| Method | Path |
|--------|------|
| GET | `/api/agents/snapshot` |
| GET | `/api/agents/market-pulse` |
| GET | `/api/agents/indicators/{symbol}` |
| GET | `/api/agents/journal` |