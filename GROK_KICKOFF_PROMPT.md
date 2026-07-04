# /goal Objective — run this inside Grok Build (started in the extracted package's root folder)

**Before running this:** confirm auto-approval for tool calls is enabled in your Grok Build session (check `/help` or `grok --help` for the exact setting in your installed version). Without it, this run will stall waiting for you to approve individual file writes — which defeats the purpose.

---

Build the complete system specified in this working directory (`MarinerX_SuperGrok_Build_Package/`).

Read in this order before writing any code:
1. `START_HERE.md`
2. `command-center/00_ORCHESTRATOR_KICKOFF.md`
3. `command-center/00B_PRE_FLIGHT_ADDENDUM.md`
4. `command-center/00_MASTER_BRIEF.md`, then work orders `01`–`14`
5. `tradeify-sync/00_MASTER_BRIEF.md`, then work orders `01`–`07`

You are Build Manager. Operate fully autonomously per the Orchestrator Kickoff charter: dispatch each of the 15 named subagents (per the Master Brief's roster — the same 15 identities serve as build-subagents and runtime agents) into its own git worktree for its phase, self-verify every phase's Acceptance Gate with captured evidence (no PASS without it — see the Addendum), checkpoint progress to `PROGRESS.md`, commit to `main` per phase, and resolve every blocker per the Hard Blocker Policy.

Do not pause for my approval of intermediate decisions and do not summarize progress to me mid-build. The only exceptions are Grok Build's own tool-call approvals if auto-approval is unavailable in this session, and `/goal`'s built-in status/pause/resume steering, which I will use only if I choose to check in — neither requires action from you.

Complete Phases 01–13 fully (locally buildable, launchable, and testable — all 15 agents running, web dashboard live, full test suite green), then Phase 14 (Docker + Railway deployment; if Railway credentials aren't available in this environment, build and locally verify the container and document the exact deploy steps rather than blocking).

Do not report back until Phase 14's gate passes. Then deliver the Final Build Report specified in the charter, including the Post-Build Activation Checklist.

Begin.
