import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "analytics"))

from ratios import (
    asset_turnover,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage,
    net_debt,
    net_profit_margin,
    operating_profit_margin,
    return_on_assets,
    return_on_capital_employed,
    return_on_equity,
)


class RatioFormulaTests(unittest.TestCase):
    def test_net_profit_margin_normal(self):
        self.assertEqual(net_profit_margin(25, 100), 25)

    def test_net_profit_margin_zero_sales(self):
        self.assertIsNone(net_profit_margin(25, 0))

    def test_operating_profit_margin_mismatch(self):
        value, mismatch = operating_profit_margin(30, 100, 20)
        self.assertEqual(value, 30)
        self.assertTrue(mismatch)

    def test_roe_negative_equity_returns_none(self):
        self.assertIsNone(return_on_equity(10, 5, -10))

    def test_roce_normal(self):
        value, mode = return_on_capital_employed(20, 5, 10, 50, 40, "Industrials")
        self.assertAlmostEqual(value, 25)
        self.assertEqual(mode, "absolute")

    def test_roce_financials_mode(self):
        _, mode = return_on_capital_employed(20, 5, 10, 50, 40, "Financials")
        self.assertEqual(mode, "financials_sector_relative")

    def test_roa_zero_assets(self):
        self.assertIsNone(return_on_assets(10, 0))

    def test_debt_to_equity_debt_free_returns_zero(self):
        self.assertEqual(debt_to_equity(0, 10, 90), 0)

    def test_debt_to_equity_negative_equity_none(self):
        self.assertIsNone(debt_to_equity(50, 10, -20))

    def test_high_leverage_non_financial(self):
        self.assertTrue(high_leverage_flag(6, "Industrials"))

    def test_high_leverage_financial_suppressed(self):
        self.assertFalse(high_leverage_flag(6, "Financials"))

    def test_interest_coverage_debt_free_label(self):
        value, label, warning = interest_coverage(100, 10, 0)
        self.assertIsNone(value)
        self.assertEqual(label, "Debt Free")
        self.assertFalse(warning)

    def test_interest_coverage_warning(self):
        value, _, warning = interest_coverage(100, 0, 100)
        self.assertEqual(value, 1)
        self.assertTrue(warning)

    def test_net_debt(self):
        self.assertEqual(net_debt(100, 25), 75)

    def test_asset_turnover_zero_assets(self):
        self.assertIsNone(asset_turnover(100, 0))


if __name__ == "__main__":
    unittest.main()
