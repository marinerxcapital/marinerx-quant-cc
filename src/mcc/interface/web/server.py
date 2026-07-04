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
    sup = _SUP
    if sup is None:
        # Always provide dynamic 15 agents even if not set from run (for direct test/web)
        from mcc.runtime.bootstrap import create_supervisor
        sup = create_supervisor(replay=True)
    snap = sup.snapshot()
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
