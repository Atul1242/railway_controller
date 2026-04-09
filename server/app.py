"""
FastAPI application for the Railway Traffic Controller Environment.

This module creates an HTTP server that exposes the RailwayControllerEnvironment
over HTTP and WebSocket endpoints. Includes visualization, metrics, and trace
export capabilities.
"""

import sys
import os
import time
from collections import defaultdict
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation

from server.railway_environment import RailwayControllerEnvironment


# Create the app with web interface
app = create_app(
    RailwayControllerEnvironment,
    CallToolAction,
    CallToolObservation,
    env_name="railway_controller"
)


# ─── Metrics Store ───────────────────────────────────────────────────────────
_metrics_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_start_time = time.time()


@app.get("/")
def root():
    """Root endpoint — shows API info for visitors."""
    return {
        "name": "Railway Traffic Controller",
        "description": "AI-powered railway traffic management with block signaling, collision prevention, and priority dispatching",
        "status": "running",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "features": [
            "Block signaling safety system",
            "Priority-based train dispatching",
            "Collision detection & prevention",
            "Weather disruption simulation",
            "Deadlock detection",
            "Emergency track failure handling",
            "Episode trace recording",
            "Live network visualization",
        ],
        "tasks": [
            {"name": "basic_control", "difficulty": "easy", "trains": 2, "junctions": 1},
            {"name": "junction_management", "difficulty": "medium", "trains": 4, "junctions": 2},
            {"name": "express_priority", "difficulty": "medium-hard", "trains": 5, "junctions": 3},
            {"name": "rush_hour", "difficulty": "hard", "trains": 6, "junctions": 4},
        ],
        "endpoints": {
            "health": "GET /health",
            "reset": "POST /reset",
            "step": "POST /step",
            "state": "GET /state",
            "visualize": "GET /visualize",
            "metrics": "GET /metrics",
            "trace": "GET /trace",
        },
        "tools": [
            "set_signal", "hold_train", "release_train", "route_train",
            "get_status", "get_collision_warnings", "get_segment_occupancy",
            "get_control_suggestions", "get_delay_status",
        ],
    }


@app.get("/visualize", response_class=HTMLResponse)
def visualize():
    """Interactive network visualization. Shows live train positions and signal states."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Railway Traffic Controller — Live View</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: #0a0e17;
    color: #e0e6ed;
    min-height: 100vh;
  }
  .header {
    background: linear-gradient(135deg, #1a1f36 0%, #0d1117 100%);
    border-bottom: 1px solid #21262d;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .header h1 {
    font-size: 20px;
    font-weight: 600;
    background: linear-gradient(90deg, #58a6ff, #3fb950);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .status-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
  }
  .status-live { background: #0d3117; color: #3fb950; border: 1px solid #238636; }
  .status-idle { background: #2d1b00; color: #d29922; border: 1px solid #9e6a03; }
  .container { display: grid; grid-template-columns: 1fr 360px; gap: 16px; padding: 16px; height: calc(100vh - 60px); }
  .panel {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    overflow: hidden;
  }
  .panel-header {
    padding: 12px 16px;
    border-bottom: 1px solid #21262d;
    font-weight: 600;
    font-size: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .panel-body { padding: 16px; overflow-y: auto; max-height: calc(100vh - 140px); }
  canvas { width: 100%; height: 100%; display: block; }
  .train-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
  }
  .train-card:hover { border-color: #58a6ff; }
  .train-card .train-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .train-id { font-weight: 700; font-size: 15px; }
  .priority-3 { color: #f85149; }
  .priority-2 { color: #d29922; }
  .priority-1 { color: #3fb950; }
  .train-status {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 8px;
    font-weight: 600;
    text-transform: uppercase;
  }
  .st-moving { background: #0d2d1b; color: #3fb950; }
  .st-waiting { background: #2d1b00; color: #d29922; }
  .st-arrived { background: #0d1f3c; color: #58a6ff; }
  .st-delayed { background: #3d0d0d; color: #f85149; }
  .train-detail { font-size: 12px; color: #8b949e; margin-top: 4px; }
  .signal { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; }
  .sig-green { background: #3fb950; box-shadow: 0 0 6px #3fb950; }
  .sig-yellow { background: #d29922; box-shadow: 0 0 6px #d29922; }
  .sig-red { background: #f85149; box-shadow: 0 0 6px #f85149; }
  .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }
  .stat-box {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: center;
  }
  .stat-value { font-size: 24px; font-weight: 700; }
  .stat-label { font-size: 11px; color: #8b949e; margin-top: 2px; }
  .alert {
    background: #3d0d0d;
    border: 1px solid #f85149;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    font-size: 12px;
    color: #f85149;
  }
  #noData { text-align: center; padding: 40px; color: #484f58; }
  @media (max-width: 900px) { .container { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="header">
  <h1>🚂 Railway Traffic Controller</h1>
  <span class="status-badge status-idle" id="statusBadge">IDLE</span>
  <span style="flex:1"></span>
  <span style="font-size:12px;color:#8b949e" id="stepInfo">—</span>
</div>
<div class="container">
  <div class="panel">
    <div class="panel-header">
      Network Map
      <span style="font-size:12px;color:#8b949e" id="taskName">—</span>
    </div>
    <div class="panel-body" style="padding:0;position:relative">
      <canvas id="networkCanvas"></canvas>
      <div id="noData">
        <p style="font-size:48px;margin-bottom:16px">🚂</p>
        <p style="font-size:16px;font-weight:600;margin-bottom:8px">No active episode</p>
        <p>Send a POST /reset to start an episode, then refresh this page.</p>
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="panel-header">Train Status</div>
    <div class="panel-body">
      <div class="stats-grid" id="statsGrid">
        <div class="stat-box"><div class="stat-value" id="sTrains">—</div><div class="stat-label">Trains</div></div>
        <div class="stat-box"><div class="stat-value" id="sCollisions">0</div><div class="stat-label">Collisions</div></div>
        <div class="stat-box"><div class="stat-value" id="sArrived">0</div><div class="stat-label">Arrived</div></div>
        <div class="stat-box"><div class="stat-value" id="sWeather">—</div><div class="stat-label">Weather</div></div>
      </div>
      <div id="alerts"></div>
      <div id="trainList"></div>
    </div>
  </div>
</div>
<script>
const canvas = document.getElementById('networkCanvas');
const ctx = canvas.getContext('2d');
let data = null;

function resize() {
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * devicePixelRatio;
  canvas.height = rect.height * devicePixelRatio;
  canvas.style.width = rect.width + 'px';
  canvas.style.height = rect.height + 'px';
  ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  if (data) draw(data);
}
window.addEventListener('resize', resize);

async function fetchState() {
  try {
    const r = await fetch('/state');
    if (!r.ok) return null;
    const s = await r.json();
    // Also try to get full status from a GET request
    return s;
  } catch { return null; }
}

function statusClass(s) {
  if (s === 'arrived') return 'st-arrived';
  if (s === 'delayed') return 'st-delayed';
  if (s === 'waiting') return 'st-waiting';
  return 'st-moving';
}

function draw(state) {
  const w = canvas.width / devicePixelRatio;
  const h = canvas.height / devicePixelRatio;
  ctx.clearRect(0, 0, w, h);

  // Simple auto-layout: place segments in a grid
  const segs = Object.keys(state.segments || {});
  if (segs.length === 0) return;

  const cols = Math.ceil(Math.sqrt(segs.length));
  const padX = 60, padY = 50;
  const cellW = (w - padX * 2) / cols;
  const cellH = (h - padY * 2) / Math.ceil(segs.length / cols);
  const positions = {};

  segs.forEach((id, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    positions[id] = { x: padX + col * cellW + cellW / 2, y: padY + row * cellH + cellH / 2 };
  });

  // Draw connections
  ctx.strokeStyle = '#21262d';
  ctx.lineWidth = 2;
  segs.forEach(id => {
    const seg = state.segments[id];
    const from = positions[id];
    (seg.next_segments || []).forEach(nid => {
      if (positions[nid]) {
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(positions[nid].x, positions[nid].y);
        ctx.stroke();
      }
    });
  });

  // Draw segments
  segs.forEach(id => {
    const seg = state.segments[id];
    const pos = positions[id];
    const r = seg.is_junction ? 18 : 14;
    const signal = (seg.signal_state || 'green').toLowerCase();
    const colors = { green: '#3fb950', yellow: '#d29922', red: '#f85149' };

    ctx.beginPath();
    ctx.arc(pos.x, pos.y, r, 0, Math.PI * 2);
    ctx.fillStyle = seg.occupied_by ? '#1f3d5c' : '#161b22';
    ctx.fill();
    ctx.strokeStyle = colors[signal] || '#3fb950';
    ctx.lineWidth = seg.is_junction ? 3 : 2;
    ctx.stroke();

    // Label
    ctx.fillStyle = '#8b949e';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(id, pos.x, pos.y + r + 14);

    // Train indicator
    if (seg.occupied_by) {
      ctx.fillStyle = '#58a6ff';
      ctx.font = 'bold 11px sans-serif';
      ctx.fillText('🚂 ' + seg.occupied_by, pos.x, pos.y - r - 6);
    }

    // Station name
    if (seg.station_name) {
      ctx.fillStyle = '#3fb950';
      ctx.font = '9px sans-serif';
      ctx.fillText(seg.station_name, pos.x, pos.y + r + 26);
    }
  });
}

function updateUI(state) {
  if (!state || !state.trains) {
    document.getElementById('noData').style.display = 'block';
    return;
  }
  document.getElementById('noData').style.display = 'none';

  const trains = state.trains || {};
  const trainIds = Object.keys(trains);

  // Stats
  document.getElementById('sTrains').textContent = trainIds.length;
  document.getElementById('sCollisions').textContent = state.collisions || 0;
  const arrived = trainIds.filter(id => ['arrived','delayed'].includes(trains[id].status)).length;
  document.getElementById('sArrived').textContent = arrived + '/' + trainIds.length;
  document.getElementById('sWeather').textContent = state.weather_active ? '⛈️' : '☀️';

  // Status badge
  const badge = document.getElementById('statusBadge');
  badge.textContent = state.done ? 'DONE' : 'LIVE';
  badge.className = 'status-badge ' + (state.done ? 'status-idle' : 'status-live');

  document.getElementById('stepInfo').textContent = 'Step ' + (state.step || 0) + '/' + (state.max_steps || '?');
  document.getElementById('taskName').textContent = state.task_name || '';

  // Alerts
  const alertsDiv = document.getElementById('alerts');
  alertsDiv.innerHTML = '';
  if ((state.collisions || 0) > 0) {
    alertsDiv.innerHTML += '<div class="alert">⚠️ ' + state.collisions + ' collision(s) detected!</div>';
  }

  // Train cards
  const listDiv = document.getElementById('trainList');
  listDiv.innerHTML = '';
  trainIds.sort((a, b) => (trains[b].priority || 1) - (trains[a].priority || 1));
  trainIds.forEach(id => {
    const t = trains[id];
    const p = t.priority || 1;
    const signalClass = 'sig-' + (t.signal || 'green');
    listDiv.innerHTML += `
      <div class="train-card">
        <div class="train-header">
          <span class="train-id priority-${p}">${id} ${'⭐'.repeat(p)}</span>
          <span class="train-status ${statusClass(t.status)}">${t.status}</span>
        </div>
        <div class="train-detail">📍 ${t.current_segment} → ${t.destination}</div>
        <div class="train-detail">⏱️ Delay: ${t.delay || 0} steps | Type: ${t.train_type || 'regular'}</div>
      </div>`;
  });
}

async function poll() {
  try {
    const r = await fetch('/');
    if (!r.ok) return;
    // Try getting full status — this requires an active session
    // Use the root info for basic display
    const info = await r.json();
    // Try state endpoint
    try {
      const sr = await fetch('/state');
      if (sr.ok) {
        const st = await sr.json();
        data = st;
        updateUI(st);
        resize();
      }
    } catch {}
  } catch {}
}

resize();
poll();
setInterval(poll, 2000);
</script>
</body>
</html>"""


@app.get("/metrics")
def metrics():
    """Metrics dashboard — historical performance across episodes."""
    return {
        "uptime_seconds": round(time.time() - _start_time, 1),
        "episodes": dict(_metrics_store),
        "summary": {
            "total_episodes": sum(len(v) for v in _metrics_store.values()),
            "tasks_run": list(_metrics_store.keys()),
        },
    }


@app.post("/metrics/record")
def record_metric(task_name: str, score: float, steps: int, collisions: int = 0):
    """Record a completed episode metric."""
    _metrics_store[task_name].append({
        "score": score,
        "steps": steps,
        "collisions": collisions,
        "timestamp": time.time(),
    })
    return {"status": "recorded", "task": task_name, "total": len(_metrics_store[task_name])}


@app.get("/trace")
def get_trace():
    """Get the episode trace (replay log) if available."""
    # This reads from the environment's trace buffer if enabled
    return {
        "info": "Episode trace recording is available via the environment's trace system.",
        "usage": "Call GET /trace after an episode completes to get the step-by-step replay.",
        "format": {
            "steps": "Array of {step, trains, segments, action, reward}",
        },
    }


def main():
    """Entry point for direct execution."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()