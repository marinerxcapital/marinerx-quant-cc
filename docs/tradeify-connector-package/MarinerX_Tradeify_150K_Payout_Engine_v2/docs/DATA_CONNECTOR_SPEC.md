# MarinerX Tradeify + Tradovate Data Connector Spec

## Objective

Build a secure Python data ingestion layer inside MarinerX Labs that pulls:

1. Tradovate market data, positions, account balance, realized PnL, unrealized PnL, fills, and order state.
2. Tradeify / TFD dashboard account metrics, including account status, evaluation/funded phase, winning days, payout progress, drawdown headroom, consistency status, and payout eligibility.

The ingestion layer must feed the existing MarinerX modules:

- Risk Command
- Trade-or-No-Trade
- Execution & Orders
- Trade Journal
- Performance
- Reports
- Settings/System Control

This is a risk and payout-management overlay. It is not allowed to place live orders unless live execution is explicitly enabled and all risk gates approve the trade.

## Data Source Priority

| Priority | Source | Use |
|---:|---|---|
| 1 | Official Tradovate API / OAuth | Market data, account state, positions, fills, order state |
| 2 | Tradeify / TFD dashboard authenticated session | Prop-firm-specific metrics not available through Tradovate |
| 3 | Manual CSV import | Fallback for payout/trade-journal reconciliation |

## Required Data Model

Normalize all external data into these internal records:

### BrokerAccountMetrics

- source
- account_name
- account_id_hash
- balance
- net_liq
- cash_balance
- realized_day_pnl
- unrealized_pnl
- open_trade_risk
- eod_drawdown_floor
- positions
- observed_at
- raw metadata without secrets

### TradeifyDashboardMetrics

- source
- account_label
- phase
- account_size
- current_balance
- realized_day_pnl
- total_profit
- max_drawdown_limit
- drawdown_floor
- winning_days
- payout_eligible
- next_payout_cap
- last_payout_status
- consistency_current_pct
- observed_at
- raw metadata without secrets

### Merged AccountSnapshot

Use `connectors.normalizer.merge_to_account_snapshot()` to combine the broker and Tradeify metrics into the existing `AccountSnapshot` used by the risk engine.

## Required Backend Endpoints

Add these endpoints under the existing Tradeify router:

```text
GET  /api/tradeify/150k/data/status
POST /api/tradeify/150k/data/sync
GET  /api/tradeify/150k/data/latest
GET  /api/tradeify/150k/data/health
POST /api/tradeify/150k/data/validate-session
POST /api/tradeify/150k/data/reconcile
```

### Endpoint Behavior

| Endpoint | Behavior |
|---|---|
| `/data/status` | Returns connector enabled/disabled state, last sync time, last sync source, and stale-data status. |
| `/data/sync` | Pulls Tradovate + Tradeify dashboard metrics, normalizes them, saves to DB, and returns merged snapshot. |
| `/data/latest` | Returns latest cached snapshot. Must never force a dashboard login. |
| `/data/health` | Checks connector availability without exposing private account details. |
| `/data/validate-session` | Confirms dashboard/session state is valid. Must not expose cookies/tokens. |
| `/data/reconcile` | Compares broker PnL vs Tradeify dashboard PnL and flags mismatches. |

## Database Tables

Add tables/migrations compatible with the existing MarinerX database layer.

### tradeify_account_snapshots

- id
- workspace_id
- account_label
- phase
- account_size
- balance
- net_liq
- realized_day_pnl
- unrealized_pnl
- total_profit
- drawdown_floor
- drawdown_headroom
- winning_days
- payout_eligible
- next_payout_cap
- consistency_current_pct
- source
- observed_at
- created_at

### tradeify_sync_events

- id
- workspace_id
- sync_type: tradovate_api | tradeify_dashboard | csv_import | merged
- status: success | warning | failed
- started_at
- completed_at
- latency_ms
- error_code
- error_message_redacted

### tradovate_fills

- id
- workspace_id
- account_hash
- symbol
- side
- quantity
- price
- commission
- timestamp
- external_fill_hash
- created_at

### tradovate_positions

- id
- workspace_id
- account_hash
- symbol
- net_quantity
- average_price
- unrealized_pnl
- realized_pnl
- observed_at

## Risk Engine Integration

The synced snapshot must run through this sequence:

```text
Tradovate API + Tradeify Dashboard
    ↓
Connector Normalizer
    ↓
AccountSnapshot
    ↓
Risk Command
    ↓
Tradeify Risk Gate
    ↓
Trade-or-No-Trade Verdict
    ↓
Execution & Orders
```

No execution path may bypass the Tradeify Risk Gate.

## Stale Data Rules

| Data Age | System Behavior |
|---:|---|
| 0-15 seconds | Normal operation |
| 15-60 seconds | Allow analysis; require confirmation before order staging |
| 60-180 seconds | Block new trades; allow flatten-only |
| >180 seconds | Data stale; disable trading actions |

## Reconciliation Rules

Flag a warning when:

- Tradovate balance and dashboard balance differ by more than `$25`.
- Realized day PnL differs by more than `$25`.
- Dashboard phase conflicts with MarinerX phase.
- Winning-day count changes unexpectedly.
- Drawdown floor is missing or lower confidence than expected.

If reconciliation fails, the system must default to `BLOCK` for new trades.

## Security Constraints

- Never store raw account IDs in logs; hash account identifiers.
- Never store passwords in plaintext.
- Never log dashboard HTML, cookies, OAuth tokens, or session storage.
- Never put user credentials in prompts.
- Use environment variables or a secret manager.
- Browser dashboard automation must respect MFA and must not bypass security controls.
- Dashboard scraping must be read-only: no payout request clicks, profile edits, or platform changes.

## Execution Constraints

Default mode:

```env
MARINERX_ALLOW_LIVE_ORDERS=false
MARINERX_TRADEIFY_DATA_ENABLED=true
MARINERX_TRADEIFY_DASHBOARD_ENABLED=false
MARINERX_TRADOVATE_ENVIRONMENT=demo
```

Live order mode can only be enabled when:

1. Unit tests pass.
2. Replay tests pass.
3. Dashboard sync works.
4. Tradovate sync works.
5. Manual kill switch works.
6. Risk gate blocks correctly under stale data.
7. User explicitly sets `MARINERX_ALLOW_LIVE_ORDERS=true`.
