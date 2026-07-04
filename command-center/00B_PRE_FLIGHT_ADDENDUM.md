# 00B — PRE-FLIGHT ADDENDUM
### Supersedes/extends §§5,7 of `00_ORCHESTRATOR_KICKOFF.md`. Read this alongside the Kickoff before dispatching Phase 01.

---

## 1. Cross-Package Topology (resolves the undefined IPC scheme)

The prior integration spec (`integration/quant_hub_bus.py`, `bus_endpoint: "ipc://marinerx-quant-hub.bus"`) is a **placeholder, not a protocol** — build accordingly:

- **Directory layout (local dev):** both projects live as siblings: `tradeify-sync/` and `command-center/` under one root.
- **Integration mechanism — use this, not a message broker:** Tradeify Sync persists to its own `data/tradeify_sync.db` (SQLite) and exports parquet snapshots. The Command Center's `data/accounts/sync_adapter.py` reads that SQLite file **directly** on its own polling cadence (read-only connection, SQLite WAL mode to avoid lock contention with Tradeify Sync's writer). No socket, no ZeroMQ, no IPC endpoint required.
- **If Command Center runs on Railway and Tradeify Sync runs locally (the recommended split — see §7):** the adapter cannot read a local file over the network directly. Add a minimal authenticated read-only sync endpoint: Tradeify Sync exposes `GET /api/account-state` (FastAPI, bound to localhost + a reverse tunnel, or pushed via a scheduled upload of the SQLite file/parquet snapshot to the Railway volume through an authenticated `PUT`). Use a long random bearer token in `.env` on both sides — never expose this endpoint unauthenticated to the public internet.
- **Staleness contract:** the adapter flags `stale=True` if `last_synced_utc` exceeds `2 × cadence_minutes`. `PropGuardian` treats stale account state as a soft risk downgrade (reduce size), not a hard LOCKOUT.

## 2. The One Category of Action That Cannot Be Automated

**The build is 100% autonomous; going live afterward is not, by design.**

- Tradeify Sync's `discover`/`login` flow requires a human to complete login and 2FA/captcha in a headed browser. No agent should attempt to bypass, script, or pre-store a 2FA code.
- The build must construct, wire, and **fully test** this flow using the replay adapter and mocked/fixture-driven auth (per the Hard Blocker Policy) so it ships complete and verified. It cannot *activate* against the real account without the user, once, later.
- Same logic applies to: Databento API key, IQFeed subscription/credentials, Railway account/token if absent at build time, and enabling `execution/live_stub.py`.
- **Final Report item 11** is the enumerated, one-time human actions required to go live — the only list the user should ever act on personally.

## 3. Evidence-Based Verification Mandate (extends validation-first rigor to the build process itself)

**No PASS without captured evidence.**

- A subagent reporting PASS must include the literal output it verified against — the `pytest` summary line, actual computed numeric values (e.g., DSR/PF figures from the discrimination test, not a claim it "looked right"), and `ruff`/`mypy` exit output.
- The Build Manager rejects any PASS lacking this evidence and returns it to the subagent for re-verification. Zero exceptions for: no-look-ahead (04/05), the validation-discrimination test (06), decision-determinism (09), the end-to-end replay test (13), and the Railway health-check response (14).
- Fabricating or mocking away the underlying computation to force a green result is treated with the same severity as bypassing a safety gate.

## 4. Grok Build Beta-Stability Mitigation (read this one carefully)

Grok Build's own documentation is explicit that **parallel subagent coordination is its newest and least mature capability** and is the part most likely to misfire on complex, long-running jobs — this build qualifies as exactly that class of job (15 subagents, 14 phases, thousands of lines of typed Python). Design and expectations accordingly:

- **Worktree isolation (§3 of the Kickoff) is not optional polish — it is the primary mitigation.** Each subagent working in its own git worktree means a coordination failure in one subagent cannot silently corrupt another's in-progress files, and the Manager's merge step (Execution Loop §4.6) is the point where conflicts surface visibly rather than being masked.
- **Commit granularity is a second mitigation.** Commit after every phase gate passes, not just at the end — if a session degrades mid-build, the git history bounds the blast radius to "since the last passing phase," not "since the start."
- **Realistic completion expectation:** despite the full autonomy design in this package, the user should expect that a build of this size, on a beta tool whose own docs flag subagent-coordination as fragile, may occasionally require the user to notice a stalled or errored `/goal` run and issue a bare "continue" or restart — this is a platform-maturity limitation, not a gap in this package's instructions. `PROGRESS.md` (§5) and the git history exist specifically so that any such restart requires zero re-explanation.
- If subagent parallelism itself appears to be causing repeated failures on a given phase, the Build Manager should fall back to building that phase's subagent work **serially** (no parallel worktree for that one phase) rather than repeatedly retrying a failing parallel dispatch — a slower, working build beats a fast, corrupted one.

## 5. Checkpoint & Resume Protocol

Maintain `PROGRESS.md` in the project root, updated after every phase gate passes: current phase, subagent, worktree, files completed vs. planned, and the last verified evidence block. If a session ends before Phase 14 is reached, the next session's first action is reading `PROGRESS.md` and resuming exactly where it left off — never restarting from scratch, never marking a phase complete to "wrap up" a session.

**Mirror this into `/goal`'s own progress checklist** so its native plan–execute–observe–replan loop tracks phase completion directly. Restarting `/goal` on the same working directory should pick the checklist back up without the user re-explaining anything.

## 6. Dependency Resolution Policy

If a pinned library version doesn't resolve, resolve to the nearest compatible stable release, record the substitution in `BUILD_DECISIONS.md`, and continue. Never block on a version-pin mismatch.

## 7. Railway Deployment Specifics (Phase 14 — build against these confirmed facts)

- **Playwright/browser automation on Railway is officially supported** via Docker: use Microsoft's official Playwright image or install with `playwright install --with-deps chromium` in a Dockerfile. Allocate **≥1 GB RAM** for a single headless Chromium instance; more per concurrent session.
- **Recommended split (default; lower risk):** run **Tradeify Sync locally** on the user's own machine (preserves the original residential-IP, low-footprint safety posture) and deploy only the **Command Center** (data/quant engine/risk/decision/dashboard) to Railway. This is the default this package builds toward.
- **Alternative (fully cloud, higher detection-risk):** containerize Tradeify Sync too, using the official Playwright Docker approach above, with its `data/sessions/` mounted to a **Railway volume** so the persisted login session survives redeploys. **State this trade-off explicitly in the Final Report if built:** requests then originate from a Railway datacenter IP rather than the user's residential IP, which many anti-automation/fraud-detection systems weight as materially higher-risk traffic than residential IP requests — this changes Tradeify Sync's risk profile even though the automation itself is unchanged and still read-only. Build this path only if selected; default to the recommended split otherwise.
- **Command Center Dockerfile:** multi-stage build, `python:3.11-slim` base, `uv sync --frozen` for reproducible installs, non-root user, `HEALTHCHECK` hitting a `/health` endpoint on the FastAPI app.
- **`railway.json` / `nixpacks.toml`:** define the build (Dockerfile-based) and start command (`python main.py run --interface web`). Bind to `0.0.0.0:$PORT` — Railway injects `PORT` automatically; do not hardcode a port.
- **Volumes:** mount a Railway volume at `/app/data` for `sqlite`, `duckdb`/`parquet`, and `logs/` so state survives redeploys.
- **Environment variables:** every `.env` key from both projects maps to a Railway service variable of the same name (set via dashboard Variables tab or `railway variables set KEY=value`). Never bake secrets into the image.
- **Process split (optional, recommended for cleaner scaling):** one Railway service for the web/API process (`interface/web`, decision-facing read paths), one for the background worker process (Supervisor + all 15 agents' async loops) if the Manager judges the combined single-process approach is resource-constrained; both share the same volume and database.
- **TUI is local-dev only** on Railway (no interactive terminal on a headless host) — the web dashboard is the production interface; confirm this is reflected in Phase 12's build.

## 8. Version Control as a Deliverable

`git init` at project root before Phase 01. Commit after every phase gate passes (`Phase NN — <agent> — gate PASS`), tag each (`git tag phaseNN`), and merge each subagent's worktree into `main` at that point. This is the literal, reviewable audit trail of the entire unsupervised build.

---

**Net effect on your side:** unchanged from the plain-language instructions in `START_HERE.md`. This addendum is read by the Build Manager alongside the Kickoff and removes every ambiguity it would otherwise have had to resolve unilaterally — including, now, the Railway deployment path and the realistic operating expectations for Grok Build's current beta maturity.
