# GROK CONTINUATION DIRECTIVE — Close the "Built But Not Wired" Gap + Complete Missing Subsystems
### Target: https://marinerx-labs-api.onrender.com/#home — live, deployed, majority non-functional per direct user report.
### Repo: `gh repo clone marinerxcapital/marinerx-quant-cc`

---

## 0. Confirm Repo State First

```
gh repo clone marinerxcapital/marinerx-quant-cc
cd marinerx-quant-cc
```

Work directly against this repo. Do not assume a local checkout already exists — clone fresh if there's any doubt about working-tree state matching what's actually deployed on Render.

---

## 1. Current Verified State (do not re-derive — confirm against this, then act)

Per the last authoritative project summary and CRITICAL PATCH 01:

| Component | Verified Status |
|---|---|
| Render + Neon + R2 deployment | **Live** — site reachable at the URL above |
| `risk_veto` pipeline wiring | Patch was issued (CRITICAL_PATCH_01) — **verify it landed; do not assume** |
| MarketPulse, IndicatorEngine, TradeJournal | **Missing / NoOp** as of last verified state |
| Tradeify Sync Engine | **Spec-only** — 9 markdown files, zero Python implementation |
| AccountSync agent | Partial — has nothing real to read yet, since Tradeify Sync doesn't exist as code |
| Dashboard UI | Shell with **mock data** (`pages.js`) — not fed by live bus/API events |

**User-reported symptoms, mapped to root cause:**
- *"Not connected to my Tradeify dashboard"* → Tradeify Sync Engine was never actually built, only specified.
- *"Not at a quantitative research level"* → Three core agents (MarketPulse, IndicatorEngine, TradeJournal) are stubs; confirm Phase 16/17 upgrades (Riskfolio-Lib, QuantStats, statsmodels, forecast extensions) are actually invoked by the live pipeline, not just present as isolated, unit-tested modules.
- *"Majority of the program is not usable"* → The UI displays mock data regardless of what the backend does. Until this is wired, no backend progress will be visible to the user at all — **this should be treated as a leading priority for that reason alone.**

---

## 2. Systemic Instruction — Do Not Just Patch the Three Symptoms

Before starting new feature work, run an **end-to-end wiring audit**: for every agent-to-agent and agent-to-UI data path in the system, verify with an *integration test* (a real event traveling through the real pipeline) — not a unit test on an isolated function — that data actually flows. This is exactly the category of bug CRITICAL_PATCH_01 found in the risk veto path, and it is reasonable to assume it is not the only instance. Where you find another one, log it and fix it with the same rigor as that patch, before or alongside the named priorities below.

---

## 3. Priority-Ordered Task List

### P0 — Verify CRITICAL_PATCH_01 Landed
Confirm `src/mcc/agents/pipeline.py` no longer hardcodes `risk_veto=False` in either `DecisionEngineAgent._listen` or `ExecutionGatewayAgent._listen`, and that `tests/integration/test_pipeline_risk_veto.py` exists and passes. If not done, this is still priority zero, above everything below.

### P1 — Build Tradeify Sync Engine For Real
The full 7-phase specification for this subsystem already exists (scaffold/config/models → browser/auth → discovery → scrapers/exports → normalize/storage → pipeline/scheduler/CLI → tests/docs). Implement it — this has been designed in detail but never actually written as code. Once built:
- Wire `AccountSync` to read its output (`data/tradeify_sync.db`, read-only, WAL mode) as originally specified.
- **One step in this subsystem cannot be automated and is not yours to perform:** the one-time Tradeify login/2FA via the `discover` command requires the human user, in a headed browser, on their own machine. Build everything up to and including that step being ready to run; flag it clearly as the one blocking human action in your final report, exactly as the original Tradeify Sync spec already requires.

### P2 — Build Out the Three Missing Agents
`MarketPulse` (Phase 03: internals, microstructure, heatmaps), `IndicatorEngine` (Phase 04: indicator library + engine), `TradeJournal` (Phase 11: structured trade logging) — currently NoOp/minimal. Build against their original phase specs. While doing so, confirm `ValidationEngine`, `ResearchLab`, and `RiskCommand` are actually being called by the live pipeline with the Phase 16/17 upgrades active — not just present as passing unit tests in isolation, per Section 2's audit instruction.

### P3 — Wire the UI to Live Data
Remove `pages.js`'s mock data. Connect the dashboard to the real websocket/API feed from the running agents. This is what will make the user's own eyes confirm progress on P0–P2 — sequence it so visible improvement happens as early as possible, not only after every backend piece is finished.

---

## 4. Evidence Mandate (unchanged from every prior phase in this project)

No PASS without captured evidence: real `pytest` output, a real integration test proving end-to-end data flow (not a unit test), and — for P3 specifically — a screenshot or equivalent proof that the live dashboard is showing real, non-mock data. A narrative claim that something "should work now" is not acceptable evidence.

---

## 5. Acceptance Criteria

- CRITICAL_PATCH_01 confirmed landed (or completed now if it wasn't).
- Tradeify Sync Engine exists as real, tested Python code; `AccountSync` reads real (or realistically fixture-driven, pending the human login step) data from it.
- MarketPulse, IndicatorEngine, and TradeJournal are functioning agents, not stubs, each with integration-level evidence of real data flow.
- The live dashboard at the Render URL displays real backend state, not `pages.js` mock data.
- At least one further "built but not wired" instance (if any exists) is found and fixed via the same audit discipline as CRITICAL_PATCH_01.
- Full existing test suite remains green throughout.

---

## 6. Handoff Message

```
Continue work on the live MarinerX Labs deployment at
https://marinerx-labs-api.onrender.com/#home — majority of the program is currently not
usable. Read GROK_CONTINUATION_DIRECTIVE.md in full before acting.

First: confirm whether CRITICAL_PATCH_01 (risk_veto pipeline wiring) actually landed — verify,
don't assume. If not, that is still priority zero.

Then, in order: (1) build the Tradeify Sync Engine subsystem for real — it has a complete
7-phase spec but zero Python implementation, and AccountSync has nothing to read until this
exists; flag the one-time login/2FA step clearly as the single action I need to do myself,
(2) build out MarketPulse, IndicatorEngine, and TradeJournal, currently stubs, against their
existing phase specs, while confirming Phase 16/17's upgrades are actually invoked by the live
pipeline and not just unit-tested in isolation, (3) wire the dashboard to real data, removing
pages.js's mock data, so I can actually see progress on the backend work as it happens.

Before any of this, run an end-to-end wiring audit: for every agent-to-agent and agent-to-UI
data path, confirm with a real integration test that data actually flows — the risk_veto bug
was exactly this failure mode (module built, unit-tested, never actually wired in), and it may
not be the only instance.

Full autonomy, evidence-based verification, git discipline as established throughout this
project. Report once, with captured evidence for every item above.

Begin.
```
