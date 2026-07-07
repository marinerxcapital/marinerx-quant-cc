# Codex Implementation Prompt — Tradeify 150K Select Flex Overlay

Implement a Python rules/risk/payout module inside MarinerX Labs.

Use the files in this package as the source of truth. Preserve the risk-first architecture.

## Deliverables

1. Backend integration
2. FastAPI router registration
3. UI widgets on existing MarinerX pages
4. Tests
5. Documentation updates
6. Safe execution flags

## Important

The system must not claim guaranteed payouts or predictive certainty. It must enforce rules, compute risk, compute payout eligibility, and block/reduce trades that violate MarinerX risk policy.

## Core Formulas

Evaluation consistency:

```text
largest_winning_day <= 0.40 * total_eval_profit
required_total = largest_winning_day / 0.40
```

Funded Flex payout:

```text
gross_available = min((balance - 150000) * 0.50, 5000)
trader_net = gross_available * 0.90
max_payout_profit_target = 10000
```

Risk gate:

```text
projected_risk <= min(
  max_risk_per_trade,
  remaining_daily_risk,
  drawdown_headroom - emergency_flatten_headroom
)
```

## Add Tests

Required cases:

- Oversized $5,000 eval day on $9,000 total blocks pass.
- Clean 3 x $3,000 eval pass is eligible.
- $160,000 funded balance with 5 winning days produces $5,000 gross / $4,500 net.
- $151,250 funded balance with 5 winning days is rule-eligible but not safe by MarinerX policy.
- MNQ signal risk is reduced or blocked if size exceeds $250.

## Do Not

- Do not hardcode live credentials.
- Do not add broker execution unless there is already a validated execution gateway.
- Do not remove existing MarinerX modules.
- Do not make payout guarantees.
