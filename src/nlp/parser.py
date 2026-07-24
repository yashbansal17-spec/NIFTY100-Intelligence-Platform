from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PATTERN = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%", re.IGNORECASE)
TARGET_FIELDS = ["compounded_sales_growth", "compounded_profit_growth", "stock_price_cagr", "roe"]


def rowdict(cursor: sqlite3.Cursor, sql: str, params: tuple = ()) -> list[dict]:
    cursor.execute(sql, params)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def metric_to_ratio_column(metric_type: str, period_years: int) -> str | None:
    if metric_type == "compounded_sales_growth":
        return f"revenue_cagr_{period_years}yr"
    if metric_type == "compounded_profit_growth":
        return f"pat_cagr_{period_years}yr"
    if metric_type == "roe":
        return "return_on_equity_pct"
    return None


def latest_ratio_lookup(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = rowdict(
        conn.cursor(),
        """
        WITH latest AS (
          SELECT fr.*,
                 ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY fiscal_year DESC, id DESC) AS rn
          FROM financial_ratios fr
          WHERE fiscal_year IS NOT NULL
        )
        SELECT * FROM latest WHERE rn = 1
        """,
    )
    return {row["company_id"]: row for row in rows}


def parse_analysis(db_path: str | Path, output_dir: str | Path) -> dict[str, int]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    analysis_rows = rowdict(conn.cursor(), "SELECT company_id, compounded_sales_growth, compounded_profit_growth, stock_price_cagr, roe FROM analysis")
    ratios = latest_ratio_lookup(conn)
    parsed_rows = []
    failure_rows = []
    for row in analysis_rows:
        company_id = row["company_id"]
        latest = ratios.get(company_id, {})
        for field in TARGET_FIELDS:
            text = row.get(field)
            if text is None or not str(text).strip():
                failure_rows.append({"company_id": company_id, "metric_type": field, "raw_text": text, "reason": "blank"})
                continue
            matches = PATTERN.findall(str(text))
            if not matches:
                failure_rows.append({"company_id": company_id, "metric_type": field, "raw_text": text, "reason": "no_regex_match"})
                continue
            for years, value in matches:
                period_years = int(years)
                value_pct = float(value)
                ratio_column = metric_to_ratio_column(field, period_years)
                computed = latest.get(ratio_column) if ratio_column else None
                divergence = None
                status = "NOT_COMPARABLE"
                if computed is not None:
                    divergence = abs(value_pct - float(computed))
                    status = "REVIEW" if divergence > 5 else "PASS"
                parsed_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": field,
                        "period_years": period_years,
                        "value_pct": value_pct,
                        "computed_value_pct": computed,
                        "divergence_pct": divergence,
                        "status": status,
                    }
                )
    conn.close()
    with (output_path / "analysis_parsed.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "company_id",
                "metric_type",
                "period_years",
                "value_pct",
                "computed_value_pct",
                "divergence_pct",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(parsed_rows)
    with (output_path / "parse_failures.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["company_id", "metric_type", "raw_text", "reason"])
        writer.writeheader()
        writer.writerows(failure_rows)
    return {"parsed_rows": len(parsed_rows), "parse_failures": len(failure_rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse Sprint 5 analysis text fields.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "output"))
    args = parser.parse_args()
    counts = parse_analysis(args.db, args.output_dir)
    for key, value in counts.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
