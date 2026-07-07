# UI Specification

## Risk Command Card

Title: TRADEIFY 150K RISK COMMAND

Metrics:

- Account phase: Evaluation / Funded Flex
- Balance
- EOD drawdown floor
- Drawdown headroom
- Day P&L
- Open risk
- Remaining daily risk
- Risk state: Nominal / Caution / Lockout / Flatten

Actions:

- Manual kill switch
- Disable new orders
- Flatten simulated positions
- Export daily risk report

## Trade-or-No-Trade Card

Inputs:

- Symbol
- Direction
- Setup name
- Entry
- Stop
- Target
- Contract type
- Requested contracts

Outputs:

- Decision: ALLOW / REDUCE_SIZE / BLOCK / FLATTEN
- Approved contracts
- Projected risk
- Reason
- Drawdown headroom after full loss

## Payout Tracker Card

Metrics:

- Winning days: X / 5
- Current funded profit
- Gross payout available
- Trader net after 90/10
- Additional profit to max payout
- Recommended request
- Post-payout balance

States:

- NOT ELIGIBLE
- ELIGIBLE BUT TOO THIN
- PARTIAL PAYOUT ZONE
- MAX PAYOUT ZONE

## Evaluation Tracker Card

Metrics:

- Current evaluation profit
- Target: $9,000
- Largest winning day
- Max allowed largest day at current total
- Required total profit for consistency
- Remaining profit to target
- Remaining profit to consistency
- Pass eligible: yes/no
