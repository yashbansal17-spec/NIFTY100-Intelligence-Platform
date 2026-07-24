import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "etl"))

from normaliser import normalize_ticker, normalize_year, snake_case


class NormaliserTests(unittest.TestCase):
    def test_snake_case_lowercases(self):
        self.assertEqual(snake_case("Company Name"), "company_name")

    def test_snake_case_replaces_percentage(self):
        self.assertEqual(snake_case("ROCE %"), "roce_percentage")

    def test_snake_case_removes_punctuation(self):
        self.assertEqual(snake_case("Profit & Loss"), "profit_loss")

    def test_ticker_uppercase(self):
        self.assertEqual(normalize_ticker(" hdfcbank "), "HDFCBANK")

    def test_ticker_removes_exchange_prefix(self):
        self.assertEqual(normalize_ticker("NSE:TCS"), "TCS")

    def test_ticker_handles_empty(self):
        self.assertIsNone(normalize_ticker(""))

    def test_year_four_digit(self):
        self.assertEqual(normalize_year("Dec 2012"), 2012)

    def test_year_two_digit(self):
        self.assertEqual(normalize_year("Mar-13"), 2013)

    def test_year_older_two_digit(self):
        self.assertEqual(normalize_year("Mar-99"), 1999)

    def test_year_none(self):
        self.assertIsNone(normalize_year(None))


if __name__ == "__main__":
    unittest.main()


YEAR_CASES = [
    ("Dec 2012", 2012),
    ("Mar-13", 2013),
    ("Mar 2014", 2014),
    ("FY 2024", 2024),
    ("2020", 2020),
    ("Mar-99", 1999),
    ("Dec-05", 2005),
    ("2018-19", 2018),
    ("Year 2021", 2021),
    ("Sep 2007", 2007),
    ("Jun-38", 2038),
    ("Jun-40", 1940),
    ("TTM", None),
    ("", None),
    (None, None),
    ("No year", None),
    ("Mar 2000", 2000),
    ("Dec-01", 2001),
    ("FY1998", 1998),
    ("Calendar 2026", 2026),
]

TICKER_CASES = [
    (" hdfcbank ", "HDFCBANK"),
    ("NSE:TCS", "TCS"),
    ("BSE-INFY", "INFY"),
    (" reliance ", "RELIANCE"),
    ("NSE : itc", "ITC"),
    ("BSE: sbin", "SBIN"),
    ("adaniports", "ADANIPORTS"),
    ("BAJAJ FINSV", "BAJAJFINSV"),
    ("", None),
    (None, None),
    ("  ", None),
    ("nse-wipro", "WIPRO"),
    ("BSE : LT", "LT"),
    ("HDFC BANK", "HDFCBANK"),
    ("NSE:ULTRACEMCO", "ULTRACEMCO"),
]


def _make_year_test(raw, expected):
    def test(self):
        self.assertEqual(normalize_year(raw), expected)
    return test


def _make_ticker_test(raw, expected):
    def test(self):
        self.assertEqual(normalize_ticker(raw), expected)
    return test


for idx, (raw, expected) in enumerate(YEAR_CASES, start=1):
    setattr(NormaliserTests, f"test_normalize_year_case_{idx:02d}", _make_year_test(raw, expected))

for idx, (raw, expected) in enumerate(TICKER_CASES, start=1):
    setattr(NormaliserTests, f"test_normalize_ticker_case_{idx:02d}", _make_ticker_test(raw, expected))
