import unittest
from services.forecasting.assumptions import Scenario, validate_scenario
from services.forecasting.engine import project_12q

class TestForecasting(unittest.TestCase):
    def test_validate_scenario(self):
        s = Scenario(
            revenue_growth_qoq=0.02,
            target_gross_margin=0.6,
            target_operating_margin=0.2,
            dso=45, dio=60, dpo=50,
            capex_pct_revenue=0.05,
            da_pct_revenue=0.03,
            tax_rate=0.25,
        )
        validate_scenario(s)  # should not raise

    def test_project_12q_shapes_and_identities(self):
        s = Scenario(
            revenue_growth_qoq=0.02,
            target_gross_margin=0.6,
            target_operating_margin=0.2,
            dso=45, dio=60, dpo=50,
            capex_pct_revenue=0.05,
            da_pct_revenue=0.03,
            tax_rate=0.25,
        )
        hist = {"revenue": 1000, "ar": 100, "inventory": 80, "ap": 70}
        rows = project_12q(hist, s)
        self.assertEqual(len(rows), 12)
        # Basic fields present
        for r in rows:
            for k in ["revenue", "cogs", "gross_profit", "ebit", "tax", "net_income", "da", "capex", "ar", "inventory", "ap", "delta_nwc", "cfo", "cfi", "cff", "delta_cash"]:
                self.assertIn(k, r)
            # Identity CFO + CFI + CFF == delta_cash
            self.assertAlmostEqual(r["cfo"] + r["cfi"] + r["cff"], r["delta_cash"], places=6)

if __name__ == '__main__':
    unittest.main()

