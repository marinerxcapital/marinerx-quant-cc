# Local Development

Setup and run guide for **marinerx-quant-cc** on a developer machine.

**Repo path:** `MarinerX_Labs/01_ACTIVE_PROJECT/marinerx-quant-cc/`  
**Package:** `marinerx-cc` (Python ≥ 3.11)

---

## 1. Clone and enter repo

```bash
cd MarinerX_Labs/01_ACTIVE_PROJECT/marinerx-quant-cc
```

## 2. Create virtual environment (recommended)

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -e ".[dev]"
```

For R2/storage testing locally against real buckets (optional):

```bash
pip install -e ".[dev,deploy]"
```

No `requirements.txt` — use `pyproject.toml` extras:

| Extra | Packages |
|-------|----------|
| `dev` | pytest, pytest-asyncio, ruff, mypy |
| `deploy` | boto3 (R2) |

## 4. Configure environment

```bash
cp .env.example .env
```

Defaults work out of the box:

- SQLite at `./data/mcc.sqlite`
- Local object storage at `./data/objects`
- Web on `http://localhost:8000`
- `ENABLE_LIVE_EXECUTION=false`

Edit `.env` only if you need custom paths or ports.

## 5. Verify setup

```bash
python main.py doctor
```

Expected: database OK (sqlite), object storage ok (local), 15 agents registered, safety modules OK.

## 6. Run web service

```bash
python main.py run --interface web
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000/ | Dashboard SPA |
| http://localhost:8000/health | Health JSON |
| ws://localhost:8000/ws | Live WebSocket |

Uses replay adapter — no market data API keys required.

**Alternate entry:**

```bash
mcc run --interface web
```

## 7. Run background worker

Separate terminal:

```bash
python main.py run --interface worker
```

Writes heartbeats to `./data/mcc.sqlite` → `agent_heartbeats` every 30s. Stop with `Ctrl+C` (graceful shutdown).

## 8. Run tests

Full suite:

```bash
python -m pytest tests/ -q
```

Targeted:

```bash
# Safety gates
python -m pytest tests/test_safety_gates.py -q

# Deployment migration tests
python -m pytest tests/deployment/ -q

# Phase integration
python -m pytest tests/integration/ -q
```

**Baseline:** 70 tests (includes deployment tests added in migration).

Async tests use `pytest-asyncio` with `asyncio_mode = auto` (see `pyproject.toml`).

## 9. Lint and type check (optional)

```bash
ruff check src tests
mypy src
```

## 10. Docker local run

```bash
docker build -t marinerx-mcc .
docker run --rm -p 8080:8080 marinerx-mcc
curl http://localhost:8080/health
```

Docker defaults `PORT=8080`; local CLI defaults `8000`.

## 11. Data directories

Created automatically on startup:

```
data/
├── mcc.sqlite          # SQLite database
├── logs/
├── parquet/
├── reports/
└── objects/            # Local object storage
```

Delete `data/mcc.sqlite` to reset DB schema (recreated via `create_all`).

## 12. Tradeify development

- Specs only: `tradeify-sync/` (9 markdown files)
- Browser automation: **local machine only**
- Guard: `assert_tradeify_automation_allowed()` blocks cloud/production
- No Playwright in repo — implement locally per specs if needed

See `docs/deployment/TRADEIFY_LOCAL_ONLY_POLICY.md`.

## 13. Project layout (key paths)

```
marinerx-quant-cc/
├── main.py                 # CLI: doctor, run
├── src/mcc/
│   ├── core/config.py      # Environment settings
│   ├── interface/web/      # FastAPI + static SPA
│   ├── storage/            # DB, object store, models
│   ├── agents/pipeline.py  # 15-agent roster
│   └── runtime/bootstrap.py
├── tests/
│   └── deployment/         # Migration tests
├── render.yaml             # Render blueprint
├── railway.json            # Railway fallback
└── Dockerfile
```

## 14. Common issues

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: mcc` | `pip install -e ".[dev]"` or `PYTHONPATH=src` |
| Port in use | Change `APP_PORT` in `.env` |
| Doctor database FAIL | Ensure `data/` writable; check `DATA_DIR` |
| R2 tests skip/fail | Install `[deploy]` extra; or test local store only |
| Web shows legacy dashboard | Ensure `static/index.html` exists |

## 15. Production parity (optional local test)

Test production config validation without deploying:

```powershell
$env:APP_ENV = "production"
$env:DATABASE_URL = "postgresql://..."
$env:OBJECT_STORAGE_BACKEND = "r2"
# ... set R2_* ...
python main.py doctor
```

Use a dev/staging database — not production credentials on shared machines.

## Related docs

- `docs/deployment/ENVIRONMENT_VARIABLES.md`
- `docs/deployment/DATABASE_MIGRATION.md`
- `docs/deployment/DEPLOYMENT_VERIFICATION.md`