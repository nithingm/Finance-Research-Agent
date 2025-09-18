import unittest
from services.exports.writers import write_income_statement, write_dcf, write_metadata, SCHEMAS
from services.exports.reports import assumptions_md, validation_report_md
import csv
import io

class TestExports(unittest.TestCase):
    def test_income_statement_csv(self):
        rows = [{
            "company_id":"AAPL","basis":"US-GAAP","currency":"USD","period_end":"2024-03-31","period_type":"Q",
            "revenue":1000,"cogs":400,"gross_profit":600,"rnd":50,"sma":100,"gna":60,"da":30,"ebit":200,
            "interest_net":-5,"pretax":195,"tax":40,"net_income":155,"nci":0
        }]
        csv_text = write_income_statement(rows)
        reader = csv.DictReader(io.StringIO(csv_text))
        recs = list(reader)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["company_id"], "AAPL")
        self.assertEqual(set(reader.fieldnames), set(SCHEMAS["income_statement"]))

    def test_dcf_csv(self):
        rows = [{
            "period_end":"2025-03-31","ebit":200,"tax_rate":0.25,"nopat":150,"da":30,"capex":50,
            "delta_nwc":10,"fcf":120,"discount_factor":0.95,"pv_fcf":114,
            "terminal_value":1000,"pv_terminal":900,"ev":1200,"net_cash":200,"equity_value":1400,
            "shares":1000,"value_per_share":1.4
        }]
        txt = write_dcf(rows)
        self.assertIn("period_end,ebit,tax_rate", txt.splitlines()[0])

    def test_metadata_csv(self):
        txt = write_metadata([{"run_id":"r1","company_key":"AAPL/NASDAQ","basis":"US-GAAP","currency":"USD","fiscal_year_end":"09-30","generated_at":"2025-01-01T00:00:00Z","mapper_version":"0.1","taxonomy_version":"2024.0","code_sha":"abc123"}])
        self.assertTrue(txt.startswith("run_id,company_key"))

    def test_reports_md(self):
        a = assumptions_md({"revenue_growth_qoq":0.02,"target_gross_margin":0.6}, warnings=["mapping coverage < 95%"])
        self.assertIn("# Assumptions", a)
        v = validation_report_md({"balance_sheet_balances": True, "cash_flow_identity": True}, details={"periods_checked": 10})
        self.assertIn("# Validation Report", v)

if __name__ == '__main__':
    unittest.main()

