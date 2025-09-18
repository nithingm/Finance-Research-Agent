from __future__ import annotations
from typing import Any
from flask import Flask, request, jsonify
from services.api.orchestrator import REGISTRY, start_run

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

