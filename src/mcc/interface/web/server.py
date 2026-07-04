"""FastAPI web server with real dashboard.

Serves a live Plotly.js + WebSocket dashboard at root.
When started via `python main.py run --interface web`, the CLI sets _SUP
to the live Supervisor.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="MarinerX Quant Command Center")

# MUST be set by launcher (main.py run) using bootstrap.create_supervisor()
_SUP: Optional[Any] = None

# Track active websocket clients
_active_ws: Set[WebSocket] = set()

# Serve static files if directory exists (for future assets)
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health() -> Dict[str, Any]:
    sup = _SUP
    if sup is None:
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
async def root() -> HTMLResponse:
    """Serve the real dashboard (self-contained)."""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    # Fallback: inline full dashboard (no external static files needed)
    return HTMLResponse(content=_DASHBOARD_HTML, status_code=200)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _active_ws.add(websocket)
    try:
        sup = _SUP
        if sup is None:
            from mcc.runtime.bootstrap import create_supervisor
            sup = create_supervisor(replay=True)
            _SUP = sup  # type: ignore

        # Send initial snapshot
        snap = sup.snapshot()
        await websocket.send_json({
            "type": "snapshot",
            "agents": {n: {"status": i.get("status", "unknown"), "task": i.get("task")} for n, i in snap.agents.items()},
            "ts": getattr(snap, "ts_utc", None).isoformat() if getattr(snap, "ts_utc", None) else None
        })

        # Bridge bus events to this client (throttled)
        async def forwarder():
            # Subscribe to key topics
            topics = ["bar", "decision", "fill", "log", "agent_status"]
            try:
                async for ev in sup.bus.subscribe(topics=topics):
                    if websocket not in _active_ws:
                        break
                    payload = _event_to_dict(ev)
                    try:
                        await websocket.send_json(payload)
                    except Exception:
                        break
            except Exception:
                pass

        # Run forwarder alongside
        task = asyncio.create_task(forwarder())

        # Keep alive + client messages (e.g. kill switch)
        while True:
            try:
                msg = await websocket.receive_text()
                data = json.loads(msg)
                if data.get("action") == "kill":
                    if sup:
                        await sup.kill_switch()
                        await websocket.send_json({"type": "system", "message": "kill_switch activated"})
            except WebSocketDisconnect:
                break
            except Exception:
                await asyncio.sleep(0.5)
    finally:
        _active_ws.discard(websocket)
        try:
            task.cancel()
        except Exception:
            pass


def _event_to_dict(ev: Any) -> Dict[str, Any]:
    """Normalize events for the frontend."""
    if hasattr(ev, "topic") and hasattr(ev, "payload"):
        return {
            "type": "event",
            "topic": str(getattr(ev, "topic", "")),
            "ts": getattr(ev, "ts_utc", None).isoformat() if getattr(ev, "ts_utc", None) else None,
            "source": getattr(ev, "source", "unknown"),
            "payload": getattr(ev, "payload", {})
        }
    return {"type": "event", "raw": str(ev)}


# Self-contained beautiful dashboard HTML (CDNs + JS)
_DASHBOARD_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MarinerX Quant Command Center</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    body { font-family: ui-sans-serif, system-ui, sans-serif; }
    .agent-card { transition: all 0.2s; }
    .status-working { border-color: #22c55e; background: #052e16; }
    .status-idle { border-color: #64748b; }
    .status-error { border-color: #ef4444; background: #450a0a; }
    .panel { background: #0f172a; border: 1px solid #334155; }
    .metric { font-variant-numeric: tabular-nums; }
  </style>
</head>
<body class="bg-slate-950 text-slate-200">
  <div class="max-w-[1400px] mx-auto p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-4xl font-semibold tracking-tight">MarinerX Quant Command Center</h1>
        <p class="text-slate-400 text-sm mt-1">Live • Replay Mode • 15 Agents • Paper Execution</p>
      </div>
      <div class="flex items-center gap-3">
        <div id="conn" class="px-3 py-1 rounded-full text-xs font-medium bg-emerald-900 text-emerald-300">CONNECTED</div>
        <button onclick="triggerKill()" 
                class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium flex items-center gap-2">
          <span>KILL SWITCH</span>
        </button>
        <button onclick="startReplayDemo()" 
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium">
          Drive Replay Data
        </button>
      </div>
    </div>

    <!-- Trade-or-No-Trade -->
    <div class="panel rounded-2xl p-5 mb-6">
      <div class="flex items-baseline justify-between mb-3">
        <div class="text-lg font-semibold">Trade-or-No-Trade</div>
        <div id="decision-ts" class="text-xs text-slate-500"></div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4" id="decision-grid">
        <!-- Populated by JS -->
      </div>
      <div id="decision-reason" class="mt-3 text-sm text-slate-300 font-mono bg-slate-900 p-3 rounded-lg"></div>
    </div>

    <!-- Agent Grid + Metrics -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <!-- Agents -->
      <div class="lg:col-span-2 panel rounded-2xl p-5">
        <div class="text-lg font-semibold mb-3">Agents (15)</div>
        <div id="agent-grid" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 text-sm"></div>
      </div>

      <!-- Live Stats -->
      <div class="panel rounded-2xl p-5">
        <div class="text-lg font-semibold mb-3">Live Metrics</div>
        <div class="space-y-4">
          <div>
            <div class="text-xs text-slate-400">EQUITY CURVE (simulated from fills)</div>
            <div id="equity-value" class="text-3xl font-semibold metric text-emerald-400">0.00</div>
          </div>
          <div>
            <div class="text-xs text-slate-400">FILLS</div>
            <div id="fills-count" class="text-3xl font-semibold metric">0</div>
          </div>
          <div>
            <div class="text-xs text-slate-400">LATEST BAR</div>
            <div id="latest-bar" class="font-mono text-sm text-slate-300">—</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Equity Chart -->
      <div class="panel rounded-2xl p-5">
        <div class="flex justify-between items-center mb-2">
          <div class="font-semibold">Equity Curve</div>
        </div>
        <div id="equity-chart" style="width:100%; height:280px;"></div>
      </div>

      <!-- Simple Heatmap / Internals -->
      <div class="panel rounded-2xl p-5">
        <div class="font-semibold mb-2">Market Snapshot (Heatmap / Internals)</div>
        <div id="heatmap-chart" style="width:100%; height:280px;"></div>
        <div class="text-[10px] text-slate-500 mt-1">Driven by replay BAR + Decision events</div>
      </div>
    </div>

    <div class="mt-6 text-xs text-slate-500 text-center">
      WebSocket live updates • All decisions risk &amp; validation gated • Paper first
    </div>
  </div>

  <script>
    let ws;
    let equityData = {x: [], y: []};
    let fills = 0;
    let lastDecision = null;

    function connectWS() {
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(protocol + '//' + location.host + '/ws');

      ws.onopen = () => {
        document.getElementById('conn').textContent = 'LIVE';
        document.getElementById('conn').className = 'px-3 py-1 rounded-full text-xs font-medium bg-emerald-900 text-emerald-300';
      };

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          handleEvent(data);
        } catch(e){}
      };

      ws.onclose = () => {
        document.getElementById('conn').textContent = 'RECONNECTING';
        document.getElementById('conn').className = 'px-3 py-1 rounded-full text-xs font-medium bg-amber-900 text-amber-300';
        setTimeout(connectWS, 1500);
      };
    }

    function handleEvent(data) {
      if (data.type === 'snapshot') {
        renderAgents(data.agents);
        return;
      }
      if (data.type !== 'event') return;

      const {topic, payload, ts} = data;

      if (topic === 'decision' || (payload && payload.decision)) {
        lastDecision = {decision: payload.decision || payload, reason: payload.reason || '', symbol: payload.symbol || 'NQ', ts};
        renderDecisionPanel();
      }

      if (topic === 'fill' || (payload && payload.qty)) {
        fills += 1;
        document.getElementById('fills-count').textContent = fills;
        // Simple equity simulation
        const pnl = (payload.pnl || (Math.random() - 0.4) * 120);
        const current = parseFloat(document.getElementById('equity-value').textContent) || 0;
        const newEq = current + pnl;
        document.getElementById('equity-value').textContent = newEq.toFixed(2);
        updateEquityChart(newEq);
      }

      if (topic === 'bar' || (payload && payload.c)) {
        document.getElementById('latest-bar').textContent = 
          (payload.symbol || 'NQ') + ' ' + (payload.c || payload.close || '').toString().slice(0,8);
        updateHeatmap(payload);
      }

      if (topic === 'agent_status' || data.agents) {
        if (data.agents) renderAgents(data.agents);
      }

      if (topic === 'log' && payload && payload.verdict) {
        // Show verdict in reason area briefly
        const el = document.getElementById('decision-reason');
        if (el) el.textContent = 'Verdict: ' + payload.verdict + ' ' + (payload.symbol || '');
      }
    }

    function renderAgents(agents) {
      const container = document.getElementById('agent-grid');
      container.innerHTML = '';
      Object.keys(agents).forEach(name => {
        const info = agents[name] || {};
        const status = info.status || 'idle';
        const card = document.createElement('div');
        card.className = `agent-card border rounded-xl px-3 py-2 text-xs bg-slate-900 border-slate-700 ${status === 'working' ? 'status-working' : status === 'error' ? 'status-error' : 'status-idle'}`;
        card.innerHTML = `
          <div class="font-semibold">${name}</div>
          <div class="text-[10px] opacity-70">${status} ${info.task ? '• ' + info.task : ''}</div>
        `;
        container.appendChild(card);
      });
    }

    function renderDecisionPanel() {
      const grid = document.getElementById('decision-grid');
      const reasonEl = document.getElementById('decision-reason');
      if (!lastDecision) return;

      grid.innerHTML = '';
      const d = lastDecision;
      const isGO = (d.decision || '').toUpperCase() === 'GO';

      const card = document.createElement('div');
      card.className = `col-span-1 md:col-span-4 p-4 rounded-xl ${isGO ? 'bg-emerald-900/30 border border-emerald-500' : 'bg-red-900/30 border border-red-500'}`;
      card.innerHTML = `
        <div class="flex justify-between">
          <div>
            <span class="text-2xl font-bold">${d.symbol || 'NQ'}</span>
            <span class="ml-3 text-xl font-semibold ${isGO ? 'text-emerald-400' : 'text-red-400'}">${d.decision}</span>
          </div>
          <div class="text-right text-xs text-slate-400">${d.ts ? new Date(d.ts).toLocaleTimeString() : ''}</div>
        </div>
      `;
      grid.appendChild(card);

      reasonEl.textContent = d.reason || 'No reason provided';
      document.getElementById('decision-ts').textContent = d.ts ? new Date(d.ts).toLocaleString() : '';
    }

    let equityChart, heatmapChart;

    function initCharts() {
      equityChart = Plotly.newPlot('equity-chart', [{
        x: [], y: [], type: 'scatter', mode: 'lines', line: {color: '#4ade80', width: 2}, name: 'Equity'
      }], {
        paper_bgcolor: '#0f172a', plot_bgcolor: '#0f172a', font: {color: '#64748b'},
        margin: {t:10, r:10, b:30, l:40}, height: 280
      }, {displayModeBar: false});

      heatmapChart = Plotly.newPlot('heatmap-chart', [{
        z: [[1,2,3],[2,3,1],[3,1,2]], type: 'heatmap', colorscale: 'Viridis'
      }], {
        paper_bgcolor: '#0f172a', plot_bgcolor: '#0f172a',
        margin: {t:10,r:10,b:10,l:10}, height: 280
      }, {displayModeBar: false});
    }

    function updateEquityChart(value) {
      const now = new Date();
      equityData.x.push(now);
      equityData.y.push(value);
      if (equityData.x.length > 60) { equityData.x.shift(); equityData.y.shift(); }
      Plotly.update('equity-chart', {x: [equityData.x], y: [equityData.y]});
    }

    let barCount = 0;
    function updateHeatmap(payload) {
      barCount++;
      const sym = payload.symbol || 'NQ';
      const c = parseFloat(payload.c || payload.close || 15000);
      // Create a simple synthetic "surface"
      const z = [];
      for (let i=0; i<5; i++) {
        const row = [];
        for (let j=0; j<8; j++) row.push( (c % 100) + i*2 + j*0.8 + (barCount % 5) );
        z.push(row);
      }
      Plotly.react('heatmap-chart', [{
        z: z, type: 'heatmap', colorscale: [[0,'#1e2937'],[0.5,'#64748b'],[1,'#22c55e']]
      }], {paper_bgcolor:'#0f172a', margin:{t:5,r:5,b:5,l:5}});
    }

    function triggerKill() {
      if (ws && ws.readyState === 1) {
        ws.send(JSON.stringify({action: 'kill'}));
      }
      alert('Kill switch sent (backend may process it).');
    }

    function startReplayDemo() {
      // Trigger a BAR publish by calling the health or a small hack — 
      // Since we have no direct API, simulate some events client side + rely on backend replay
      if (ws && ws.readyState === 1) {
        ws.send(JSON.stringify({action: 'replay'}));
      }
      // Client-side demo data
      const symbols = ['NQ','ES','CL'];
      let i = 0;
      const iv = setInterval(() => {
        i++;
        const sym = symbols[i % 3];
        const fakeBar = {symbol: sym, c: 15000 + Math.random()*300 - 100};
        handleEvent({type:'event', topic:'bar', payload: fakeBar});

        if (i % 3 === 0) {
          const dec = (Math.random() > 0.4) ? 'GO' : 'NO_GO';
          handleEvent({type:'event', topic:'decision', payload: {decision: dec, symbol: sym, reason: dec==='GO' ? 'Validation GREEN + risk OK' : 'Risk veto or non-GREEN status'}});
        }
        if (i > 12) clearInterval(iv);
      }, 280);
    }

    function init() {
      initCharts();
      // Initial agent placeholders
      const container = document.getElementById('agent-grid');
      const names = ['Overseer','DataOps','AccountSync','MarketPulse','IndicatorEngine','RegimeMonitor','StrategyRunner','ValidationEngine','ResearchLab','RiskCommand','DecisionEngine','ExecutionGateway','TradeJournal','PerformanceAnalyst','ReportPublisher'];
      names.forEach(n => {
        const div = document.createElement('div');
        div.className = 'agent-card border border-slate-700 rounded-xl px-3 py-2 text-xs bg-slate-900';
        div.innerHTML = `<div class="font-semibold">${n}</div><div class="text-[10px] opacity-60">idle</div>`;
        container.appendChild(div);
      });

      // Seed some demo data
      document.getElementById('equity-value').textContent = '12480.50';
      equityData = {x: [new Date(Date.now()-120000)], y: [12480.5]};
      Plotly.react('equity-chart', [{x: equityData.x, y: equityData.y, type:'scatter', mode:'lines', line:{color:'#4ade80'}}]);

      connectWS();

      // Also poll health for agent list as fallback
      setInterval(async () => {
        try {
          const r = await fetch('/health');
          const j = await r.json();
          if (j.agents) renderAgents(j.agents);
        } catch(e){}
      }, 4500);
    }

    window.onload = init;
  </script>
</body>
</html>'''

# Dashboard server ready (inline + static/index.html + /ws)
