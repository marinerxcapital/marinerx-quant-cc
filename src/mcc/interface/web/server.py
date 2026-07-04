"""FastAPI web server.

When started via `python main.py run --interface web`, the CLI sets _SUP
to the live Supervisor so /health returns real dynamic status.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import FastAPI

app = FastAPI(title="MarinerX Quant Command Center")

# MUST be set by launcher (main.py run) using bootstrap.create_supervisor()
# before uvicorn starts or before TestClient probes.
_SUP: Optional[Any] = None


@app.get("/health")
def health() -> Dict[str, Any]:
    if _SUP is None:
        # For direct uvicorn without launcher, provide a minimal but note it is not the full run spine.
        # Verification always sets it from bootstrap.
        return {"status": "degraded", "agents": {}, "ts": "now", "note": "no supervisor wired - use python main.py run"}
    snap = _SUP.snapshot()
    agent_status: Dict[str, str] = {}
    for name, info in snap.agents.items():
        agent_status[name] = info.get("status", "unknown")
    status = "ok" if all(s != "error" for s in agent_status.values()) else "degraded"
    ts_val = getattr(snap, "ts_utc", None)
    ts_str = ts_val.isoformat() if ts_val else "now"
    return {"status": status, "agents": agent_status, "ts": ts_str}


@app.get("/")
def root() -> Dict[str, str]:
    return {"name": "MarinerX Quant Command Center", "status": "running"}
