import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "analytics"))

from cashflow_kpis import (
    capital_allocation_pattern,
    capex_intensity,
    cfo_quality_label,
    cfo_quality_ratio,
    fcf_conversion_rate,
    free_cash_flow,
    sign,
)


class CashFlowKpiTests(unittest.TestCase):
    def test_free_cash_flow_allows_negative(self):
        self.assertEqual(free_cash_flow(100, -150), -50)

    def test_cfo_quality_pat_zero_none(self):
        self.assertIsNone(cfo_quality_ratio(100, 0))

    def test_cfo_quality_high_label(self):
        self.assertEqual(cfo_quality_label(1.2), "High Quality")

    def test_cfo_quality_moderate_label(self):
        self.assertEqual(cfo_quality_label(0.8), "Moderate")

    def test_cfo_quality_accrual_risk_label(self):
        self.assertEqual(cfo_quality_label(0.3), "Accrual Risk")

    def test_capex_intensity_asset_light(self):
        value, label = capex_intensity(-2, 100)
        self.assertEqual(value, 2)
        self.assertEqual(label, "Asset Light")

    def test_capex_intensity_capital_intensive(self):
        _, label = capex_intensity(-20, 100)
        self.assertEqual(label, "Capital Intensive")

    def test_fcf_conversion_zero_op_none(self):
        self.assertIsNone(fcf_conversion_rate(10, 0))

    def test_sign_zero(self):
        self.assertEqual(sign(0), "0")

    def test_capital_allocation_shareholder_returns(self):
        self.assertEqual(capital_allocation_pattern(100, -50, -25, 1.2), "Shareholder Returns")

    def test_capital_allocation_growth_funded_by_debt(self):
        self.assertEqual(capital_allocation_pattern(-100, -50, 25), "Growth Funded by Debt")

    def test_capital_allocation_distress_signal(self):
        self.assertEqual(capital_allocation_pattern(-100, 50, 25), "Distress Signal")


if __name__ == "__main__":
    unittest.main()
