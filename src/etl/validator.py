from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


DQ_RULES = [
    ("DQ-01", "CRITICAL", "companies", "Company primary key must be unique and exactly 92 companies must load", "SELECT (COUNT(*) - COUNT(DISTINCT id)) + CASE WHEN COUNT(*) = 92 THEN 0 ELSE 1 END FROM companies"),
    ("DQ-02", "CRITICAL", "financial facts", "Record IDs must be unique inside each financial fact table", "SELECT (SELECT COUNT(*) - COUNT(DISTINCT id) FROM profitandloss) + (SELECT COUNT(*) - COUNT(DISTINCT id) FROM balancesheet) + (SELECT COUNT(*) - COUNT(DISTINCT id) FROM cashflow) + (SELECT COUNT(*) - COUNT(DISTINCT id) FROM financial_ratios) + (SELECT COUNT(*) - COUNT(DISTINCT id) FROM market_cap)"),
    ("DQ-03", "CRITICAL", "all", "Foreign-key integrity must pass", "PRAGMA foreign_key_check"),
    ("DQ-04", "WARNING", "balancesheet", "Balance sheet assets and liabilities should match within 1%", "SELECT COUNT(*) FROM balancesheet WHERE total_assets IS NOT NULL AND total_liabilities IS NOT NULL AND ABS(total_assets-total_liabilities) > MAX(1, ABS(total_assets)*0.01)"),
    ("DQ-05", "WARNING", "profitandloss", "Operating profit should match sales minus expenses within 1%", "SELECT COUNT(*) FROM profitandloss WHERE sales IS NOT NULL AND expenses IS NOT NULL AND operating_profit IS NOT NULL AND ABS((sales-expenses)-operating_profit) > MAX(1, ABS(sales)*0.01)"),
    ("DQ-06", "WARNING", "profitandloss", "Sales should be positive", "SELECT COUNT(*) FROM profitandloss WHERE sales <= 0"),
    ("DQ-07", "WARNING", "cashflow", "Net cash flow should equal operating + investing + financing within 1 crore", "SELECT COUNT(*) FROM cashflow WHERE net_cash_flow IS NOT NULL AND ABS((operating_activity+investing_activity+financing_activity)-net_cash_flow) > 1"),
    ("DQ-08", "WARNING", "documents", "Available annual report URLs should be HTTP(S) PDF links", "SELECT COUNT(*) FROM documents WHERE annual_report IS NOT NULL AND (annual_report NOT LIKE 'http%' OR lower(annual_report) NOT LIKE '%.pdf%')"),
    ("DQ-09", "CRITICAL", "companies", "Company website, NSE profile, and BSE profile URLs must be valid when present", "SELECT COUNT(*) FROM companies WHERE (website IS NOT NULL AND website NOT LIKE 'http%') OR (nse_profile IS NOT NULL AND nse_profile NOT LIKE 'http%') OR (bse_profile IS NOT NULL AND bse_profile NOT LIKE 'http%')"),
    ("DQ-10", "WARNING", "profitandloss", "Tax percentage should be between -100 and 100", "SELECT COUNT(*) FROM profitandloss WHERE tax_percentage < -100 OR tax_percentage > 100"),
    ("DQ-11", "WARNING", "profitandloss", "Dividend payout should be between 0 and 200", "SELECT COUNT(*) FROM profitandloss WHERE dividend_payout < 0 OR dividend_payout > 200"),
    ("DQ-12", "WARNING", "stock_prices", "Stock high should be >= low", "SELECT COUNT(*) FROM stock_prices WHERE high_price < low_price"),
    ("DQ-13", "WARNING", "stock_prices", "Close price should be between high and low", "SELECT COUNT(*) FROM stock_prices WHERE close_price < low_price OR close_price > high_price"),
    ("DQ-14", "WARNING", "stock_prices", "Volume should be non-negative", "SELECT COUNT(*) FROM stock_prices WHERE volume < 0"),
    ("DQ-15", "WARNING", "profitandloss", "EPS sign should generally match net profit sign", "SELECT COUNT(*) FROM profitandloss WHERE eps IS NOT NULL AND net_profit IS NOT NULL AND ((eps < 0 AND net_profit > 0) OR (eps > 0 AND net_profit < 0))"),
    ("DQ-16", "WARNING", "companies", "Companies should have at least five years across P&L, balance sheet, or cash flow", "SELECT COUNT(*) FROM companies c WHERE (SELECT COUNT(DISTINCT fiscal_year) FROM profitandloss p WHERE p.company_id=c.id) < 5 AND (SELECT COUNT(DISTINCT fiscal_year) FROM balancesheet b WHERE b.company_id=c.id) < 5 AND (SELECT COUNT(DISTINCT fiscal_year) FROM cashflow cf WHERE cf.company_id=c.id) < 5"),
]


def scalar_count(conn: sqlite3.Connection, sql: str) -> int:
    rows = conn.execute(sql).fetchall()
    if sql.strip().upper().startswith("PRAGMA"):
        return len(rows)
    return int(rows[0][0] or 0)


def validate(db_path: Path, failures_path: Path) -> list[dict[str, object]]:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    failures: list[dict[str, object]] = []

    for rule_id, severity, table_name, description, sql in DQ_RULES:
        count = scalar_count(conn, sql)
        if count:
            failures.append(
                {
                    "rule_id": rule_id,
                    "severity": severity,
                    "table": table_name,
                    "failure_count": count,
                    "description": description,
                    "sql": sql,
                }
            )

    failures_path.parent.mkdir(parents=True, exist_ok=True)
    with failures_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["rule_id", "severity", "table", "failure_count", "description", "sql"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(failures)

    conn.close()
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sprint 1 data quality rules.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--failures", default=str(PROJECT_ROOT / "output" / "validation_failures.csv"))
    args = parser.parse_args()
    failures = validate(Path(args.db), Path(args.failures))
    critical = sum(1 for row in failures if row["severity"] == "CRITICAL")
    print(f"{len(DQ_RULES)} rules run; {len(failures)} rules with failures; {critical} critical failure groups.")


if __name__ == "__main__":
    main()
