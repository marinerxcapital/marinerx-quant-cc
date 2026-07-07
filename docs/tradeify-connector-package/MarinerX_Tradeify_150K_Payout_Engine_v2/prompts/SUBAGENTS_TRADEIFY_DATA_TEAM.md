# Subagent Team Instructions — Tradeify/Tradovate Data System

Use this file to split work across Grok subagents.

## Global Rules For Every Subagent

- Do not commit secrets.
- Do not place credentials in prompts.
- Do not bypass MFA, CAPTCHA, device approval, or platform security.
- Do not enable live orders by default.
- Do not add mock production data.
- Every connector failure must fail safe into `BLOCK` for new trades.
- Maintain current MarinerX style and architecture.

---

## Subagent A — Tradovate API Engineer

### Mission

Build the official Tradovate connector.

### Files

- `src/marinerx_tradeify/connectors/tradovate_connector.py`
- Any existing MarinerX broker connector folder if one already exists
- Tests under `tests/`

### Deliverables

- Auth client
- Account discovery
- Account balance parser
- Position parser
- Fill parser
- Market data snapshot/subscription client
- Mock tests
- Error redaction

### Acceptance Criteria

- No tests need live credentials.
- Demo environment is default.
- Missing API credentials produce a clean configuration error.
- Account IDs are hashed in logs/storage.

---

## Subagent B — Tradeify / TFD Dashboard Engineer

### Mission

Build read-only dashboard metrics ingestion.

### Files

- `src/marinerx_tradeify/connectors/tradeify_dashboard_connector.py`
- `src/marinerx_tradeify/tools/tradeify_login_bootstrap.py`
- Static HTML fixtures under `tests/fixtures/`

### Deliverables

- Playwright manual login bootstrap
- Protected storage state handling
- Dashboard account-card/table parsing
- Selector fallback strategy
- Session validation endpoint support
- Tests with static HTML fixtures

### Acceptance Criteria

- User completes login manually.
- MFA is respected.
- No payout buttons are clicked.
- No screenshots saved unless debug flag is true.
- Expired session returns a clear reconnect required state.

---

## Subagent C — Normalization + Reconciliation Engineer

### Mission

Merge Tradovate and Tradeify metrics into one authoritative MarinerX snapshot.

### Files

- `src/marinerx_tradeify/connectors/normalizer.py`
- `src/marinerx_tradeify/models.py`
- Risk engine integration points

### Deliverables

- Merge function
- Stale data checker
- Balance/PnL mismatch checker
- Phase conflict checker
- Confidence scoring
- Risk-gate fail-safe integration

### Acceptance Criteria

- Balance mismatch > `$25` warns/blocks.
- PnL mismatch > `$25` warns/blocks.
- Stale data blocks new trades.
- Missing drawdown floor blocks new trades unless explicit manual override exists.

---

## Subagent D — Backend API + Persistence Engineer

### Mission

Expose connector status and sync pipeline through FastAPI.

### Files

- `src/marinerx_tradeify/router.py`
- Existing MarinerX DB/migration files
- Existing API registration files

### Deliverables

- `/data/status`
- `/data/sync`
- `/data/latest`
- `/data/health`
- `/data/validate-session`
- `/data/reconcile`
- Snapshot persistence
- Sync event persistence
- Error redaction

### Acceptance Criteria

- Endpoints never expose credentials.
- Sync failures are stored as redacted events.
- Latest cached snapshot works even when live sync fails.
- Health endpoint is safe for UI polling.

---

## Subagent E — MarinerX UI Engineer

### Mission

Add Tradeify/Tradovate connector status and payout telemetry to the existing MarinerX UI.

### UI Targets

- Settings/System Control
- Risk Command
- Trade-or-No-Trade
- Performance
- Reports

### Deliverables

- Connector status cards
- Manual sync button
- Dashboard reconnect button
- Payout progress gauge/table
- Risk gate reason display
- Stale data warning state
- Reconciliation warning state

### Acceptance Criteria

- UI preserves current MarinerX dark institutional theme.
- No secrets appear in frontend.
- The user can see why a trade is blocked.
- The user can see exact profit needed to reach max payout.

---

## Subagent F — QA / Red-Team Engineer

### Mission

Break the system before the market does.

### Scenarios

- Tradovate API down
- Dashboard session expired
- Dashboard selectors broken
- Wrong account selected
- Balance mismatch > `$25`
- PnL mismatch > `$25`
- Data older than 180 seconds
- Open position but connector fails
- User accidentally toggles live mode
- Drawdown headroom <= `$1,500`
- Evaluation consistency violation
- Funded account payout request would leave insufficient cushion

### Acceptance Criteria

- All unsafe states produce `BLOCK` or flatten-only.
- No unsafe state allows new orders.
- Reports explain the failure clearly.
