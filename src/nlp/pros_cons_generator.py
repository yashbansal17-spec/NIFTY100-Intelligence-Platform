from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def rowdict(cursor: sqlite3.Cursor, sql: str, params: tuple = ()) -> list[dict]:
    cursor.execute(sql, params)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def latest_rows(conn: sqlite3.Connection) -> list[dict]:
    return rowdict(
        conn.cursor(),
        """
        WITH latest AS (
          SELECT fr.*,
                 ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
          FROM financial_ratios fr
          WHERE fr.fiscal_year IS NOT NULL
        ),
        latest_pl AS (
          SELECT p.*,
                 ROW_NUMBER() OVER (PARTITION BY p.company_id ORDER BY p.fiscal_year DESC, p.id DESC) AS rn
          FROM profitandloss p
          WHERE p.fiscal_year IS NOT NULL
        ),
        latest_bs AS (
          SELECT b.*,
                 ROW_NUMBER() OVER (PARTITION BY b.company_id ORDER BY b.fiscal_year DESC, b.id DESC) AS rn
          FROM balancesheet b
          WHERE b.fiscal_year IS NOT NULL
        ),
        latest_market AS (
          SELECT mc.*,
                 ROW_NUMBER() OVER (PARTITION BY mc.company_id ORDER BY mc.year DESC, mc.id DESC) AS rn
          FROM market_cap mc
        )
        SELECT c.id AS company_id, c.company_name, COALESCE(s.broad_sector, 'Unassigned') AS broad_sector,
               fr.fiscal_year, fr.return_on_equity_pct, fr.operating_profit_margin_pct,
               fr.debt_to_equity, fr.free_cash_flow_cr, fr.revenue_cagr_5yr,
               fr.pat_cagr_5yr, fr.icr_label, fr.interest_coverage, fr.eps_cagr_5yr,
               fr.dividend_payout_ratio_pct, fr.return_on_capital_employed_pct,
               fr.net_debt_cr, p.sales, p.net_profit, p.operating_profit, p.eps,
               b.borrowings, b.total_assets, mc.dividend_yield_pct
        FROM companies c
        LEFT JOIN latest fr ON fr.company_id = c.id AND fr.rn = 1
        LEFT JOIN latest_pl p ON p.company_id = c.id AND p.rn = 1
        LEFT JOIN latest_bs b ON b.company_id = c.id AND b.rn = 1
        LEFT JOIN latest_market mc ON mc.company_id = c.id AND mc.rn = 1
        LEFT JOIN sectors s ON s.company_id = c.id
        ORDER BY c.id
        """,
    )


def history(conn: sqlite3.Connection, company_id: str) -> list[dict]:
    return rowdict(
        conn.cursor(),
        """
        SELECT fr.fiscal_year, fr.return_on_equity_pct, fr.operating_profit_margin_pct,
               fr.debt_to_equity, fr.free_cash_flow_cr, fr.earnings_per_share,
               fr.return_on_capital_employed_pct, fr.net_debt_cr, p.sales, p.net_profit,
               p.operating_profit, b.borrowings, b.total_assets
        FROM financial_ratios fr
        LEFT JOIN profitandloss p ON p.company_id = fr.company_id AND p.fiscal_year = fr.fiscal_year
        LEFT JOIN balancesheet b ON b.company_id = fr.company_id AND b.fiscal_year = fr.fiscal_year
        WHERE fr.company_id = ? AND fr.fiscal_year IS NOT NULL
        ORDER BY fr.fiscal_year
        """,
        (company_id,),
    )


def increasing(values: list[float | None], count: int) -> bool:
    series = [value for value in values if value is not None]
    if len(series) < count:
        return False
    tail = series[-count:]
    return all(tail[idx] > tail[idx - 1] for idx in range(1, len(tail)))


def declining(values: list[float | None], count: int) -> bool:
    series = [value for value in values if value is not None]
    if len(series) < count:
        return False
    tail = series[-count:]
    return all(tail[idx] < tail[idx - 1] for idx in range(1, len(tail)))


def confidence(base: float, value: float | None = None, threshold: float | None = None) -> int:
    if value is None or threshold in (None, 0):
        return int(base)
    return int(min(100, max(61, base + abs(value - threshold) * 1.5)))


def add(rows: list[dict], company_id: str, kind: str, rule_id: str, text: str, score: int) -> None:
    if score > 60:
        rows.append({"company_id": company_id, "type": kind, "rule_id": rule_id, "text": text, "confidence_pct": score})


def generate_for_company(row: dict, hist: list[dict]) -> list[dict]:
    out: list[dict] = []
    company_id = row["company_id"]
    roes = [item.get("return_on_equity_pct") for item in hist]
    fcfs = [item.get("free_cash_flow_cr") for item in hist]
    opms = [item.get("operating_profit_margin_pct") for item in hist]
    sales = [item.get("sales") for item in hist]
    des = [item.get("debt_to_equity") for item in hist]
    eps = [item.get("earnings_per_share") for item in hist]
    borrowings = [item.get("borrowings") for item in hist]
    total_assets = [item.get("total_assets") for item in hist]

    if len([value for value in roes[-3:] if value is not None and value > 20]) >= 3:
        add(out, company_id, "pro", "PRO-01", "Consistently high return on equity above 20% demonstrates exceptional capital efficiency", confidence(82, row.get("return_on_equity_pct"), 20))
    if len([value for value in fcfs[-5:] if value is not None and value > 0]) >= 5:
        add(out, company_id, "pro", "PRO-02", "Strong free cash flow generation over 5 years signals healthy business fundamentals", 84)
    if row.get("debt_to_equity") is not None and row["debt_to_equity"] <= 0.01:
        add(out, company_id, "pro", "PRO-03", "Debt-free balance sheet provides financial flexibility and eliminates interest burden", 88)
    if row.get("revenue_cagr_5yr") is not None and row["revenue_cagr_5yr"] > 15:
        add(out, company_id, "pro", "PRO-04", "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum", confidence(78, row["revenue_cagr_5yr"], 15))
    if row.get("operating_profit_margin_pct") is not None and row["operating_profit_margin_pct"] > 25:
        add(out, company_id, "pro", "PRO-05", "Operating profit margin above 25% indicates strong pricing power and cost discipline", confidence(80, row["operating_profit_margin_pct"], 25))
    if row.get("pat_cagr_5yr") is not None and row["pat_cagr_5yr"] > 20:
        add(out, company_id, "pro", "PRO-06", "Net profit compounding at above 20% over 5 years creates significant shareholder value", confidence(80, row["pat_cagr_5yr"], 20))
    if row.get("icr_label") == "Debt Free" or (row.get("interest_coverage") is not None and row["interest_coverage"] > 10):
        add(out, company_id, "pro", "PRO-07", "Very high interest coverage ratio reflects negligible financial stress from debt servicing", 86)
    if (row.get("dividend_yield_pct") is not None and row["dividend_yield_pct"] > 2) and (row.get("free_cash_flow_cr") is not None and row["free_cash_flow_cr"] > 0):
        add(out, company_id, "pro", "PRO-08", "Consistent dividend yield above 2% backed by positive free cash flow", 78)
    if row.get("eps_cagr_5yr") is not None and row["eps_cagr_5yr"] > 15:
        add(out, company_id, "pro", "PRO-09", "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding", confidence(78, row["eps_cagr_5yr"], 15))
    if increasing(roes, 3):
        add(out, company_id, "pro", "PRO-10", "Return on equity improving for 3 consecutive years shows strengthening business quality", 76)
    if row.get("revenue_cagr_5yr") is not None and row.get("pat_cagr_5yr") is not None and row["pat_cagr_5yr"] > row["revenue_cagr_5yr"]:
        add(out, company_id, "pro", "PRO-11", "Revenue growing slower than profits shows improving operating leverage and scale benefits", 76)
    if increasing(total_assets, 3) and declining(borrowings, 3):
        add(out, company_id, "pro", "PRO-12", "Growing asset base funded by internal accruals reflects self-sustaining growth", 74)

    if row.get("debt_to_equity") is not None and row["debt_to_equity"] > 2.0 and row.get("broad_sector") != "Financials":
        add(out, company_id, "con", "CON-01", f"Debt-to-equity ratio of {row['debt_to_equity']:.2f} is elevated for a non-financial company and warrants monitoring", confidence(78, row["debt_to_equity"], 2))
    if len([value for value in fcfs[-3:] if value is not None and value < 0]) >= 3:
        add(out, company_id, "con", "CON-02", "Free cash flow negative for 3 consecutive years raises concern about cash generation quality", 84)
    if declining(opms, 3):
        add(out, company_id, "con", "CON-03", "Operating margins declining for 3 consecutive years suggest pricing or cost pressure", 78)
    if row.get("net_profit") is not None and row["net_profit"] < 0:
        add(out, company_id, "con", "CON-04", "Company reported a net loss in the most recent financial year", 88)
    if declining(sales, 2):
        add(out, company_id, "con", "CON-05", "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss", 78)
    if row.get("interest_coverage") is not None and row["interest_coverage"] < 1.5:
        add(out, company_id, "con", "CON-06", "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations", 84)
    if row.get("dividend_payout_ratio_pct") is not None and row["dividend_payout_ratio_pct"] > 100:
        add(out, company_id, "con", "CON-07", "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable", 82)
    if increasing(des, 3):
        add(out, company_id, "con", "CON-08", "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk", 76)
    if declining(eps, 3):
        add(out, company_id, "con", "CON-09", "Earnings per share declining for 3 consecutive years reflects deteriorating profitability", 78)
    if row.get("return_on_capital_employed_pct") is not None and row["return_on_capital_employed_pct"] < 10:
        add(out, company_id, "con", "CON-10", "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital", 82)
    ebitda = (row.get("operating_profit") or 0)
    if row.get("net_debt_cr") is not None and ebitda > 0 and row["net_debt_cr"] > 3 * ebitda:
        add(out, company_id, "con", "CON-11", "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility", 84)
    if row.get("revenue_cagr_5yr") is not None and row["revenue_cagr_5yr"] < 5:
        add(out, company_id, "con", "CON-12", "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum", 78)

    if not any(item["type"] == "pro" for item in out):
        add(out, company_id, "pro", "PRO-FALLBACK", "Stable NIFTY100 constituent with enough available financial history for ongoing monitoring", 61)
    if not any(item["type"] == "con" for item in out):
        add(out, company_id, "con", "CON-FALLBACK", "No major red-flag rule triggered; continue monitoring valuation, growth, and cash-flow quality", 61)
    return out


def generate_pros_cons(db_path: str | Path, output_dir: str | Path) -> dict[str, int]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    rows = latest_rows(conn)
    output_rows = []
    for row in rows:
        output_rows.extend(generate_for_company(row, history(conn, row["company_id"])))
    conn.close()
    with (output_path / "pros_cons_generated.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["company_id", "type", "rule_id", "text", "confidence_pct"])
        writer.writeheader()
        writer.writerows(output_rows)
    companies = {row["company_id"] for row in rows}
    companies_with_pro = {row["company_id"] for row in output_rows if row["type"] == "pro"}
    companies_with_con = {row["company_id"] for row in output_rows if row["type"] == "con"}
    return {
        "generated_rows": len(output_rows),
        "companies": len(companies),
        "companies_with_pro": len(companies_with_pro),
        "companies_with_con": len(companies_with_con),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Sprint 5 rule-based pros and cons.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "output"))
    args = parser.parse_args()
    counts = generate_pros_cons(args.db, args.output_dir)
    for key, value in counts.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
