import unittest
import json
from services.ingestion.sec_client import (
    normalize_cik, build_company_facts_url, build_frames_url, extract_facts_companyfacts
)
from services.ingestion.market_client import build_stooq_daily_csv, parse_alpha_vantage_daily


class TestSECClient(unittest.TestCase):
    def test_normalize_cik(self):
        self.assertEqual(normalize_cik("320193"), "CIK0000320193")
        self.assertEqual(normalize_cik("CIK0000320193"), "CIK0000320193")
        self.assertEqual(normalize_cik(1652044), "CIK0001652044")

    def test_build_company_facts_url(self):
        url = build_company_facts_url("320193")
        self.assertIn("/xbrl/companyfacts/CIK0000320193.json", url)

    def test_build_frames_url(self):
        url = build_frames_url("US-GAAP", "Revenues", "USD", "FY2023")
        self.assertTrue(url.endswith("/xbrl/frames/US-GAAP/Revenues/USD/FY2023"))

    def test_extract_facts_companyfacts(self):
        payload = {
            "facts": {
                "US-GAAP": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {"end": "2023-12-31", "val": 100.0, "accn": "000-1", "fp": "FY"},
                                {"end": "2022-12-31", "val": 90.0, "accn": "000-2", "fp": "FY"},
                                {"end": "2023-09-30", "val": 75.5, "accn": "000-3", "fp": "Q3"},
                                {"end": "2023-06-30", "val": "NaN"},
                            ]
                        }
                    }
                }
            }
        }
        facts = extract_facts_companyfacts(payload, "US-GAAP", "Revenues", "USD")
        self.assertGreaterEqual(len(facts), 3)
        self.assertEqual(facts[0].end, "2023-12-31")
        self.assertAlmostEqual(facts[0].val, 100.0)


class TestMarketClient(unittest.TestCase):
    def test_build_stooq_url(self):
        self.assertIn("AAPL.US", build_stooq_daily_csv("AAPL", exchange_hint="NASDAQ"))
        self.assertIn("MSFT", build_stooq_daily_csv("MSFT"))

    def test_parse_alpha_vantage(self):
        payload = {
            "Time Series (Daily)": {
                "2024-01-02": {"1. open": "100.0", "4. close": "105.0"},
                "2024-01-03": {"1. open": "105.0", "4. close": "103.5"},
            }
        }
        out = parse_alpha_vantage_daily(payload, "AAPL")
        self.assertIn("2024-01-02", out)
        self.assertAlmostEqual(out["2024-01-02"].close, 105.0)


if __name__ == "__main__":
    unittest.main()

