from __future__ import annotations
from typing import Any
from flask import Flask, request, jsonify, Response
from services.api.orchestrator import REGISTRY, start_run, ARTIFACTS_ROOT

import os
import io
import zipfile

import time
import json
from collections import deque, defaultdict
try:
    from flask_sock import Sock
except Exception:  # pragma: no cover
    Sock = None  # Optional dependency for WS

app = Flask(__name__)

# Configuration helpers (overridable via app.config in tests)

def _get_api_key() -> str | None:
    if 'API_KEY' in app.config:
        return app.config.get('API_KEY')
    return os.environ.get('API_KEY')


def _get_rate_limit() -> tuple[int, float]:
    n = app.config.get('RATE_LIMIT_N')
    w = app.config.get('RATE_LIMIT_WINDOW_SEC')
    if n is None:
        n = int(os.environ.get('RATE_LIMIT_N', '5'))
    if w is None:
        w = float(os.environ.get('RATE_LIMIT_WINDOW_SEC', '1.0'))
    return int(n), float(w)

_recent: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=100))

# Optional WebSocket support
if Sock is not None:
    sock = Sock(app)
else:
    sock = None
def _client_ip() -> str:
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        return xff.split(',')[0].strip()
    return request.remote_addr or 'anon'


def _check_api_key():
    api_key = _get_api_key()
    if api_key:
        provided = request.headers.get('X-API-Key')
        if provided != api_key:
            return jsonify({'error': 'unauthorized'}), 401
    return None


def _check_rate_limit(ip: str):
    # Allow if rate limiting disabled or N <= 0
    n, window = _get_rate_limit()
    if n <= 0:
        return None
    now = time.time()
    dq = _recent[ip]
    # Drop old entries outside window
    while dq and now - dq[0] > window:
        dq.popleft()
    if len(dq) >= n:
        retry = max(0.0, window - (now - dq[0]))
        resp = jsonify({'error': 'rate_limited'})
        resp.status_code = 429
        resp.headers['Retry-After'] = f"{retry:.2f}"
        return resp
    dq.append(now)
    return None

@app.before_request
def _auth_and_rate_limit():
    # Only enforce for API routes under /runs; skip static or root
    if request.path.startswith('/runs'):
        # Auth
        unauthorized = _check_api_key()
        if unauthorized is not None:
            return unauthorized
        # Rate limit only for POST /runs
        if request.method == 'POST' and request.path == '/runs':
            rl = _check_rate_limit(_client_ip())
            if rl is not None:
                return rl
    return None

@app.post('/runs')
def post_runs():
    payload = request.get_json(force=True, silent=True) or {}
    name = payload.get('company_name') or ''
    if not name:
        return jsonify({'error': 'company_name is required'}), 400
    rid = start_run(name)
    return jsonify({'run_id': rid, 'status': 'queued'})

@app.get('/runs/<rid>')
def get_run(rid: str):
    r = REGISTRY.get(rid)
    if not r:
        return jsonify({'error': 'not_found'}), 404
    return jsonify({
        'run_id': r.id,
        'status': r.status,
        'summary': r.summary,
        'artifacts': list(r.artifacts.keys()),
        'events': r.events,
        'error': r.error,
    })
@app.get('/runs/<rid>/artifacts/<name>')
def get_artifact(rid: str, name: str):
    r = REGISTRY.get(rid)
    if not r:
        return jsonify({'error': 'not_found'}), 404
    body = r.artifacts.get(name)
    if body is None:
        return jsonify({'error': 'artifact_not_found'}), 404
    # Basic content-type inference for MVP
    if name.endswith('.csv'):
        mimetype = 'text/csv'
    elif name.endswith('.md'):
        mimetype = 'text/markdown'
    else:
        mimetype = 'application/octet-stream'
    return Response(body, mimetype=mimetype)
# Optional: OpenAPI spec route (serves static JSON file)
@app.get('/openapi.json')
def get_openapi():
    try:
        with open('services/api/openapi.json', 'r') as f:
            spec = json.load(f)
        return jsonify(spec)
    except Exception:
        return jsonify({'error': 'openapi_not_found'}), 404

# Optional: WebSocket for events stream (if flask-sock installed)
if sock is not None:
    @sock.route('/runs/<rid>/events')
    def ws_events(ws, rid):  # pragma: no cover (basic smoke only)
        r = REGISTRY.get(rid)
        if not r:
            ws.close()
            return
        last_idx = 0
        # Stream existing then poll for new events for a short time
        start = time.time()
        while ws.connected and time.time() - start < 10:
            evs = r.events
            if last_idx < len(evs):
                for ev in evs[last_idx:]:
                    ws.send(json.dumps(ev))
                last_idx = len(evs)
            time.sleep(0.05)

@app.get('/runs')
def list_runs():
    # List persisted runs from disk; ignore in-memory registry
    try:
        runs = []
        if ARTIFACTS_ROOT.exists():
            for p in sorted(ARTIFACTS_ROOT.iterdir()):
                if p.is_dir() and (p / 'run.json').exists():
                    try:
                        meta = json.loads((p / 'run.json').read_text())
                        runs.append({
                            'run_id': meta.get('run_id') or p.name,
                            'status': meta.get('status'),
                            'summary': meta.get('summary'),
                            'artifacts': meta.get('artifacts', []),
                            'completed_at': meta.get('completed_at'),
                        })
                    except Exception:
                        continue
        return jsonify({'runs': runs})
    except Exception:
        return jsonify({'runs': []})

@app.get('/runs/<rid>/download.zip')
def download_zip(rid: str):
    # Create a zip of all artifacts for a run
    run_dir = ARTIFACTS_ROOT / rid
    if not run_dir.exists():
        return jsonify({'error': 'not_found'}), 404
    # Build zip in memory
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for child in run_dir.iterdir():
            if child.is_file() and child.name != 'run.json':
                zf.writestr(child.name, child.read_bytes())
    mem.seek(0)
    return Response(mem.getvalue(), mimetype='application/zip', headers={
        'Content-Disposition': f'attachment; filename="{rid}.zip"'
    })




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

