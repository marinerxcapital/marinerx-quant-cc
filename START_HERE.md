# MarinerX SuperGrok Build Package — START HERE

One archive, two build specs, 15 named agents, one Railway deployment target. This file is the map.

---

## Package Contents

```
MarinerX_SuperGrok_Build_Package/
├── START_HERE.md                          ← this file
├── GROK_KICKOFF_PROMPT.md                 ★ the /goal objective you run
├── command-center/                        ← the main system (19 files)
│   ├── 00_ORCHESTRATOR_KICKOFF.md         Build Manager charter — read first
│   ├── 00B_PRE_FLIGHT_ADDENDUM.md         ★ Railway specifics, beta-stability mitigation, topology
│   ├── 00_MASTER_BRIEF.md                 constitution: principles, stack, 15-agent roster, file tree
│   ├── INDEX.md                           dependency graph, architecture diagram
│   └── 01_CORE_INFRA.md … 14_RAILWAY_DEPLOYMENT.md   the 14 work orders
└── tradeify-sync/                         ← account-data ingestion module (9 files)
    ├── INDEX.md                           build order for this subsystem
    ├── 00_MASTER_BRIEF.md                 constraints, stack, file tree for this subsystem
    └── 01_SCAFFOLD_CONFIG_MODELS.md … 07_TESTS_DOCS_ACCEPTANCE.md
```

---

## What This Builds

**MarinerX Quant Command Center** — a complete personal quant trading operating system: historical + live data, market internals, live heatmaps, indicators, regime detection, strategy engineering, a validation gauntlet, quant/ML research, risk management, a Trade-or-No-Trade decision engine, execution (paper-first), journaling, reporting, a real-time web dashboard (+ local-dev TUI), and **Railway cloud deployment**. Instruments: NQ, ES, CL, GC. Built by, and running as, **15 named agents** — the same 15 identities serve as both the build crew and the live runtime services you watch on the dashboard.

**Tradeify Sync Engine** — a read-only browser-automation subsystem that logs into your Tradeify dashboard (no API access available) and feeds account/trade data into the Command Center's `RiskCommand` (PropGuardian) and `TradeJournal` agents. **Recommended: runs locally on your own machine**, not on Railway — see "The Railway Question" below for why.

---

## Execution Environment — Grok Build on SuperGrok Heavy, Windows PowerShell

The plain grok.com chat window is turn-based by design and isn't built for unattended background execution — no set of instructions inside a chat message can change that. The tool that actually delivers "runs to completion, manages its own subagents, only pings me when done" is **Grok Build**, xAI's agentic CLI, specifically its **`/goal` mode**. Your SuperGrok Heavy subscription is what gates access to it.

**Setup (one time, PowerShell):**
```powershell
irm https://x.ai/cli/install.ps1 | iex
```
This is xAI's official Windows installer (released May 25, 2026). It installs the `grok` CLI and adds it to your PATH.

```powershell
grok login
```
Opens a browser for OAuth. **Sign in with the account that holds your SuperGrok Heavy subscription** — beta access is gated to that specific account, not to a plain API key.

```powershell
Expand-Archive -Path "$HOME\Desktop\MarinerX_SuperGrok_Build_Package.zip" -DestinationPath "$HOME\Desktop\MarinerX_Build"
cd "$HOME\Desktop\MarinerX_Build"
grok
```
Extracts the package and starts Grok Build inside that working directory — this matters, since Grok Build operates against the local codebase in its current directory.

**Before running the objective, confirm your auto-approval setting** for this session (check `/help` or `grok --help` in your installed version — exact flag names are still moving in this beta). Without auto-approval, the run will stall waiting for you to approve individual file writes, which defeats the point of an unattended build.

**Run the objective:** paste the contents of `GROK_KICKOFF_PROMPT.md` as your `/goal` (or as your first message if `/goal` isn't yet available in your installed version — check `/help`).

**One honest caveat, direct from Grok Build's own documentation:** parallel subagent coordination is explicitly flagged as its newest and least mature capability, most likely to misfire on complex, long-running jobs — and this build (15 subagents, 14 phases) is exactly that class of job. This package is designed around that reality (one git worktree per subagent, a commit after every phase gate, a `PROGRESS.md` checkpoint file) so that if a run ever stalls, restarting requires nothing more than you noticing and typing "continue" — never re-explaining anything. Full details in `command-center/00B_PRE_FLIGHT_ADDENDUM.md` §4.

`/goal` also gives you optional steering commands (`status`, `pause`, `resume`) if you want to check in — nothing in the workflow requires it.

---

## The Railway Question

You mentioned this may run on Railway. It's fully specified (Phase 14: Dockerfile, `railway.json`, volumes, health checks, environment variables) — confirmed against Railway's own current docs, which officially support Python + Playwright deployments.

**One trade-off worth knowing before you decide:** Tradeify Sync's browser automation is currently designed to run from your own residential IP address. If you containerize it and run it on Railway too, its traffic originates from a datacenter IP instead — many anti-automation/fraud-detection systems weight datacenter traffic as materially higher-risk than residential traffic, independent of the fact that the automation itself is unchanged and still read-only. **The default this package builds toward:** Tradeify Sync stays local on your machine; only the Command Center (data engine, risk, decision, dashboard) deploys to Railway. The fully-cloud alternative is fully documented in the addendum if you decide the trade-off is worth it for your use case — that choice is yours, made with the full picture.

---

## What You Get Back

A single **Final Build Report**, emitted after Phase 14's Railway gate passes, containing: build status, the actual file tree produced, per-phase gate results by subagent, test/coverage summary, all 15 runtime agents' start-up status, a Build-Decisions Ledger summary, the Railway deployment URL and health status, and — most important for you personally — a **Post-Build Activation Checklist**: the short list of one-time human actions (Tradeify login/2FA, Databento key, IQFeed credentials, explicit live-execution enable) required to move from "verified on replay data" to "connected to your real accounts." That checklist is the only thing you should expect to act on yourself.

---

## The One Honest Caveat (unchanged from every prior discussion)

This system is validation-first and risk-first by design — it will faithfully tell you when a strategy has no edge, and it should. The value of everything in this package is disciplined infrastructure and process, not a guarantee of profitability. Expect the worked example strategy in the Final Report to honestly fail its verdict; that is the system working correctly, not a build defect.
