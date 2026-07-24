import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "analytics"))

from cagr import BOTH_NEGATIVE, DECLINE_TO_LOSS, INSUFFICIENT, OK, TURNAROUND, ZERO_BASE, cagr, cagr_for_window


class CagrFormulaTests(unittest.TestCase):
    def test_cagr_normal(self):
        value, flag = cagr(100, 121, 2)
        self.assertAlmostEqual(value, 10)
        self.assertEqual(flag, OK)

    def test_cagr_turnaround_flag(self):
        value, flag = cagr(-100, 120, 5)
        self.assertIsNone(value)
        self.assertEqual(flag, TURNAROUND)

    def test_cagr_decline_to_loss_flag(self):
        value, flag = cagr(100, -20, 5)
        self.assertIsNone(value)
        self.assertEqual(flag, DECLINE_TO_LOSS)

    def test_cagr_both_negative_flag(self):
        value, flag = cagr(-100, -20, 5)
        self.assertIsNone(value)
        self.assertEqual(flag, BOTH_NEGATIVE)

    def test_cagr_zero_base_flag(self):
        value, flag = cagr(0, 20, 5)
        self.assertIsNone(value)
        self.assertEqual(flag, ZERO_BASE)

    def test_cagr_insufficient_years_flag(self):
        value, flag = cagr_for_window({2024: 120}, 2024, 5)
        self.assertIsNone(value)
        self.assertEqual(flag, INSUFFICIENT)


if __name__ == "__main__":
    unittest.main()
