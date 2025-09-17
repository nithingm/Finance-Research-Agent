import unittest
from services.historical.timeseries import stitch_periods, validate_accounting_identities
from services.historical.kpi import enrich_with_kpis


class TestHistorical(unittest.TestCase):
    def test_stitch_and_sort(self):
        annual = [
            {"period_end": "2023-12-31", "period_type": "A", "revenue": 1000},
            {"period_end": "2022-12-31", "period_type": "A", "revenue": 900},
        ]
        quarterly = [
            {"period_end": "2023-09-30", "period_type": "Q", "revenue": 250},
            {"period_end": "2023-06-30", "period_type": "Q", "revenue": 240},
            {"period_end": "2023-09-30", "period_type": "Q", "revenue": 250},  # duplicate
        ]
        rows = stitch_periods(annual, quarterly)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["period_end"], "2022-12-31")
        self.assertEqual(rows[-1]["period_end"], "2023-12-31")

    def test_kpis(self):
        rows = [
            {"period_end": "2023-12-31", "period_type": "A", "revenue": 1000, "gross_profit": 600, "ebit": 200, "cogs": 400, "ar": 100, "inventory": 80, "ap": 70, "capex": 50}
        ]
        out = enrich_with_kpis(rows)
        self.assertAlmostEqual(out[0]["gross_margin"], 0.6)
        self.assertAlmostEqual(out[0]["operating_margin"], 0.2)
        self.assertIn("dso", out[0])
        self.assertIn("dio", out[0])
        self.assertIn("dpo", out[0])
        self.assertAlmostEqual(out[0]["capex_pct_revenue"], 0.05)

    def test_cashflow_identity(self):
        rows = [
            {"period_end": "2023-06-30", "period_type": "Q", "cash": 100},
            {"period_end": "2023-09-30", "period_type": "Q", "cash": 120, "cfo": 30, "cfi": -5, "cff": -5},
            {"period_end": "2023-12-31", "period_type": "Q", "cash": 135, "cfo": 10, "cfi": 10, "cff": -5},
        ]
        self.assertTrue(validate_accounting_identities(rows))


if __name__ == "__main__":
    unittest.main()

