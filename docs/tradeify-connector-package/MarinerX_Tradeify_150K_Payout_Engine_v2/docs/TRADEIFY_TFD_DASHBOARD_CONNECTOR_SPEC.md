# Tradeify / TFD Dashboard Connector Build Spec

## Objective

Build a read-only dashboard connector that logs into the user's Tradeify/TFD dashboard and extracts prop-firm metrics that may not be available directly from Tradovate.

## Important Constraint

This connector must not bypass MFA, CAPTCHA, device approval, anti-bot protections, or access controls. It should operate only on the user's own dashboard session.

## Preferred Login Flow

Use Playwright with local manual login bootstrap.

```text
python -m marinerx_tradeify.tools.tradeify_login_bootstrap
```

Flow:

1. Open browser in headed mode.
2. User logs in manually.
3. User completes MFA if required.
4. System saves `storage_state` to a protected path.
5. Production sync uses the saved session in headless mode.

## Required Dashboard Metrics

Extract these fields when visible:

| Metric | Required | Notes |
|---|---:|---|
| Account label | Yes | Must identify the correct 150K account. |
| Account phase/status | Yes | Evaluation, funded, inactive, failed, payout pending, etc. |
| Current balance | Yes | Used for payout/risk engine. |
| Daily realized PnL | Yes | Used for daily stop and winning day. |
| Total profit | Yes | Used for eval and payout progress. |
| Drawdown floor/headroom | Yes | Used for risk gate. |
| Winning days | Yes for funded | Used for 5-day payout path. |
| Payout eligibility | Yes for funded | Display only; MarinerX also calculates independently. |
| Next payout cap/status | Preferred | Used for Performance module. |
| Consistency percentage | Required during eval | Used to avoid passing with a rule violation. |
| Last payout status | Preferred | Reporting and reconciliation. |

## Selector Strategy

Use resilient extraction:

1. Prefer stable data attributes if the dashboard exposes them.
2. Otherwise use text-based locators around metric labels.
3. Avoid brittle nth-child selectors unless no other option exists.
4. Add screenshot-assisted debugging only behind `MARINERX_DEBUG_DASHBOARD_SNAPSHOTS=true`.
5. Redact screenshots by default.

## Sync Frequency

| State | Frequency |
|---|---:|
| Market hours with open position | 15 seconds |
| Market hours no open position | 30-60 seconds |
| Outside market hours | 5-15 minutes |
| Dashboard login invalid | Stop sync; alert user |

## Reconciliation

Compare dashboard data with Tradovate data:

- Balance difference > `$25` = warning.
- Realized PnL difference > `$25` = warning.
- Dashboard says inactive/failed = block trading.
- Dashboard drawdown unknown = block new trades unless manual override is enabled.

## UI Requirements

Add a Settings/System Control panel:

- Tradovate connection status
- Tradeify dashboard session status
- Last sync time
- Last sync source
- Balance reconciliation result
- Manual refresh button
- Re-authenticate dashboard button
- Live order lock state

Add a Performance panel:

- Current funded profit
- Winning days
- Max payout progress
- Amount needed for `$5,000` gross payout cap
- Safe payout amount if requested today
- Risk warning if payout would leave too little cushion

## Failure Policy

If dashboard sync breaks:

```text
New trades = BLOCK
Open trades = allow flatten-only
Reports = continue using cached data, marked stale
User alert = Dashboard data stale; reconnect Tradeify session
```
