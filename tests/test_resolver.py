import unittest
from services.resolver.core import resolve, Entity

class TestResolver(unittest.TestCase):
    def test_exact_alias(self):
        cands = resolve("Google")
        self.assertGreaterEqual(len(cands), 1)
        self.assertEqual(cands[0].entity.ticker, "GOOGL")
        self.assertIn(cands[0].reason, ("alias", "lev:0", "exact_name"))

    def test_typo(self):
        cands = resolve("Gooogle")
        self.assertTrue(any(c.entity.ticker == "GOOGL" for c in cands))

    def test_exact_name(self):
        cands = resolve("Apple Inc.")
        self.assertEqual(cands[0].entity.ticker, "AAPL")

    def test_empty(self):
        self.assertEqual(resolve(""), [])

if __name__ == "__main__":
    unittest.main()

