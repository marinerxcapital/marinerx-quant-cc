Take over the current MarinerX Labs project and implement the Tradeify 150K Select Flex data connector package.

Main goal: MarinerX must pull Tradovate account/market data and Tradeify/TFD dashboard account metrics, normalize them into the existing risk/payout engine, and display payout progress/risk status inside the MarinerX UI.

Use the attached package as the build spec. Start with `prompts/GROK_MASTER_DATA_CONNECTOR_PROMPT.md`, then run the subagents defined in `prompts/SUBAGENTS_TRADEIFY_DATA_TEAM.md`.

Critical rules:
- Do not ask me to paste credentials into prompts.
- Use environment variables, deployment secrets, or Playwright manual login storage state.
- Do not bypass MFA or platform security.
- Live orders must stay disabled by default.
- Data failures must block new trades.
- Build into the existing MarinerX repo, not a separate prototype.

After implementation, report changed files, commands run, tests, required env vars, and any manual setup steps.
