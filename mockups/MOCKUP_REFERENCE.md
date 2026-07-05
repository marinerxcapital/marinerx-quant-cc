# MOCKUP_REFERENCE.md
# MarinerX Labs Research System — Approved UI Reference

This document describes the final approved visual system and the 13 full-resolution PNG mockups in this package. The PNGs are the source of truth. This document exists to make implementation faster and remove ambiguity for the SuperGrok build agent.

## 1. Package Source of Truth

Use these files:

- `mockups/01_command_center_home.png`
- `mockups/02_market_pulse.png`
- `mockups/03_indicators_regime.png`
- `mockups/04_strategy_registry.png`
- `mockups/05_validation_verdicts.png`
- `mockups/06_research_lab.png`
- `mockups/07_risk_command.png`
- `mockups/08_trade_or_no_trade.png`
- `mockups/09_execution_orders.png`
- `mockups/10_trade_journal.png`
- `mockups/11_performance_analytics.png`
- `mockups/12_reports.png`
- `mockups/13_settings_system_control.png`
- `design_elements/marinerx_labs_logo.jpeg`
- `design_elements/marinerx_labs_x_icon.png`

The logo and X icon must be used as provided. Do not redraw, recolor, reshape, or replace them.

## 2. Global Visual System

### Core layout

- Desktop widescreen dashboard, 16:9 composition.
- Light institutional financial dashboard style.
- Fixed left sidebar.
- Fixed top status/header bar.
- Dense SaaS dashboard content area with white analytical cards.
- No landing-page styling.
- No mobile layout.
- No dark mode.
- No cyberpunk, 3D, decorative wallpaper, or abstract concept styling.

### Colors

Use the following as the implementation token baseline:

```css
:root {
  --mx-bg: #F7F8FA;
  --mx-sidebar: #EEF0F3;
  --mx-surface: #FFFFFF;
  --mx-border: #E2E5EA;
  --mx-primary: #12141A;
  --mx-secondary: #5B6270;
  --mx-muted: #9CA3AF;
  --mx-blue: #1D4ED8;
  --mx-blue-soft: #EFF6FF;
  --mx-green-text: #15803D;
  --mx-green-bg: #DCFCE7;
  --mx-amber-text: #B45309;
  --mx-amber-bg: #FEF3C7;
  --mx-red-text: #B91C1C;
  --mx-red-bg: #FEE2E2;
  --mx-neutral-text: #374151;
  --mx-neutral-bg: #E5E7EB;
}
```

### Typography

- Use a clean modern sans-serif throughout, such as Inter, system-ui, or an equivalent.
- Use medium/bold weights for page titles, card titles, table headers, metric values, and active states.
- Use smaller secondary text for subtitles, helper copy, notes, timestamps, and descriptions.
- Use tabular numerals or monospace treatment for:
  - P&L
  - timestamps
  - prices
  - percentages
  - strategy IDs
  - run IDs
  - hashes
  - instrument metrics

### Cards and panels

- Cards are white with a subtle 1px `#E2E5EA` border.
- Standard radius is 8px.
- Minimal shadow or no shadow.
- Dense but readable spacing.
- Chart panels, tables, and detail drawers all use the same border and radius language.

### Status badges

Use compact rounded pill badges with semantic color:

- Green: approved, running, healthy, connected, pass, filled, clear, signal, GO.
- Amber: caution, yellow, partial, stand-aside, review.
- Red: failed, red verdict, no-go, disabled, archived, lockout, error.
- Neutral: draft, flat, not configured, no signal, cancelled.

### Persistent chrome

Every page must include:

- Top-left brand cell with `MarinerX Labs` logo and small subtitle `Research System`.
- Standalone black X icon in the sidebar brand area.
- Left sidebar with active page highlighted by a solid blue rounded pill.
- Top header with:
  - `ALL SYSTEMS NOMINAL`
  - `Day P&L +$1,240`
  - `Week P&L +$3,870`
  - `Drawdown Headroom $4,620`
  - UTC clock
  - red outlined `KILL SWITCH` button

## 3. Page-by-Page Reference

### 01 — Command Center Home

Purpose: system overview and agent command grid.

Key layout:
- Page title: `Command Center Home`.
- Section 1: `Agent Command Grid`, 15 agent cards in a 5-column by 3-row grid.
- Agents: Overseer, DataOps, AccountSync, MarketPulse, IndicatorEngine, RegimeMonitor, StrategyRunner, ValidationEngine, ResearchLab, RiskCommand, DecisionEngine, ExecutionGateway, TradeJournal, PerformanceAnalyst, ReportPublisher.
- Each agent card includes icon, status dot, status badge, task line, and key metric.
- Section 2: instrument decision cards for NQ, ES, CL, GC.
- NQ shows GO. ES and CL show NO-GO. GC shows STAND-ASIDE.

### 02 — Market Pulse

Purpose: real-time breadth and internals telemetry.

Key layout:
- Page title: `Market Pulse`.
- Tabs: Internals active, Microstructure inactive, Heatmaps inactive.
- Five sparkline cards: `$TICK`, `$TRIN`, `$ADD`, `$VOLD`, `$VIX`.
- Composite Breadth Regime card with large `RISK-ON` badge, confidence, rationale, contribution table, total impact, and regime score.
- Bottom `Market Pulse Detail` cards:
  - Breadth Pressure Meter
  - Advance / Decline
  - VIX Term Structure
  - Session Breadth Timeline

### 03 — Indicators & Regime

Purpose: charting and regime classification.

Key layout:
- Page title: `Indicators & Regime`.
- Two-column layout.
- Left card: `Indicator Library` with compact rows and toggles:
  SMA(20), EMA(50), RSI(14), MACD(12,26,9), Bollinger Bands(20,2), VWAP + Bands, ADX(14), Donchian Channel, Opening Range, Session VWAP.
- Right card: large NQ candlestick chart with tabs NQ/ES/CL/GC.
- Chart includes moving averages, Bollinger envelope, dashed VWAP line, price axis, time axis, and legend.
- Bottom strip: `Regime Snapshot` with NQ, ES, CL, GC regime cards.

### 04 — Strategy Registry

Purpose: strategy lifecycle tracking.

Key layout:
- Page title: `Strategy Registry`.
- Large dense strategy table.
- Top utility row with search and filters.
- Columns: Strategy ID, Name, Version, Instrument(s), Status, Last Updated, Owner/Agent, Notes.
- Right-side detail drawer titled `Strategy Detail`.
- Selected row: `CL EIA Inventory Drift`.
- Drawer includes strategy description, parameter table, lifecycle timeline, memo, and buttons: Open Memo, Run Validation, Archive.

### 05 — Validation & Verdicts

Purpose: statistical strategy validation.

Key layout:
- Page title: `Validation & Verdicts`.
- Narrow left panel: `Registered Hypotheses`.
- Selected hypothesis: `CL EIA Drift`, verdict RED, trial count 42.
- Wide right panel: selected result for `CL EIA Inventory-Day Post-Report Drift`.
- Large red verdict banner: `VERDICT: RED — ARCHIVED`.
- Stat cards:
  - OOS Net Profit Factor 0.97
  - Deflated Sharpe Ratio 0.21
  - Probabilistic Sharpe Ratio 48.6%
  - Trial Count 42
  - OOS Trade Count 186
- Walk-forward table with five folds, only two passing.
- Bottom Monte Carlo drawdown distribution histogram with risk limit and observed DD markers.

### 06 — Research Lab

Purpose: quant and machine-learning experiment tracking.

Key layout:
- Page title: `Research Lab`.
- Top section: four Forecast Lab model cards:
  - LightGBM — NQ 15m Direction — SIGNAL
  - XGBoost — ES 30m Continuation — NO_SIGNAL
  - Logistic Regression — CL Event Filter — NO_SIGNAL
  - CatBoost — GC Vol Regime — NO_SIGNAL
- Each model card includes Brier score, model hit rate, baseline bar, and last trained timestamp.
- Bottom: `Experiment Tracker` table with run IDs, config hashes, dataset windows, model, key metric, result badge, and timestamp.

### 07 — Risk Command

Purpose: sizing, VaR, expected shortfall, drawdown control, and portfolio exposure.

Key layout:
- Page title: `Risk Command`.
- Top-left `Position Sizing` card with NQ, recommended size 2 contracts, Fractional Kelly selected, risk per trade $350, stop distance 17.5 pts, max size cap 3 contracts, and reason text.
- Two gauge cards:
  - Portfolio VaR $1,180 / $2,500 limit
  - Expected Shortfall CVaR $1,740 / $3,500 limit
- Dominant `PropGuardian` card with green OK badge, caution/lockout legend, drawdown headroom bar, daily loss progress bar, and rule summary.
- Bottom: `Portfolio Exposure` horizontal bar chart for NQ, ES, CL, GC.

### 08 — Trade-or-No-Trade Decision Center

Purpose: signature decision screen.

Key layout:
- Page title: `Trade-or-No-Trade Decision Center`.
- Four large instrument decision cards:
  - NQ = GO, selected with blue border and light blue fill
  - ES = NO-GO
  - CL = NO-GO
  - GC = STAND-ASIDE
- Detail panel: `NQ Decision Detail`.
- Left: Veto Checklist with five green OK rows.
- Right: Factor Breakdown horizontal bar chart.
- Total confidence: 68%.
- Bottom Reasoning panel with recommended size, max risk, and invalidation.

### 09 — Execution & Orders

Purpose: paper execution monitoring and live-execution safety.

Key layout:
- Page title: `Execution & Orders`.
- Full-width red safety banner: `LIVE TRADING: DISABLED`.
- Guardrail row with green badges:
  Strategy GREEN, PropGuardian Clear, Size Within Caps, Session Open, No Event Blackout, Data Feed Healthy.
- Middle-left: Open Positions (Paper) table.
- Middle-right: Recent Fills (Paper) table.
- Bottom: disabled New Order / Paper Mode ticket.

### 10 — Trade Journal

Purpose: structured trade logging.

Key layout:
- Page title: `Trade Journal`.
- Top filter bar: Instrument, Setup Tag, Strategy, Date Range, Result, Search.
- Buttons: Export CSV, Attach Screenshot, New Note.
- Dense trade table with 10–12 rows.
- Columns: Date, Time, Instrument, Side, Setup Tag, Strategy ID, Entry, Exit, Net P&L, Regime at Entry, Decision, Expand.
- One NQ row is expanded inline with:
  - Decision Engine Reason
  - Trader Notes
  - screenshot thumbnail placeholder labeled `screenshot attached`.

### 11 — Performance Analytics

Purpose: equity, drawdown, risk-adjusted return, expectancy, and decision attribution.

Key layout:
- Page title: `Performance Analytics`.
- Top-left card: `Equity Curve & Drawdown`.
- Metrics: Net P&L +$8,420, Max DD -$2,180, Win Rate 58%, Profit Factor 1.42.
- Top-right mini charts: Rolling Sharpe Ratio and Rolling Sortino Ratio.
- Middle: Expectancy by Setup, Expectancy by Regime, Expectancy by Instrument.
- Bottom: Decision Attribution card plus performance-by-decision table.
- Summary note explains that the decision engine added value by filtering low-quality CL and ES setups during high-vol regimes.

### 12 — Reports

Purpose: generated institutional research document archive.

Key layout:
- Page title: `Reports`.
- Two-column layout.
- Left panel: `Generated Reports` list.
- Selected report: `Verdict Memo — CL EIA Inventory Drift`.
- Right panel: report preview with buttons Download, Export, Open Full Report.
- Preview shows mini PDF page with:
  - branded header
  - report title
  - red verdict badge
  - summary paragraph
  - embedded chart
  - key metrics table
  - footer timestamp
  - subtle X watermark.

### 13 — Settings & System Control

Purpose: system configuration and danger-zone controls.

Key layout:
- Page title: `Settings & System Control`.
- Top-left: `Data & Feed Status` table.
- Top-right: read-only Configuration list.
- Middle: large red-bordered `System Control (Danger Zone)` card.
- Includes GLOBAL KILL SWITCH, confirm checkbox, Live Execution OFF toggle, disabled text, and confirmation token input.
- Bottom: Audit Log table.

## 4. Implementation Acceptance Standard

The implementation should visually match each PNG at the page level before shipping. Required evidence:

1. Local screenshot of each rebuilt page.
2. Side-by-side comparison with the matching mockup.
3. Live Railway screenshot after deploy.
4. Final side-by-side comparison from live URL.

No page should be marked PASS without screenshot evidence.
