import csv
import sqlite3
import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "etl"))

from loader import initialise_schema, split_known_companies
from normaliser import LOAD_ORDER
from validator import DQ_RULES, scalar_count


class SchemaAndValidatorTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON")
        initialise_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_schema_creates_companies(self):
        self.assertIn(("companies",), self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'").fetchall())

    def test_schema_creates_stock_prices(self):
        self.assertIn(("stock_prices",), self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_prices'").fetchall())

    def test_schema_has_twelve_tables(self):
        count = self.conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        self.assertEqual(count, 12)

    def test_foreign_keys_enabled(self):
        self.assertEqual(self.conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_company_pk_blocks_duplicate(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")

    def test_profitandloss_fk_blocks_unknown_company(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO profitandloss(id, company_id, year, fiscal_year) VALUES(1, 'NOPE', 'Mar 2024', 2024)")

    def test_profitandloss_allows_repeated_company_year_from_source(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO profitandloss(id, company_id, year, fiscal_year) VALUES(1, 'AAA', 'Mar 2024', 2024)")
        self.conn.execute("INSERT INTO profitandloss(id, company_id, year, fiscal_year) VALUES(2, 'AAA', 'Mar 2024', 2024)")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM profitandloss").fetchone()[0], 2)

    def test_sector_unique_company(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO sectors(id, company_id, broad_sector) VALUES(1, 'AAA', 'Tech')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO sectors(id, company_id, broad_sector) VALUES(2, 'AAA', 'Tech')")

    def test_stock_price_unique_company_date(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO stock_prices(id, company_id, date) VALUES(1, 'AAA', '2024-01-01')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO stock_prices(id, company_id, date) VALUES(2, 'AAA', '2024-01-01')")

    def test_peer_group_boolean_check(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO peer_groups(id, peer_group_name, company_id, is_benchmark) VALUES(1, 'G', 'AAA', 2)")

    def test_dq_rule_count(self):
        self.assertEqual(len(DQ_RULES), 16)

    def test_scalar_count_for_select(self):
        self.assertEqual(scalar_count(self.conn, "SELECT COUNT(*) FROM companies"), 0)

    def test_scalar_count_for_pragma(self):
        self.assertEqual(scalar_count(self.conn, "PRAGMA foreign_key_check"), 0)

    def test_can_insert_minimal_company(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0], 1)

    def test_balance_sheet_warning_query_finds_mismatch(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO balancesheet(id, company_id, year, fiscal_year, total_assets, total_liabilities) VALUES(1, 'AAA', 'Mar 2024', 2024, 100, 80)")
        sql = [rule[-1] for rule in DQ_RULES if rule[0] == "DQ-04"][0]
        self.assertEqual(scalar_count(self.conn, sql), 1)

    def test_stock_high_low_rule_finds_error(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO stock_prices(id, company_id, date, high_price, low_price) VALUES(1, 'AAA', '2024-01-01', 10, 20)")
        sql = [rule[-1] for rule in DQ_RULES if rule[0] == "DQ-12"][0]
        self.assertEqual(scalar_count(self.conn, sql), 1)

    def test_documents_url_rule_finds_error(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO documents(id, company_id, year, annual_report) VALUES(1, 'AAA', 2024, 'not-a-url')")
        sql = [rule[-1] for rule in DQ_RULES if rule[0] == "DQ-08"][0]
        self.assertEqual(scalar_count(self.conn, sql), 1)

    def test_audit_csv_shape(self):
        path = PROJECT_ROOT / "work" / "test_audit.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["table", "loaded_rows"])
            writer.writeheader()
            writer.writerow({"table": "companies", "loaded_rows": 92})
        with path.open(encoding="utf-8") as handle:
            self.assertEqual(list(csv.DictReader(handle))[0]["table"], "companies")

    def test_index_exists_for_stock_prices(self):
        indexes = [row[1] for row in self.conn.execute("PRAGMA index_list(stock_prices)").fetchall()]
        self.assertIn("idx_prices_company_date", indexes)

    def test_index_exists_for_profitandloss(self):
        indexes = [row[1] for row in self.conn.execute("PRAGMA index_list(profitandloss)").fetchall()]
        self.assertIn("idx_pl_company_year", indexes)

    def test_index_exists_for_market_cap(self):
        indexes = [row[1] for row in self.conn.execute("PRAGMA index_list(market_cap)").fetchall()]
        self.assertIn("idx_market_cap_company_year", indexes)

    def test_cashflow_allows_repeated_company_year_from_source(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO cashflow(id, company_id, year, fiscal_year) VALUES(1, 'AAA', 'Mar 2024', 2024)")
        self.conn.execute("INSERT INTO cashflow(id, company_id, year, fiscal_year) VALUES(2, 'AAA', 'Mar 2024', 2024)")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM cashflow").fetchone()[0], 2)

    def test_financial_ratios_allows_repeated_company_year_from_source(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO financial_ratios(id, company_id, year, fiscal_year) VALUES(1, 'AAA', 'Mar 2024', 2024)")
        self.conn.execute("INSERT INTO financial_ratios(id, company_id, year, fiscal_year) VALUES(2, 'AAA', 'Mar 2024', 2024)")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0], 2)

    def test_balance_sheet_allows_repeated_company_year_from_source(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO balancesheet(id, company_id, year, fiscal_year) VALUES(1, 'AAA', 'Mar 2024', 2024)")
        self.conn.execute("INSERT INTO balancesheet(id, company_id, year, fiscal_year) VALUES(2, 'AAA', 'Mar 2024', 2024)")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM balancesheet").fetchone()[0], 2)

    def test_market_cap_unique_company_year(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO market_cap(id, company_id, year) VALUES(1, 'AAA', 2024)")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO market_cap(id, company_id, year) VALUES(2, 'AAA', 2024)")

    def test_cashflow_sum_rule_finds_error(self):
        self.conn.execute("INSERT INTO companies(id, company_name) VALUES('AAA', 'A Ltd')")
        self.conn.execute("INSERT INTO cashflow(id, company_id, year, fiscal_year, operating_activity, investing_activity, financing_activity, net_cash_flow) VALUES(1, 'AAA', 'Mar 2024', 2024, 1, 1, 1, 10)")
        sql = [rule[-1] for rule in DQ_RULES if rule[0] == "DQ-07"][0]
        self.assertEqual(scalar_count(self.conn, sql), 1)

    def test_load_order_has_twelve_tables(self):
        self.assertEqual(len(LOAD_ORDER), 12)

    def test_load_order_includes_market_cap(self):
        self.assertIn("market_cap", LOAD_ORDER)

    def test_load_order_includes_peer_groups(self):
        self.assertIn("peer_groups", LOAD_ORDER)

    def test_unknown_company_rows_are_filtered_before_insert(self):
        frame = pd.DataFrame({"id": [1, 2], "company_id": ["AAA", "NOPE"]})
        filtered, rejected, sample = split_known_companies(frame, {"AAA"})
        self.assertEqual(len(filtered), 1)
        self.assertEqual(rejected, 1)
        self.assertIn("NOPE", sample)

    def test_companies_frame_is_not_filtered(self):
        frame = pd.DataFrame({"id": ["AAA", "NOPE"], "company_name": ["A", "N"]})
        filtered, rejected, sample = split_known_companies(frame, {"AAA"})
        self.assertEqual(len(filtered), 2)
        self.assertEqual(rejected, 0)
        self.assertEqual(sample, "")


if __name__ == "__main__":
    unittest.main()
