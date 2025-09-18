import os
import time
import json
import shutil
import unittest
from pathlib import Path
import services.api.server as server
from services.api.orchestrator import ARTIFACTS_ROOT
from services.api.server import app

class TestRunsPersistence(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()
        # Clean artifacts dir before each test
        if ARTIFACTS_ROOT.exists():
            shutil.rmtree(ARTIFACTS_ROOT)
        ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)
        # Disable auth and rate-limit for these tests
        app.config['API_KEY'] = None
        app.config['RATE_LIMIT_N'] = 0
        try:
            server._recent.clear()
        except Exception:
            pass

    def _wait_done(self, rid: str, timeout=5.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            rv = self.client.get(f"/runs/{rid}")
            if rv.status_code == 200:
                b = rv.get_json()
                if b.get('status') in ('completed', 'failed'):
                    return b
            time.sleep(0.05)
        return {}

    def test_artifacts_written_to_disk_and_list_runs(self):
        rv = self.client.post('/runs', json={'company_name': 'Apple'})
        self.assertEqual(rv.status_code, 200)
        rid = rv.get_json()['run_id']
        final = self._wait_done(rid)
        self.assertIn(final.get('status'), ('completed', 'failed'))
        run_dir = ARTIFACTS_ROOT / rid
        self.assertTrue((run_dir / 'run.json').exists())
        # Basic expected artifacts
        for name in ('dcf.csv','income_statement.csv','metadata.csv','assumptions.md','validation_report.md'):
            self.assertTrue((run_dir / name).exists(), f"missing {name}")
        # List runs endpoint
        rv_list = self.client.get('/runs')
        self.assertEqual(rv_list.status_code, 200)
        runs = rv_list.get_json().get('runs', [])
        self.assertTrue(any(r.get('run_id') == rid for r in runs))
        # Zip download
        rv_zip = self.client.get(f"/runs/{rid}/download.zip")
        self.assertEqual(rv_zip.status_code, 200)
        self.assertEqual(rv_zip.mimetype, 'application/zip')

if __name__ == '__main__':
    unittest.main()

