# GROK MASTER BUILD PROMPT — MarinerX Tradeify 150K Data Connector + Payout Engine

## Role

You are Grok Heavy acting as the lead implementation engineer for the existing MarinerX Labs project.

You must run specialized subagents in parallel, then merge their work into one production-safe implementation.

## Project Location

Use the current MarinerX Labs repository/folder that Skyler is working from. If the repo is not already open, ask the terminal/user for the exact path before editing files. Do not create a disconnected prototype.

Live reference URL:

```text
https://marinerx-labs-api.onrender.com/#home
```

## Main Objective

Integrate a Python-based Tradeify 150K Select Flex account data system into MarinerX Labs.

The system must:

1. Pull Tradovate account and market data.
2. Pull Tradeify / TFD dashboard metrics by logging into the user's own dashboard session.
3. Normalize the data into MarinerX account snapshots.
4. Feed Risk Command, Trade-or-No-Trade, Execution & Orders, Trade Journal, Performance, Reports, and Settings.
5. Track Tradeify Select 150K evaluation rules.
6. Track Tradeify Select Flex 5-day payout progress.
7. Help the user manage risk toward the max payout target.
8. Keep live order execution disabled unless explicitly enabled and risk-gated.

This is not a guaranteed-profit bot. This is a risk-first, payout-progress, account-telemetry, and execution-control overlay.

## Hard Security Rules

Do not put credentials in code, prompts, commits, logs, screenshots, or frontend responses.

Do not ask the user to paste credentials into chat.

Do not bypass MFA, CAPTCHA, device approval, or platform security.

Use one of these approved methods:

1. Tradovate official API / OAuth / API credentials from environment variables or secret manager.
2. Tradeify/TFD dashboard Playwright manual login bootstrap that stores protected `storage_state` locally.
3. Deployment secrets for production runtime.

Live trading must remain off by default:

```env
MARINERX_ALLOW_LIVE_ORDERS=false
MARINERX_TRADEIFY_DATA_ENABLED=true
MARINERX_TRADEIFY_DASHBOARD_ENABLED=false
MARINERX_TRADOVATE_ENABLED=true
MARINERX_TRADOVATE_ENVIRONMENT=demo
```

## Tradeify 150K Select Rules To Encode

Evaluation:

- Starting balance: `$150,000`
- Profit target: `$9,000`
- Max EOD drawdown: `$4,500`
- Daily loss limit: none
- Evaluation consistency: largest winning day must be <= `40%` of total profit
- Max size: `12 minis / 120 micros`

Funded Select Flex / 5-day payout:

- Winning days required: `5`
- 150K winning day threshold: `$250`
- Payout formula: up to `50%` of total profits
- Payout cap: `$5,000` gross
- Trader split: `90%`
- Max gross payout requires approximately `$10,000` total funded profit
- Funded consistency rule: none for Select Flex, but keep risk controls active

## MarinerX Internal Risk Policy

Default stricter rules:

- Risk per trade: `$250`
- Daily loss soft stop: `$750`
- Hard daily stop: `$900`
- Emergency flatten/block threshold: drawdown headroom <= `$1,500`
- First payout not recommended below `+$4,500` funded profit cushion
- Max payout target: `+$10,000` funded profit
- If data stale: block new trades
- If dashboard and broker disagree materially: block new trades

## Required Build Modules

### 1. Tradovate Connector

Implement `src/marinerx_tradeify/connectors/tradovate_connector.py`.

Capabilities:

- Authenticate to Tradovate official API.
- Support demo/simulation environment by default.
- Fetch account list.
- Select the correct Tradeify 150K account.
- Fetch balance/equity/cash data.
- Fetch positions.
- Fetch fills.
- Fetch orders.
- Subscribe to market data snapshots for NQ/MNQ, ES/MES, CL/MCL, GC/MGC.
- Normalize to `BrokerAccountMetrics`.

Do not enable order placement in this phase unless the existing MarinerX project already has a safe execution gateway. If order endpoints exist, wrap them behind the risk gate and `MARINERX_ALLOW_LIVE_ORDERS=false` default.

### 2. Tradeify / TFD Dashboard Connector

Implement `src/marinerx_tradeify/connectors/tradeify_dashboard_connector.py`.

Capabilities:

- Use Playwright.
- Provide manual login bootstrap command.
- Save browser `storage_state` to a protected path.
- Reuse saved session for headless read-only scraping.
- Extract dashboard metrics:
  - Account label
  - Account size
  - Phase/status
  - Current balance
  - Daily PnL
  - Total profit
  - Drawdown floor/headroom
  - Winning days
  - Payout eligibility
  - Next payout cap/status
  - Consistency percentage during evaluation
  - Last payout status when visible
- Normalize to `TradeifyDashboardMetrics`.

Do not click payout buttons. Do not change account settings. Do not scrape private data beyond account metrics needed by MarinerX.

### 3. Normalizer and Reconciliation

Implement/complete:

```text
src/marinerx_tradeify/connectors/normalizer.py
```

Required behavior:

- Merge Tradovate broker metrics with Tradeify dashboard metrics.
- Produce existing `AccountSnapshot` model.
- Hash sensitive account IDs.
- Compare Tradovate vs Tradeify values.
- Mark data stale when timestamps exceed thresholds.
- Emit warnings for mismatches greater than `$25` in balance or realized PnL.
- Default to `BLOCK` if reconciliation fails.

### 4. Persistence

Add database tables/migrations compatible with existing MarinerX backend:

```text
tradeify_account_snapshots
tradeify_sync_events
tradovate_fills
tradovate_positions
```

Do not add mock data.

Store normalized metrics, not raw credentials/session tokens.

### 5. FastAPI Endpoints

Add endpoints:

```text
GET  /api/tradeify/150k/data/status
POST /api/tradeify/150k/data/sync
GET  /api/tradeify/150k/data/latest
GET  /api/tradeify/150k/data/health
POST /api/tradeify/150k/data/validate-session
POST /api/tradeify/150k/data/reconcile
```

Existing endpoints must remain working:

```text
GET  /api/tradeify/150k/rules
POST /api/tradeify/150k/eval/status
POST /api/tradeify/150k/payout/status
POST /api/tradeify/150k/risk/gate
```

### 6. UI Integration

Add or update MarinerX UI panels:

#### Settings / System Control

- Tradovate connector status
- Tradeify dashboard session status
- Last sync timestamp
- Last sync source
- Stale data state
- Reconciliation status
- Manual sync button
- Re-authenticate Tradeify dashboard button
- Live trading lock toggle display only unless already implemented securely

#### Risk Command

- Current drawdown headroom
- Daily PnL
- Open trade risk
- Risk allowed today
- Trade gate decision
- Reason for block/reduction

#### Performance / Payout

- Evaluation progress to `$9,000`
- Evaluation consistency status
- Funded winning days out of 5
- Current funded profit
- Distance to conservative payout zone `+$4,500`
- Distance to max payout zone `+$10,000`
- Estimated gross payout
- Estimated trader net payout
- Risk warning if payout would leave account undercapitalized

#### Reports

- Daily sync report
- Payout-readiness report
- Reconciliation warnings
- Risk gate history

### 7. Testing

Add tests with mocks. No live credentials required.

Required tests:

- Tradovate auth failure blocks sync.
- Tradovate balance parsing works.
- Dashboard selector fallback parsing works using static HTML fixtures.
- Reconciliation passes with < `$25` difference.
- Reconciliation warns/blocks with > `$25` difference.
- Stale broker data blocks new trades.
- Stale dashboard data blocks new trades when dashboard is required.
- Evaluation consistency calculation remains correct.
- Funded payout calculation remains correct.
- Live orders remain disabled by default.

Run:

```bash
pytest
ruff check .
mypy .
```

If the project does not currently use ruff/mypy, add only if consistent with current repo conventions.

## Subagent Assignments

Run these as parallel workstreams:

### Subagent A — Tradovate API Engineer

Build the Tradovate API connector using official docs. Focus on auth, account metrics, positions, fills, and market data. Do not implement live order placement unless explicitly behind risk gate and disabled by default.

### Subagent B — Tradeify / TFD Dashboard Engineer

Build Playwright login bootstrap and read-only dashboard metric extraction. Use resilient selectors and protected storage state. Do not bypass MFA/security. Do not click payout actions.

### Subagent C — Risk + Payout Engine Engineer

Connect live account snapshots into the existing risk gate, payout engine, and evaluation consistency engine. Ensure stale data and reconciliation failures produce `BLOCK` decisions.

### Subagent D — Backend/API Engineer

Add FastAPI endpoints, persistence, sync events, health checks, and caching. Ensure private data is redacted.

### Subagent E — UI Engineer

Wire connector status and payout metrics into existing MarinerX modules. Preserve the current dark institutional UI style.

### Subagent F — QA/Red-Team Engineer

Try to break the system. Test stale data, wrong account selection, failed dashboard login, balance mismatch, bad selectors, expired session, and accidental live order enablement.

## Definition of Done

The build is complete only when:

1. Existing MarinerX functionality still works.
2. Tradeify 150K rules endpoint works.
3. Tradovate connector can be configured but does not require credentials in tests.
4. Dashboard connector has manual login bootstrap.
5. Sync endpoints return normalized snapshots.
6. Risk gate consumes live/cached account snapshots.
7. UI shows connector status and payout progress.
8. No secrets are committed.
9. Unit tests pass.
10. Live orders are disabled by default.
11. README and deployment docs are updated.

## Final Output Required From Grok

Return:

- Summary of files changed
- Exact commands run
- Test results
- Remaining manual setup steps
- Required environment variables
- Any limitations or assumptions
- Whether live execution is still disabled
