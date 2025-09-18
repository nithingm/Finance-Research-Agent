import unittest
import importlib
import services.api.server as server
from services.api.server import app

class TestAPIExtras(unittest.TestCase):
    def setUp(self):
        app.testing = True
        # Clear API key and rate limiter state to avoid cross-test leakage
        app.config['API_KEY'] = None
        try:
            server._recent.clear()
        except Exception:
            pass
        self.client = app.test_client()

    def test_openapi_endpoint(self):
        rv = self.client.get('/openapi.json')
        self.assertEqual(rv.status_code, 200)
        spec = rv.get_json()
        self.assertIn('openapi', spec)
        self.assertIn('/runs', spec.get('paths', {}))

    def test_rate_limit_post_runs(self):
        # Ensure no auth for this test
        app.config['API_KEY'] = None
        # Override rate limit to a very small number for test
        app.config['RATE_LIMIT_N'] = 1
        app.config['RATE_LIMIT_WINDOW_SEC'] = 1.0
        # First request should pass (but may 400 if missing company_name)
        rv1 = self.client.post('/runs', json={'company_name': 'A'})
        self.assertIn(rv1.status_code, (200, 400))
        # Second immediate request should be 429
        rv2 = self.client.post('/runs', json={'company_name': 'B'})
        self.assertEqual(rv2.status_code, 429)
        data = rv2.get_json()
        self.assertEqual(data.get('error'), 'rate_limited')

    def test_auth_api_key(self):
        # Enable API key requirement
        app.config['API_KEY'] = 'secret'
        # Missing key -> 401
        rv = self.client.get('/runs/not-exist')
        self.assertEqual(rv.status_code, 401)
        # With key -> proceeds to 404 for missing run
        rv2 = self.client.get('/runs/not-exist', headers={'X-API-Key': 'secret'})
        self.assertEqual(rv2.status_code, 404)

if __name__ == '__main__':
    unittest.main()

