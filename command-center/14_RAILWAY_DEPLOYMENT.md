# PHASE 14 — RAILWAY DEPLOYMENT (final phase; only after Phase 13 passes locally)

**CONTEXT:** Phases 01–13 complete and locally verified: all 15 agents operational, web + TUI interfaces working, full test suite green. This phase ships the Command Center to Railway as the production deployment target. Owned directly by the Build Manager (cross-cutting), pulling in subagents as needed for their modules' deployment concerns.

---

## 1. `Dockerfile` (multi-stage)
- **Stage 1 (builder):** `python:3.11-slim`, install `uv`, copy `pyproject.toml`/lockfile, `uv sync --frozen` into a venv.
- **Stage 2 (runtime):** `python:3.11-slim`, copy the venv from Stage 1 + application code, create and switch to a non-root user, expose no hardcoded port (bind to `$PORT` at runtime).
- If AccountSync's Tradeify Sync subsystem is being containerized too (per Addendum §7's alternative path): base on Microsoft's official Playwright image, or add `playwright install --with-deps chromium` to Stage 2, and document the ≥1GB memory requirement in a comment.
- `HEALTHCHECK` directive hitting `GET /health` on the FastAPI app (see §3).

## 2. `railway.json` (or `nixpacks.toml` if Nixpacks build is preferred over the Dockerfile)
- Build: Dockerfile-based (`"builder": "DOCKERFILE"`).
- Start command: `python main.py run --interface web`.
- Restart policy: on-failure, reasonable max retries.
- Healthcheck path: `/health`, matching the Dockerfile `HEALTHCHECK`.

## 3. `src/mcc/interface/web/server.py` — add a `/health` endpoint
- Returns `200 {"status": "ok", "agents": {name: status for all 15}}` when the Supervisor and all agents are at least `idle` (not `error`), else `503`. This is both Railway's healthcheck target and a genuinely useful operational endpoint.
- Ensure the FastAPI app binds to `host="0.0.0.0", port=int(os.environ["PORT"])` — never a hardcoded port. Railway injects `PORT`; do not assume 8000.

## 4. Volumes
- Document (in `README.md`'s deployment section) the exact Railway dashboard steps to attach a volume mounted at `/app/data`, covering `sqlite`, `duckdb`/`parquet`, and `logs/`. Verify the app writes exclusively under this mount in production config (`config/prod.yaml` paths point at `/app/data/...`).

## 5. Environment Variables
- Produce a complete inventory (`.env.railway.example`) listing every variable both projects require (Databento key, IQFeed credentials if used, live-execution enable flag + token, the AccountSync bearer token from Addendum §1 if the hybrid-endpoint path is used, `PORT` is Railway-provided and not set manually).
- No secret may have a default value baked into code or the Dockerfile.

## 6. Process Split (optional; decide based on resource profile observed in Phase 13's local run)
- If the combined process (web + all 15 agents' async loops in one container) shows resource contention during Phase 13's soak test, split into two Railway services sharing the same volume: `web` (interface/API, health endpoint) and `worker` (Supervisor + agents). Document whichever choice is made and why, in `BUILD_DECISIONS.md`.

## 7. Deployment Execution
- If a Railway account/token is available in the build environment: run the actual deploy (`railway up` or GitHub-connected auto-deploy), confirm the health check goes green, and confirm the public `*.up.railway.app` domain serves the dashboard.
- If no Railway credentials are available at build time (expected per the Hard Blocker Policy): build and locally verify the Docker image (`docker build`, `docker run` with `PORT` set, confirm `/health` responds 200), document the exact `railway up` / dashboard steps in `README.md`, and mark live deployment as a pending Post-Build Activation item rather than blocking.

---

## PHASE 14 ACCEPTANCE GATE
- `docker build` succeeds; `docker run -e PORT=8080 ...` serves `/health` as `200` locally.
- If deployed live: Railway build log shows a successful image build; the health check passes; the public domain serves the dashboard and its websocket connection establishes.
- Volume-backed paths persist data across a container restart (verified by a restart-and-check test, local or on Railway).
- No secret is present in the built image (`docker history` / image inspection shows none).
- `.env.railway.example` enumerates every required variable with no defaults for secrets.

Report PASS/FAIL with evidence (build log excerpt, health-check response, or the documented manual-deploy steps if credentials were unavailable) to the Build Manager. This is the final gate — its PASS triggers the Final Build Report.
