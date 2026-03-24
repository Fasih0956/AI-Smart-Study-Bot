"""
Dashboard Server
A real-time Flask + SocketIO web dashboard showing:
- Current class status
- Caption feed
- Attendance history
- System health
"""

import json
from pathlib import Path
from flask import Flask, render_template_string
from flask_socketio import SocketIO

from utils.state_store import StateStore

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
state = StateStore()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Attendance Bot Dashboard</title>
<meta http-equiv="refresh" content="5">
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --border: #1e1e2e;
    --accent: #7c3aed;
    --accent2: #06d6a0;
    --warn: #f59e0b;
    --danger: #ef4444;
    --text: #e2e8f0;
    --muted: #64748b;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
    padding: 2rem;
  }

  header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1rem;
  }

  .dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--accent2);
    box-shadow: 0 0 10px var(--accent2);
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  h1 { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.02em; }
  .subtitle { color: var(--muted); font-size: 0.85rem; font-family: 'JetBrains Mono', monospace; }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
  }

  .card-label {
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
  }

  .card-value {
    font-size: 1.4rem;
    font-weight: 700;
  }

  .status-idle { color: var(--muted); }
  .status-in_class { color: var(--accent2); }
  .status-error { color: var(--danger); }

  .badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
  }
  .badge-meet { background: #1a3a4a; color: #38bdf8; }
  .badge-zoom { background: #1a2a4a; color: #818cf8; }
  .badge-present { background: #14302a; color: var(--accent2); }
  .badge-failed { background: #2a1a1a; color: var(--danger); }

  .log-section { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }
  .log-section h2 { font-size: 1rem; font-weight: 700; margin-bottom: 1rem; }

  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th { text-align: left; color: var(--muted); font-weight: 400; font-family: 'JetBrains Mono', monospace;
       font-size: 0.7rem; text-transform: uppercase; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }
  td { padding: 0.75rem 0; border-bottom: 1px solid var(--border); }
  tr:last-child td { border-bottom: none; }

  .empty { color: var(--muted); font-style: italic; text-align: center; padding: 2rem; }
</style>
</head>
<body>
<header>
  <div class="dot"></div>
  <div>
    <h1>Attendance Bot</h1>
    <div class="subtitle">{{ student_name }} &middot; {{ roll_no }}</div>
  </div>
</header>

<div class="grid">
  <div class="card">
    <div class="card-label">Status</div>
    <div class="card-value status-{{ status }}">{{ status.upper() }}</div>
  </div>
  <div class="card">
    <div class="card-label">Current Class</div>
    <div class="card-value">{{ current_subject or '—' }}</div>
    {% if current_platform %}<span class="badge badge-{{ current_platform }}">{{ current_platform.upper() }}</span>{% endif %}
  </div>
  <div class="card">
    <div class="card-label">Attendance Marked</div>
    <div class="card-value">{{ '✅ YES' if attendance_marked else '⏳ Waiting' }}</div>
  </div>
  <div class="card">
    <div class="card-label">Sessions Today</div>
    <div class="card-value">{{ sessions_today }}</div>
  </div>
</div>

<div class="log-section">
  <h2>Attendance History</h2>
  {% if history %}
  <table>
    <thead>
      <tr>
        <th>Date</th><th>Time</th><th>Subject</th><th>Platform</th><th>Status</th>
      </tr>
    </thead>
    <tbody>
      {% for entry in history[-20:]|reverse %}
      <tr>
        <td>{{ entry.timestamp[:10] }}</td>
        <td>{{ entry.timestamp[11:16] }}</td>
        <td>{{ entry.subject }}</td>
        <td><span class="badge badge-{{ entry.platform }}">{{ entry.platform }}</span></td>
        <td><span class="badge badge-{{ entry.status }}">{{ entry.status }}</span></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty">No sessions logged yet.</div>
  {% endif %}
</div>
</body>
</html>
"""


@app.route("/")
def dashboard():
    current = state.get("current_class")
    history = _load_history()
    from datetime import date
    today = str(date.today())
    sessions_today = sum(1 for e in history if e.get("timestamp", "").startswith(today))

    return render_template_string(
        DASHBOARD_HTML,
        student_name="Fasih Ahmed",
        roll_no="24K0956",
        status=state.get("status") or "idle",
        current_subject=current["subject"] if current else None,
        current_platform=current["platform"] if current else None,
        attendance_marked=state.get("attendance_marked") or False,
        history=history,
        sessions_today=sessions_today,
    )


@app.route("/api/state")
def api_state():
    import flask
    return flask.jsonify(state.all())


def _load_history():
    p = Path("logs/attendance_history.json")
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return []


class DashboardServer:
    def run(self):
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
