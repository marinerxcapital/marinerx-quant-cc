# Data Model

SQLite fallback locally; Postgres when `DATABASE_URL` is set.

## Core Tables

| Table | Purpose |
|-------|---------|
| `instruments` | Symbol metadata |
| `market_bars` | OHLCV bars (indexed symbol+timeframe+timestamp) |
| `market_snapshots` | Point-in-time snapshots |
| `macro_series` / `macro_observations` | Macro data |
| `regime_snapshots` | Regime classifier output |
| `strategies` | Strategy registry records |
| `strategy_versions` | Rule/parameter change history |
| `backtest_runs` | Persisted backtest results |
| `validation_results` | Validation verdicts |
| `trade_decisions` | Trade-or-no-trade evaluations |
| `orders` | Paper/live order attempts |
| `journal_entries` | Trade journal |
| `performance_daily` | Daily performance rollup |
| `risk_events` | Risk engine audit trail |
| `risk_settings` | Kill switch and limits |
| `reports` | Generated report index |
| `system_events` | System audit events |

## Legacy Tables (preserved)

`account_states`, `trades`, `decision_logs`, `report_metadata`, `agent_heartbeats`

## Common Fields

`id`, `created_at`, `updated_at`, `source`, `metadata_json` where applicable.