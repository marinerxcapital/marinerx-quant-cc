# Tradovate Connector Build Spec

## Objective

Implement a Python connector for Tradovate that can provide MarinerX with real-time or near-real-time account and market telemetry for the Tradeify 150K account.

## Preferred Integration

Use the official Tradovate API where available.

Required capabilities:

- Authenticate to demo/simulation environment.
- Fetch account list.
- Identify the active Tradeify 150K account.
- Fetch balance/equity/cash metrics.
- Fetch positions.
- Fetch fills/trades.
- Subscribe to market data for active symbols.
- Optional later: stage orders only after risk gate approval.

## Environment

Tradeify Tradovate accounts should use demo/simulation connection unless the user explicitly configures another environment.

```env
MARINERX_TRADOVATE_ENVIRONMENT=demo
TRADOVATE_BASE_URL=https://demo.tradovateapi.com/v1
TRADOVATE_MD_WS_URL=wss://md-demo.tradovateapi.com/v1/websocket
```

## Market Data Symbols

Initial symbols:

- NQ / MNQ
- ES / MES
- CL / MCL
- GC / MGC

## Required Connector Methods

```python
async def authenticate() -> None: ...
async def fetch_accounts() -> list[dict]: ...
async def fetch_positions(account_id) -> list[PositionSnapshot]: ...
async def fetch_cash_balance(account_id) -> dict: ...
async def fetch_fills(account_id, start, end) -> list[dict]: ...
async def fetch_orders(account_id) -> list[dict]: ...
async def fetch_market_snapshot(symbol: str) -> dict: ...
async def subscribe_market_data(symbols: list[str]) -> AsyncIterator[MarketSnapshot]: ...
```

## Order Placement Policy

Order placement must be disabled until a later phase.

Even when enabled, order placement must require:

1. Fresh broker data.
2. Fresh Tradeify dashboard data or accepted fallback mode.
3. Passing risk gate.
4. No daily stop breach.
5. No stale-data flag.
6. No manual kill-switch flag.
7. `MARINERX_ALLOW_LIVE_ORDERS=true`.

## Testing

Add mocked tests for:

- Auth success/failure.
- Account selection.
- Position parsing.
- Balance parsing.
- Market snapshot parsing.
- Stale data block.
- Risk gate integration.

No tests should require live credentials.
