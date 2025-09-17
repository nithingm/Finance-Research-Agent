import unittest
import json
from services.mapper.engine import Mapper
from pathlib import Path

GAAP_PATH = Path('services/mapper/mapping_gaap.json')
IFRS_PATH = Path('services/mapper/mapping_ifrs.json')

class TestMapper(unittest.TestCase):
    def setUp(self):
        self.gaap = Mapper.from_json_path(GAAP_PATH)
        self.ifrs = Mapper.from_json_path(IFRS_PATH)

    def test_gaap_basic_mapping(self):
        facts = {
            'RevenueFromContractWithCustomerExcludingAssessedTax': 1000,
            'CostOfRevenue': 400,
            'ResearchAndDevelopmentExpense': 50,
            'SellingGeneralAndAdministrativeExpense': 100,
        }
        out = self.gaap.map_period(facts, unit='USD')
        self.assertAlmostEqual(out['revenue'], 1000)
        self.assertAlmostEqual(out['cogs'], 400)
        self.assertAlmostEqual(out['gross_profit'], 600)
        self.assertAlmostEqual(out['sma'], 100)
        self.assertAlmostEqual(out['rnd'], 50)

    def test_gaap_alias(self):
        facts = {'SalesRevenueNet': 900, 'CostOfRevenue': 300}
        out = self.gaap.map_period(facts, unit='USD')
        self.assertAlmostEqual(out['revenue'], 900)
        self.assertAlmostEqual(out['gross_profit'], 600)

    def test_ifrs_stub(self):
        facts = {'Revenue': 800, 'CostOfSales': 200}
        out = self.ifrs.map_period(facts, unit='EUR')
        self.assertAlmostEqual(out['revenue'], 800)
        self.assertAlmostEqual(out['cogs'], 200)
        self.assertAlmostEqual(out['gross_profit'], 600)

if __name__ == '__main__':
    unittest.main()

