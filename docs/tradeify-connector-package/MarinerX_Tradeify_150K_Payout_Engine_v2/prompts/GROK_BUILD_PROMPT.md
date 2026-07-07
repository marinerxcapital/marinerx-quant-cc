# Grok Build Prompt — MarinerX Tradeify 150K Payout Engine

You are taking over the existing MarinerX Labs project.

Goal: integrate the provided `marinerx_tradeify` Python package into the current FastAPI-based MarinerX Labs backend and UI so the system can manage a Tradeify 150K Select Flex account with risk-first payout optimization.

Do not build a separate bot. Add this as a native MarinerX overlay.

## Current MarinerX Pages to Wire

- Risk Command
- Trade-or-No-Trade
- Execution & Orders
- Trade Journal
- Performance
- Reports
- Settings

## Required Backend Work

1. Copy `src/marinerx_tradeify/` into the backend package.
2. Register the FastAPI router:

```python
from marinerx_tradeify.router import router as tradeify_150k_router
app.include_router(tradeify_150k_router)
```

3. Add config loading from `config/tradeify_150k_select_flex.yaml`.
4. Ensure every order staging path calls `/api/tradeify/150k/risk/gate` or the underlying `gate_trade()` function before execution.
5. Keep live execution inert unless `MARINERX_ALLOW_LIVE_ORDERS=true` and the user manually enables it in Settings.
6. Add structured logs for all gate decisions.
7. Add tests covering:
   - eval consistency pass/fail
   - funded payout eligibility
   - max payout calculation
   - risk gate allow/reduce/block/flatten
   - unknown symbol block
   - daily loss lockout

## Required UI Work

Add the following widgets:

### Risk Command

- Account phase
- Balance
- EOD drawdown floor
- Drawdown headroom
- Day P&L
- Remaining daily risk
- Risk state
- Kill switch

### Trade-or-No-Trade

- Signal input
- Risk gate result
- Approved contracts
- Projected risk
- Reason

### Performance

- Winning days X/5
- Current funded profit
- Gross payout available
- Trader net payout
- Additional profit to max payout
- Recommended payout request

### Validation & Verdicts

- Evaluation profit target progress
- Largest day
- Required total profit for consistency
- Pass eligible yes/no

### Settings

- Tradeify account mode: EVALUATION / FUNDED_FLEX
- Execution mode: PAPER_FIRST / SIM_ONLY / LIVE_MANUAL_APPROVAL
- Edit MarinerX risk policy
- Show official-rule verification timestamp

## Non-Negotiable Safety Requirements

- Never bypass Risk Command.
- Never place live orders by default.
- Unknown symbol = blocked.
- Drawdown headroom <= $1,500 = flatten/block.
- Day P&L <= -$750 = block new trades.
- Day P&L <= -$900 = hard lockout.
- Max risk per trade default = $250.
- If rule config is missing, block trading.

## Completion Criteria

- App builds and starts.
- `/api/tradeify/150k/rules` returns valid JSON.
- UI shows Tradeify 150K overlay.
- Tests pass.
- README updated.
- AGENTS.md updated with the new Tradeify overlay rules.
- No fake/mocked live execution.
