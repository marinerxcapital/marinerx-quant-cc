# PHASE 15 — UI FIDELITY MATCH + GITHUB-TRIGGERED RAILWAY REDEPLOY

**FINAL PACKAGE NOTE:** This SuperGrok package is complete. It already includes the 13 approved mockup PNGs, `MOCKUP_REFERENCE.md`, the horizontal MarinerX Labs logo, the standalone X icon, and the Phase 15 work order. Do not wait for missing assets and do not infer the design system from memory. Use the packaged PNGs and design elements as the source of truth.

**CONTEXT:** Phases 01–14 are complete — MarinerX Quant Command Center ("MarinerX Labs") is built, all 15 agents are operational, and the system is deployed and live on Railway. This is a **follow-up visual-fidelity pass only**: the interface must be updated to match 13 approved mockup images exactly. No backend logic, agent behavior, validation gauntlet, risk logic, or decision logic changes in this phase — this is frontend/`interface/web/` work exclusively.

---

## 1. Inputs

- `mockups/01_command_center_home.png` through `mockups/13_settings_system_control.png` — the 13 approved reference images.
- `mockups/MOCKUP_REFERENCE.md` — a written description of the exact visual system and per-page content as actually rendered in the mockups.
- `design_elements/marinerx_labs_logo.jpeg` — exact horizontal logo asset.
- `design_elements/marinerx_labs_x_icon.png` — exact standalone X icon asset.
- The existing, already-deployed codebase at `src/mcc/interface/web/` and its `static/` assets.

If `mockups/` or `design_elements/` is not present in the working directory, halt this phase only and locate the extracted final package. Do not proceed by guessing the visual system from prior specs — the packaged mockups and design elements are the source of truth now.

## 2. Establish the design token layer first

Before touching any individual page, derive one shared token set from the mockups + `MOCKUP_REFERENCE.md` — colors, typography, corner radius/shape convention, spacing scale, brand-cell treatment, sidebar/header treatment, and status-indicator/tag style.

Write this once as `src/mcc/interface/web/static/design-tokens.css` or the equivalent in the existing styling approach. Every page must consume this single token file. No page may hardcode its own one-off colors, spacing, or badge styles.

## 3. Per-page ownership

| Mockup Page | Owning Subagent | Existing Module |
|---|---|---|
| 01 Command Center Home | Overseer | `interface/web/` home view + agent-grid component |
| 02 Market Pulse | MarketPulse | internals/microstructure/heatmap views |
| 03 Indicators & Regime | IndicatorEngine + RegimeMonitor | indicator/regime views |
| 04 Strategy Registry | StrategyRunner | strategy registry view |
| 05 Validation & Verdicts | ValidationEngine | validation/verdict views |
| 06 Research Lab | ResearchLab | forecast lab / experiment tracker views |
| 07 Risk Command | RiskCommand | risk/PropGuardian views |
| 08 Trade-or-No-Trade | DecisionEngine | decision center view |
| 09 Execution & Orders | ExecutionGateway | execution/guardrail views |
| 10 Trade Journal | TradeJournal | journal view |
| 11 Performance Analytics | PerformanceAnalyst | performance view |
| 12 Reports | ReportPublisher | reports view |
| 13 Settings & System Control | Overseer | settings/config view |

Dispatch each subagent, in its own git worktree, to rebuild its page against the corresponding mockup and the shared token layer from Section 2.

## 4. Fidelity standard

For each page, the owning subagent must:

1. Load the mockup image and the running local dev build of its page side by side.
2. Reconcile colors, spacing, corner radius, typography, component placement, table/panel structure, sample-data presentation, chart styling, badges, and persistent chrome.
3. Capture a screenshot of the rebuilt page and report it alongside the mockup to the Build Manager as PASS evidence.

A claim of “matches” without both images side by side is not acceptable evidence.

## 5. Regression check

After all 13 pages pass individually:

1. Run the full existing test suite.
2. Confirm no backend functionality regressed.
3. Confirm no files outside `interface/web/` and static/UI assets were changed unless strictly required for frontend asset imports.

## 6. Commit, push to GitHub, verify Railway redeploy

1. Commit all changes with clear messages.
2. Push to the GitHub remote branch connected to Railway auto-deploy.
3. Monitor the resulting Railway deployment and confirm the build succeeds.
4. Confirm `/health` returns `200`.
5. Capture screenshots of all 13 pages from the live Railway URL.
6. Compare each live screenshot against its corresponding mockup as the final acceptance gate.

## 7. Autonomy

Full autonomy. No pausing, no mid-build reports. Checkpoint to `PROGRESS.md`, commit per phase, resolve blockers per the established Hard Blocker Policy. Report once, when the live site matches all 13 mockups and is confirmed deployed.

---

## PHASE 15 ACCEPTANCE GATE

- All 13 pages rebuilt against their mockups and shared `design-tokens.css`.
- The packaged logo and X icon are used exactly.
- Each page has side-by-side mockup vs rebuilt screenshot evidence.
- Full test suite green.
- No backend/agent logic touched.
- Changes committed and pushed.
- Railway build succeeds.
- `/health` returns `200`.
- Live-URL screenshots of all 13 pages captured and compared against the mockups.

Report PASS/FAIL with complete evidence.
