# MarinerX Tradeify 150K Payout + Data Engine v2

This package extends the original MarinerX Tradeify 150K Payout Engine with a secure data-ingestion plan for:

1. Tradovate account, position, fill, order, and market data.
2. Tradeify / TFD dashboard account metrics via authenticated user-owned dashboard session.
3. Normalized MarinerX account snapshots for risk gating, payout tracking, reporting, and UI status.

Objective: help MarinerX enforce risk-first decisioning while pursuing Tradeify 150K Select Flex payout eligibility and max-payout math.

This is not an auto-trading bot and does not guarantee payouts. It is a rules engine, payout engine, risk gate, data connector specification, and FastAPI router scaffold designed to plug into the existing MarinerX Labs modules:

- Risk Command
- Trade-or-No-Trade
- Execution & Orders
- Trade Journal
- Performance
- Reports
- Settings/System Control

## New In v2

| Addition | Purpose |
|---|---|
| `docs/DATA_CONNECTOR_SPEC.md` | Full Tradovate + Tradeify/TFD data architecture |
| `docs/TRADOVATE_CONNECTOR_SPEC.md` | Official Tradovate API connector requirements |
| `docs/TRADEIFY_TFD_DASHBOARD_CONNECTOR_SPEC.md` | Playwright dashboard connector requirements |
| `docs/SECURITY_AND_CREDENTIALS.md` | Credential, session, and deployment security policy |
| `prompts/GROK_MASTER_DATA_CONNECTOR_PROMPT.md` | Main Grok Heavy build prompt |
| `prompts/SUBAGENTS_TRADEIFY_DATA_TEAM.md` | Parallel subagent assignments |
| `prompts/SHORT_MESSAGE_TO_GROK_TERMINAL.md` | Short terminal handoff message |
| `src/marinerx_tradeify/connectors/` | Safe connector scaffolds and normalizer |
| New `/api/tradeify/150k/data/*` stubs | Endpoint contract for the target repo |

## Core Rule Assumptions

Tradeify 150K Select Evaluation:

- Starting account size: `$150,000`
- Evaluation target: `$9,000`
- Max drawdown: `$4,500 EOD`
- Daily loss limit: none
- Evaluation consistency: `40%`
- Max contracts: `12 mini / 120 micro`

Tradeify Select Flex funded payout:

- `5` winning days required
- 150K winning day threshold: `$250`
- Payout: up to `50%` of total profits
- Payout cap: `$5,000` gross
- Trader receives `90%` of approved payout
- Max gross payout requires at least `$10,000` total funded profit

## MarinerX Internal Policy Defaults

These are intentionally stricter than Tradeify's limits:

- Risk per trade: `$250`
- Daily loss soft stop: `$750`
- Hard daily stop: `$900`
- Emergency flatten if drawdown headroom <= `$1,500`
- Do not request first payout below `+$4,500` profit cushion
- Max payout objective: `+$10,000` funded profit
- New trades blocked if data is stale, missing, or unreconciled

## Secure Data-Connector Design

Data should flow through MarinerX like this:

```text
Tradovate API + Tradeify/TFD Dashboard
    ↓
Connector Normalizer + Reconciliation
    ↓
AccountSnapshot
    ↓
Risk Command
    ↓
Tradeify Risk Gate
    ↓
Trade-or-No-Trade
    ↓
Execution & Orders
    ↓
Trade Journal + Performance + Reports
```

## Required Environment Variables

See `.env.example`.

Do not put credentials in prompts, commits, screenshots, logs, or frontend responses.

## Install Into Existing FastAPI App

1. Copy `src/marinerx_tradeify/` into the MarinerX Labs backend source tree.
2. Add the router to your FastAPI app:

```python
from marinerx_tradeify.router import router as tradeify_150k_router
app.include_router(tradeify_150k_router)
```

3. Use `prompts/GROK_MASTER_DATA_CONNECTOR_PROMPT.md` for the full implementation pass.
4. Use `prompts/SUBAGENTS_TRADEIFY_DATA_TEAM.md` to parallelize the build.
5. Keep live execution inert until the full risk/connector test suite passes.

## Data Endpoints

Existing endpoints:

```text
GET  /api/tradeify/150k/rules
POST /api/tradeify/150k/eval/status
POST /api/tradeify/150k/payout/status
POST /api/tradeify/150k/risk/gate
```

New v2 endpoint contracts:

```text
GET  /api/tradeify/150k/data/status
POST /api/tradeify/150k/data/sync
GET  /api/tradeify/150k/data/latest
GET  /api/tradeify/150k/data/health
POST /api/tradeify/150k/data/validate-session
POST /api/tradeify/150k/data/reconcile
```

The new data endpoints are scaffolded safe-default placeholders. Grok/Codex must complete them inside the live MarinerX repo.

## Suggested Run Mode

Keep execution inert by default:

```env
MARINERX_TRADEIFY_MODE=PAPER_FIRST
MARINERX_ALLOW_LIVE_ORDERS=false
MARINERX_TRADOVATE_ENVIRONMENT=demo
MARINERX_TRADEIFY_DASHBOARD_ENABLED=false
```

Enable dashboard connector only after manual session bootstrap is implemented and tested.

Enable live order capability only after:

- Unit tests pass
- Replay tests pass
- Sim trading confirms slippage/commissions
- Manual kill-switch works
- Tradovate sync works
- Tradeify/TFD dashboard sync works
- Reconciliation works
- Stale-data blocking works
- Tradeify rules are verified again from official docs
