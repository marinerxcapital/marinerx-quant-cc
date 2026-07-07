# Security and Credential Policy

## Non-Negotiable Rule

Do not place Tradeify, TFD dashboard, Tradovate, email, OAuth, session cookie, or API credentials inside any prompt, commit, log, screenshot, test fixture, or frontend payload.

## Accepted Credential Methods

| Method | Status | Notes |
|---|---|---|
| Environment variables | Approved | Use local `.env` and deployment secrets. |
| Secret manager | Approved | Preferred for deployed Render/Fly/Railway/VPS setups. |
| Playwright storage state | Approved with caution | Must be protected and never committed. |
| Plaintext config files | Blocked | Do not use. |
| Prompt-inserted credentials | Blocked | Never put credentials into Grok/Claude/Codex prompts. |

## Required Environment Variables

```env
# Master switches
MARINERX_TRADEIFY_DATA_ENABLED=true
MARINERX_TRADEIFY_DASHBOARD_ENABLED=false
MARINERX_TRADOVATE_ENABLED=true
MARINERX_ALLOW_LIVE_ORDERS=false

# Tradovate
MARINERX_TRADOVATE_ENVIRONMENT=demo
TRADOVATE_BASE_URL=https://demo.tradovateapi.com/v1
TRADOVATE_MD_WS_URL=wss://md-demo.tradovateapi.com/v1/websocket
TRADOVATE_APP_ID=
TRADOVATE_APP_VERSION=
TRADOVATE_DEVICE_ID=
TRADOVATE_CID=
TRADOVATE_SECRET=
TRADOVATE_USERNAME=
TRADOVATE_PASSWORD=

# Tradeify / TFD dashboard
TRADEIFY_DASHBOARD_URL=https://app.tradeify.co
TRADEIFY_DASHBOARD_STORAGE_STATE=/secure/marinerx/tradeify_storage_state.json
MARINERX_DEBUG_DASHBOARD_SNAPSHOTS=false
```

## Browser Automation Policy

The dashboard connector should support two login modes:

### Mode A: Manual Session Bootstrap

1. Run a local command: `python -m marinerx_tradeify.tools.tradeify_login_bootstrap`.
2. Browser opens in visible mode.
3. User manually logs into Tradeify/TFD dashboard and completes MFA if required.
4. Tool saves encrypted/protected `storage_state` locally.
5. Runtime scraper uses the saved session read-only.

### Mode B: Environment Secret Login

Only allowed if manual session bootstrap is not practical.

Requirements:

- Credentials are loaded from deployment secrets only.
- Password is never printed.
- MFA must be handled manually or with an approved user-controlled mechanism.
- The automation must not attempt to bypass CAPTCHA, MFA, device approval, or security prompts.

## Logging Redaction

Redact:

- username
- password
- email
- OAuth token
- refresh token
- session cookies
- account IDs
- dashboard HTML
- screenshots with private data unless explicit debug mode is enabled

Allowed in logs:

- hashed account ID
- sync success/failure
- latency
- stale data flag
- source name
- non-sensitive metric names

## Deployment Policy

For Render deployment:

- Store secrets in Render environment variables.
- Do not commit `.env`.
- Do not commit Playwright storage state.
- Mount persistent disk only if encrypted/protected.
- Disable dashboard automation on public preview deployments unless access is locked down.

## Failure Mode

If authentication fails, data is stale, or scraping selectors break:

```text
Risk gate decision = BLOCK
Allowed action = flatten-only if an open position exists
User-facing message = Data unavailable; trading disabled until connector is healthy
```
