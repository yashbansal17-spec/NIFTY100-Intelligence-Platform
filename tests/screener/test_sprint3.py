import sqlite3
import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from analytics.peer import percent_rank
from screener.engine import FILTERABLE_METRICS, add_composite_quality_score, apply_filters, load_screener_config, run_presets


class Sprint3ScreenerTests(unittest.TestCase):
    def sample_frame(self):
        return pd.DataFrame(
            [
                {
                    "company_id": "AAA",
                    "company_name": "A",
                    "broad_sector": "Industrials",
                    "return_on_equity_pct": 20,
                    "return_on_capital_employed_pct": 18,
                    "net_profit_margin_pct": 12,
                    "debt_to_equity": 0.5,
                    "free_cash_flow_cr": 10,
                    "revenue_cagr_5yr": 12,
                    "revenue_cagr_3yr": 14,
                    "pat_cagr_5yr": 22,
                    "eps_cagr_5yr": 15,
                    "operating_profit_margin_pct": 15,
                    "pe_ratio": 15,
                    "pb_ratio": 2,
                    "dividend_yield_pct": 2.5,
                    "interest_coverage": 5,
                    "icr_for_filter": 5,
                    "market_cap_crore": 10000,
                    "net_profit": 1000,
                    "asset_turnover": 1.2,
                    "sales": 6000,
                    "dividend_payout_ratio_pct": 50,
                    "previous_debt_to_equity": 0.7,
                    "de_declining_yoy": True,
                    "cfo_quality_score": 1.2,
                },
                {
                    "company_id": "BBB",
                    "company_name": "B",
                    "broad_sector": "Financials",
                    "return_on_equity_pct": 18,
                    "return_on_capital_employed_pct": 12,
                    "net_profit_margin_pct": 10,
                    "debt_to_equity": 8,
                    "free_cash_flow_cr": 20,
                    "revenue_cagr_5yr": 11,
                    "revenue_cagr_3yr": 12,
                    "pat_cagr_5yr": 21,
                    "eps_cagr_5yr": 14,
                    "operating_profit_margin_pct": 14,
                    "pe_ratio": 18,
                    "pb_ratio": 2.5,
                    "dividend_yield_pct": 1.5,
                    "interest_coverage": None,
                    "icr_for_filter": float("inf"),
                    "market_cap_crore": 20000,
                    "net_profit": 2000,
                    "asset_turnover": 0.8,
                    "sales": 8000,
                    "dividend_payout_ratio_pct": 60,
                    "previous_debt_to_equity": 9,
                    "de_declining_yoy": True,
                    "cfo_quality_score": 0.9,
                },
            ]
        )

    def test_filterable_metric_count(self):
        self.assertEqual(len(FILTERABLE_METRICS), 15)

    def test_config_has_six_presets(self):
        config = load_screener_config(PROJECT_ROOT / "config" / "screener_config.yaml")
        self.assertEqual(len(config["presets"]), 6)

    def test_quality_compounder_filter(self):
        result = apply_filters(add_composite_quality_score(self.sample_frame()), {"roe_min": 15, "de_max": 1, "fcf_min": 0})
        self.assertEqual(set(result["company_id"]), {"AAA", "BBB"})

    def test_de_filter_skips_financials(self):
        result = apply_filters(add_composite_quality_score(self.sample_frame()), {"de_max": 1})
        self.assertIn("BBB", set(result["company_id"]))

    def test_icr_debt_free_infinity_passes(self):
        result = apply_filters(add_composite_quality_score(self.sample_frame()), {"icr_min": 100})
        self.assertIn("BBB", set(result["company_id"]))

    def test_composite_score_added(self):
        result = add_composite_quality_score(self.sample_frame())
        self.assertIn("composite_quality_score", result.columns)

    def test_run_presets_returns_all_presets(self):
        config = load_screener_config(PROJECT_ROOT / "config" / "screener_config.yaml")
        result = run_presets(add_composite_quality_score(self.sample_frame()), config)
        self.assertEqual(set(result), set(config["presets"]))

    def test_percent_rank_highest_value(self):
        ranks = percent_rank(pd.Series([10, 20, 30]), True)
        self.assertEqual(ranks.iloc[2], 1.0)

    def test_percent_rank_de_inverse(self):
        ranks = percent_rank(pd.Series([0.5, 2.0, 5.0]), False)
        self.assertGreater(ranks.iloc[0], ranks.iloc[2])

    def test_turnaround_watch_de_declining(self):
        result = apply_filters(add_composite_quality_score(self.sample_frame()), {"de_declining_yoy": True})
        self.assertEqual(len(result), 2)

    def test_asset_turnover_filter(self):
        result = apply_filters(add_composite_quality_score(self.sample_frame()), {"asset_turnover_min": 1.0})
        self.assertEqual(list(result["company_id"]), ["AAA"])

    def test_sales_filter(self):
        result = apply_filters(add_composite_quality_score(self.sample_frame()), {"sales_min": 7000})
        self.assertEqual(list(result["company_id"]), ["BBB"])

    def test_value_pick_filter(self):
        result = apply_filters(add_composite_quality_score(self.sample_frame()), {"pe_max": 20, "pb_max": 3, "dividend_yield_min": 1})
        self.assertEqual(len(result), 2)

    def test_peer_percentile_table_shape(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE peer_percentiles(company_id TEXT, peer_group_name TEXT, metric TEXT, value REAL, percentile_rank REAL, year INTEGER)")
        conn.execute("INSERT INTO peer_percentiles VALUES('AAA','G','ROE',20,1,2024)")
        count = conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
