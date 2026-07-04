# MarinerX Quant Command Center + Tradeify Sync Engine

Validation-first. Risk-first. Honest baselines.

## Quickstart (from extracted root)
```powershell
python -m pip install -e ".[dev]"
python main.py doctor
python main.py run --interface web
# In browser or curl: http://localhost:8000/health
```

## Tradeify Sync (sibling)
cd tradeify-sync
python main.py doctor
python main.py sync   # second run inserts 0 duplicates (idempotent)

## Phase 14 Railway
- Dockerfile and railway.json provided.
- Local container verify:
  docker build -t marinerx-cc .
  docker run -e PORT=8080 -p 8080:8080 marinerx-cc
  curl http://localhost:8080/health   # expect 200 + agents list
- If no Docker/Railway token: use the artifacts + manual steps below. Volume at /app/data.

## Post-Build Activation Checklist (see FINAL_BUILD_REPORT)
1. One-time Tradeify discover (headed + 2FA)
2. Databento / IQFeed keys
3. (Optional) enable live execution
4. Railway deploy with volume

Safety: no override on GREEN status, risk vetoes are hard, paper-first by default.
```

## 1. Build Status
All 14 phases. Phase 13 Master Acceptance Checklist green. Phase 14 container artifacts + local verification (or documented steps).

(Full details in FINAL_BUILD_REPORT.md)
