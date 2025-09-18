import unittest
import time
from typing import List

from services.api.server import app


class TestAPIRuns(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def _wait_for_completion(self, rid: str, timeout_s: float = 5.0) -> dict:
        deadline = time.time() + timeout_s
        last = None
        while time.time() < deadline:
            rv = self.client.get(f"/runs/{rid}")
            if rv.status_code != 200:
                time.sleep(0.05)
                continue
            last = rv.get_json()
            if last and last.get("status") in ("completed", "failed"):
                return last
            time.sleep(0.05)
        return last or {}

    def test_post_runs_requires_company_name(self):
        rv = self.client.post("/runs", json={})
        self.assertEqual(rv.status_code, 400)
        body = rv.get_json()
        self.assertEqual(body.get("error"), "company_name is required")

    def test_post_and_get_run_contract_and_events(self):
        # Create run
        rv = self.client.post("/runs", json={"company_name": "Apple"})
        self.assertEqual(rv.status_code, 200)
        body = rv.get_json()
        self.assertIn("run_id", body)
        self.assertEqual(body.get("status"), "queued")
        rid = body["run_id"]

        # Poll until finished
        final = self._wait_for_completion(rid)
        self.assertIsNotNone(final)
        self.assertIn(final.get("status"), ("completed", "failed"))
        self.assertEqual(final.get("run_id"), rid)
        self.assertIn("events", final)
        self.assertIsInstance(final["events"], list)
        self.assertIn("artifacts", final)
        self.assertIsInstance(final["artifacts"], list)

        # Verify event stage ordering (prefix order)
        stages = [e.get("stage") for e in final["events"]]
        expected_prefix: List[str] = [
            "Resolve",
            "Ingest",
            "Map",
            "Forecast",
            "DCF",
            "Export",
        ]
        # The run either completes (then 'Done' exists) or fails (then 'Error' exists)
        # Validate that expected_prefix appears in order within stages
        it = iter(stages)
        for s in expected_prefix:
            for t in it:
                if t == s:
                    break
            else:
                self.fail(f"Did not find stage '{s}' in order. Stages: {stages}")
        # End stage check
        self.assertTrue(stages[-1] in ("Done", "Error"))

        # Basic artifact presence
        arts = set(final["artifacts"])  # list of names
        for name in ("dcf.csv", "income_statement.csv", "metadata.csv", "assumptions.md", "validation_report.md"):
            self.assertIn(name, arts)

        # Artifact download endpoint (csv)
        rv_art = self.client.get(f"/runs/{rid}/artifacts/dcf.csv")
        self.assertEqual(rv_art.status_code, 200)
        self.assertIn(rv_art.mimetype, ("text/csv", "text/plain"))
        self.assertIn("period_end,ebit,tax_rate", rv_art.get_data(as_text=True).splitlines()[0])

    def test_404s(self):
        rv = self.client.get("/runs/does-not-exist")
        self.assertEqual(rv.status_code, 404)
        rv2 = self.client.get("/runs/does-not-exist/artifacts/dcf.csv")
        self.assertEqual(rv2.status_code, 404)

        # Create a run and wait; then request a missing artifact
        rv3 = self.client.post("/runs", json={"company_name": "Foo"})
        rid = rv3.get_json()["run_id"]
        self._wait_for_completion(rid)
        rv_missing = self.client.get(f"/runs/{rid}/artifacts/missing.txt")
        self.assertEqual(rv_missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()

