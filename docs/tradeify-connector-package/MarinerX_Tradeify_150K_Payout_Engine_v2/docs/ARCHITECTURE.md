# Architecture

## Integration Pattern

The Tradeify 150K module should be installed as a MarinerX overlay, not as a separate bot.

```text
MarketPulse -> IndicatorEngine -> RegimeMonitor -> StrategyRunner
       -> ValidationEngine -> RiskCommand -> Trade-or-No-Trade
       -> ExecutionGateway -> TradeJournal -> PerformanceAnalyst -> ReportPublisher
```

The new module plugs into four critical points:

1. **ValidationEngine**
   - Computes evaluation consistency status.
   - Blocks pass attempts if the largest winning day exceeds 40% of total profit.

2. **RiskCommand**
   - Computes drawdown headroom.
   - Applies MarinerX daily loss and per-trade risk limits.
   - Triggers emergency flatten/block state.

3. **Trade-or-No-Trade**
   - Converts strategy signal into ALLOW, REDUCE_SIZE, BLOCK, or FLATTEN.
   - Rejects trades that exceed the current risk budget.

4. **PerformanceAnalyst / ReportPublisher**
   - Tracks 5 winning days.
   - Tracks payout availability.
   - Tracks max-payout profit target.

## State Machine

```text
EVALUATION
  -> PASS_ELIGIBLE when profit >= $9,000 and largest day <= 40% total profit
  -> FAILED when EOD balance breaches max drawdown

FUNDED_FLEX
  -> PAYOUT_ELIGIBLE when 5 winning days >= $250/day
  -> MAX_PAYOUT_ZONE when total profit >= $10,000
  -> NO_TRADE_STATE when MarinerX loss limits hit
  -> FLATTEN_STATE when drawdown headroom <= $1,500
```

## API Endpoints

```text
GET  /api/tradeify/150k/rules
POST /api/tradeify/150k/eval/status
POST /api/tradeify/150k/payout/status
POST /api/tradeify/150k/risk/gate
```

## UI Placement

| MarinerX Page | Add |
|---|---|
| Risk Command | Drawdown headroom, risk budget, daily lockout, kill switch |
| Trade-or-No-Trade | Gate result: allow/reduce/block/flatten |
| Execution & Orders | Approved contracts only, no bypass |
| Trade Journal | Winning day counter, cycle notes, rule flags |
| Performance | Payout eligible, gross payout, trader net payout |
| Reports | Daily PDF/markdown payout status report |
| Settings | Rule config, risk policy, execution mode |
