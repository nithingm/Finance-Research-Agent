import unittest
from services.ingestion.fx_client import build_fx_latest_url, parse_fx_latest

class TestFX(unittest.TestCase):
    def test_build_url(self):
        url = build_fx_latest_url(base="USD", symbols="INR,EUR")
        self.assertIn("/latest?base=USD&symbols=INR,EUR", url)

    def test_parse(self):
        payload = {"base": "USD", "date": "2024-01-02", "rates": {"INR": 83.0, "EUR": 0.91}}
        q = parse_fx_latest(payload, "INR")
        self.assertIsNotNone(q)
        self.assertEqual(q.base, "USD")
        self.assertEqual(q.quote, "INR")
        self.assertAlmostEqual(q.rate, 83.0)

if __name__ == "__main__":
    unittest.main()

