# MarinerX Risk Policy for Tradeify 150K Select Flex

## Objective

Max payout is a survival problem first and a profit problem second.

The funded max payout cap is reached when total profit is at least $10,000 because the Flex payout is 50% of total profits, capped at $5,000 gross. The trader net at 90/10 is $4,500.

## Evaluation Risk Plan

| Metric | Value |
|---|---:|
| Account size | $150,000 |
| Profit target | $9,000 |
| Max drawdown EOD | $4,500 |
| Firm daily loss limit | None |
| MarinerX daily loss limit | $750 |
| MarinerX hard daily stop | $900 |
| Max risk per trade | $250 |
| Practical pass plan | 3 days minimum |

## Evaluation Consistency Math

Single largest day must be no more than 40% of total profit.

Formula:

```text
required_total_profit = largest_winning_day / 0.40
remaining_consistency_profit = max(0, required_total_profit - current_total_profit)
```

Example:

```text
Current profit = $9,000
Largest day = $5,000
Required total = $5,000 / 0.40 = $12,500
Extra profit needed = $3,500
```

## Funded Max Payout Math

```text
gross_payout = min(total_profit * 0.50, $5,000)
trader_net = gross_payout * 0.90
profit_needed_for_max_gross = $5,000 / 0.50 = $10,000
```

## First Payout Policy

Do not request at bare-minimum eligibility.

| Funded Profit | Gross Available | Trader Net | Internal Decision |
|---:|---:|---:|---|
| $1,250 | $625 | $562.50 | Do not request; too thin |
| $4,500 | $2,250 | $2,025 | Conservative first request zone |
| $5,000 | $2,500 | $2,250 | Better cushion |
| $10,000 | $5,000 | $4,500 | Max payout zone |

## Kill Rules

| Condition | Action |
|---|---|
| Realized day P&L <= -$750 | Block new trades |
| Realized day P&L <= -$900 | Hard lockout |
| Drawdown headroom <= $1,500 | Flatten/block |
| Trade risk > $250 | Reduce size or block |
| Unknown symbol/risk spec | Block |
| Live execution flag false | Do not route orders |
