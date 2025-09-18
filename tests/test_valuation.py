import unittest
from services.valuation.fcff import FCFFInputs, fcff
from services.valuation.wacc import WACCInputs, wacc
from services.valuation.terminal import TerminalInputs, gordon_pv
from services.valuation.discount import discount_factors, present_value

class TestValuation(unittest.TestCase):
    def test_fcff(self):
        i = FCFFInputs(ebit=200, tax_rate=0.25, da=50, capex=80, delta_nwc=10)
        self.assertAlmostEqual(fcff(i), 200*(1-0.25)+50-80-10)

    def test_wacc(self):
        i = WACCInputs(rf=0.03, erp=0.05, beta=1.2, tax_rate=0.21, debt_ratio=0.3, equity_ratio=0.7, rd=0.05)
        val = wacc(i)
        # simple bounds check
        self.assertTrue(0.03 < val < 0.12)

    def test_terminal(self):
        t = TerminalInputs(last_fcf=100, wacc=0.10, g=0.03)
        self.assertAlmostEqual(gordon_pv(t), 100/(0.10-0.03))
        with self.assertRaises(ValueError):
            gordon_pv(TerminalInputs(last_fcf=100, wacc=0.03, g=0.05))

    def test_discounting(self):
        dfs = discount_factors(0.1, 3)
        self.assertAlmostEqual(len(dfs), 3)
        pv = present_value([100, 100, 100], 0.1)
        self.assertAlmostEqual(pv, sum([100/1.1, 100/(1.1**2), 100/(1.1**3)]))

if __name__ == '__main__':
    unittest.main()

