from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from cagr import cagr_for_window
from cashflow_kpis import (
    capital_allocation_pattern,
    capex_intensity,
    cfo_quality_label,
    cfo_quality_ratio,
    fcf_conversion_rate,
    free_cash_flow,
    sign,
)
from ratios import (
    asset_turnover,
    book_value_per_share,
    composite_quality_score,
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


PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXTRA_COLUMNS = {
    "return_on_capital_employed_pct": "REAL",
    "return_on_assets_pct": "REAL",
    "high_leverage_flag": "INTEGER DEFAULT 0",
    "icr_label": "TEXT",
    "icr_warning_flag": "INTEGER DEFAULT 0",
    "net_debt_cr": "REAL",
    "revenue_cagr_3yr": "REAL",
    "revenue_cagr_3yr_flag": "TEXT",
    "revenue_cagr_5yr": "REAL",
    "revenue_cagr_5yr_flag": "TEXT",
    "revenue_cagr_10yr": "REAL",
    "revenue_cagr_10yr_flag": "TEXT",
    "pat_cagr_3yr": "REAL",
    "pat_cagr_3yr_flag": "TEXT",
    "pat_cagr_5yr": "REAL",
    "pat_cagr_5yr_flag": "TEXT",
    "pat_cagr_10yr": "REAL",
    "pat_cagr_10yr_flag": "TEXT",
    "eps_cagr_3yr": "REAL",
    "eps_cagr_3yr_flag": "TEXT",
    "eps_cagr_5yr": "REAL",
    "eps_cagr_5yr_flag": "TEXT",
    "eps_cagr_10yr": "REAL",
    "eps_cagr_10yr_flag": "TEXT",
    "cfo_quality_score": "REAL",
    "cfo_quality_label": "TEXT",
    "capex_intensity_pct": "REAL",
    "capex_intensity_label": "TEXT",
    "fcf_conversion_rate_pct": "REAL",
    "capital_allocation_pattern": "TEXT",
    "roce_benchmark_mode": "TEXT",
    "composite_quality_score": "REAL",
}


def rowdict(cursor: sqlite3.Cursor, sql: str, params: tuple = ()) -> list[dict]:
    cursor.execute(sql, params)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def first_by_key(rows: list[dict], *keys: str) -> dict[tuple, dict]:
    result = {}
    for row in rows:
        key = tuple(row[key_name] for key_name in keys)
        result.setdefault(key, row)
    return result


def ensure_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(financial_ratios)").fetchall()}
    for column, column_type in EXTRA_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE financial_ratios ADD COLUMN {column} {column_type}")
    conn.commit()


def build_series(rows: list[dict], value_col: str) -> dict[str, dict[int, float | None]]:
    series: dict[str, dict[int, float | None]] = {}
    for row in rows:
        if row["fiscal_year"] is None:
            continue
        series.setdefault(row["company_id"], {})[int(row["fiscal_year"])] = row[value_col]
    return series


def populate(db_path: Path, output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    ensure_columns(conn)

    pl_rows = rowdict(cur, "SELECT * FROM profitandloss WHERE fiscal_year IS NOT NULL")
    bs_rows = rowdict(cur, "SELECT * FROM balancesheet WHERE fiscal_year IS NOT NULL")
    cf_rows = rowdict(cur, "SELECT * FROM cashflow WHERE fiscal_year IS NOT NULL")
    ratio_rows = rowdict(cur, "SELECT * FROM financial_ratios WHERE fiscal_year IS NOT NULL")
    companies = first_by_key(rowdict(cur, "SELECT * FROM companies"), "id")
    sectors = first_by_key(rowdict(cur, "SELECT * FROM sectors"), "company_id")
    pl_by_key = first_by_key(pl_rows, "company_id", "fiscal_year")
    bs_by_key = first_by_key(bs_rows, "company_id", "fiscal_year")
    cf_by_key = first_by_key(cf_rows, "company_id", "fiscal_year")

    sales_series = build_series(pl_rows, "sales")
    pat_series = build_series(pl_rows, "net_profit")
    eps_series = build_series(pl_rows, "eps")
    edge_entries: list[dict[str, object]] = []

    update_columns = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "return_on_assets_pct",
        "debt_to_equity",
        "high_leverage_flag",
        "interest_coverage",
        "icr_label",
        "icr_warning_flag",
        "net_debt_cr",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
        "revenue_cagr_3yr",
        "revenue_cagr_3yr_flag",
        "revenue_cagr_5yr",
        "revenue_cagr_5yr_flag",
        "revenue_cagr_10yr",
        "revenue_cagr_10yr_flag",
        "pat_cagr_3yr",
        "pat_cagr_3yr_flag",
        "pat_cagr_5yr",
        "pat_cagr_5yr_flag",
        "pat_cagr_10yr",
        "pat_cagr_10yr_flag",
        "eps_cagr_3yr",
        "eps_cagr_3yr_flag",
        "eps_cagr_5yr",
        "eps_cagr_5yr_flag",
        "eps_cagr_10yr",
        "eps_cagr_10yr_flag",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_intensity_label",
        "fcf_conversion_rate_pct",
        "capital_allocation_pattern",
        "roce_benchmark_mode",
        "composite_quality_score",
    ]

    for row in ratio_rows:
        key = (row["company_id"], row["fiscal_year"])
        pl = pl_by_key.get(key, {})
        bs = bs_by_key.get(key, {})
        cf = cf_by_key.get(key, {})
        sector = sectors.get((row["company_id"],), {})
        company = companies.get((row["company_id"],), {})
        broad_sector = sector.get("broad_sector")

        npm = net_profit_margin(pl.get("net_profit"), pl.get("sales"))
        opm, opm_mismatch = operating_profit_margin(pl.get("operating_profit"), pl.get("sales"), pl.get("opm_percentage"))
        roe = return_on_equity(pl.get("net_profit"), bs.get("equity_capital"), bs.get("reserves"))
        roce, roce_mode = return_on_capital_employed(
            pl.get("operating_profit"),
            pl.get("other_income"),
            bs.get("equity_capital"),
            bs.get("reserves"),
            bs.get("borrowings"),
            broad_sector,
        )
        roa = return_on_assets(pl.get("net_profit"), bs.get("total_assets"))
        de_ratio = debt_to_equity(bs.get("borrowings"), bs.get("equity_capital"), bs.get("reserves"))
        high_de = high_leverage_flag(de_ratio, broad_sector)
        icr, icr_label, icr_warning = interest_coverage(pl.get("operating_profit"), pl.get("other_income"), pl.get("interest"))
        fcf = free_cash_flow(cf.get("operating_activity"), cf.get("investing_activity"))
        cfo_quality = cfo_quality_ratio(cf.get("operating_activity"), pl.get("net_profit"))
        capex_pct, capex_label = capex_intensity(cf.get("investing_activity"), pl.get("sales"))
        fcf_conversion = fcf_conversion_rate(fcf, pl.get("operating_profit"))
        allocation = capital_allocation_pattern(
            cf.get("operating_activity"),
            cf.get("investing_activity"),
            cf.get("financing_activity"),
            cfo_quality,
        )

        values = {
            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm,
            "return_on_equity_pct": roe,
            "return_on_capital_employed_pct": roce,
            "return_on_assets_pct": roa,
            "debt_to_equity": de_ratio,
            "high_leverage_flag": int(high_de),
            "interest_coverage": icr,
            "icr_label": icr_label,
            "icr_warning_flag": int(icr_warning),
            "net_debt_cr": net_debt(bs.get("borrowings"), bs.get("investments")),
            "asset_turnover": asset_turnover(pl.get("sales"), bs.get("total_assets")),
            "free_cash_flow_cr": fcf,
            "capex_cr": abs(cf["investing_activity"]) if cf.get("investing_activity") is not None else None,
            "earnings_per_share": pl.get("eps"),
            "book_value_per_share": book_value_per_share(bs.get("equity_capital"), bs.get("reserves")),
            "dividend_payout_ratio_pct": pl.get("dividend_payout"),
            "total_debt_cr": bs.get("borrowings"),
            "cash_from_operations_cr": cf.get("operating_activity"),
            "cfo_quality_score": cfo_quality,
            "cfo_quality_label": cfo_quality_label(cfo_quality),
            "capex_intensity_pct": capex_pct,
            "capex_intensity_label": capex_label,
            "fcf_conversion_rate_pct": fcf_conversion,
            "capital_allocation_pattern": allocation,
            "roce_benchmark_mode": roce_mode,
        }

        for metric, series in (("revenue", sales_series), ("pat", pat_series), ("eps", eps_series)):
            for window in (3, 5, 10):
                value, flag = cagr_for_window(series.get(row["company_id"], {}), row["fiscal_year"], window)
                values[f"{metric}_cagr_{window}yr"] = value
                values[f"{metric}_cagr_{window}yr_flag"] = flag

        values["composite_quality_score"] = composite_quality_score(roe, npm, de_ratio, cfo_quality)

        assignments = ", ".join(f"{column}=?" for column in update_columns)
        cur.execute(
            f"UPDATE financial_ratios SET {assignments} WHERE id=?",
            [values.get(column) for column in update_columns] + [row["id"]],
        )

        if opm_mismatch:
            edge_entries.append(edge(row, "OPM_MISMATCH", "formula discrepancy", f"computed={opm:.2f}, source={pl.get('opm_percentage')}"))
        source_roe = company.get("roe_percentage")
        if roe is not None and source_roe is not None and abs(roe - source_roe) > 5:
            edge_entries.append(edge(row, "ROE_SOURCE_VARIANCE", "data source issue", f"computed={roe:.2f}, source_display={source_roe}"))
        source_roce = company.get("roce_percentage")
        if roce is not None and source_roce is not None and abs(roce - source_roce) > 5:
            edge_entries.append(edge(row, "ROCE_SOURCE_VARIANCE", "version difference", f"computed={roce:.2f}, source_display={source_roce}"))
        if broad_sector == "Financials" and de_ratio is not None and de_ratio > 5:
            edge_entries.append(edge(row, "FINANCIALS_LEVERAGE_SUPPRESSED", "formula decision", "D/E warning suppressed for Financials sector"))

    write_capital_allocation(output_dir, cf_rows, pl_by_key)
    write_edge_log(output_dir, edge_entries)
    write_manual_spot_check(output_dir, conn)
    write_screener_preview(output_dir, conn)
    conn.commit()

    summary = {
        "financial_ratios_rows": conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0],
        "capital_allocation_rows": len(cf_rows),
        "edge_case_rows": len(edge_entries),
    }
    conn.close()
    return summary


def edge(row: dict, rule: str, category: str, explanation: str) -> dict[str, object]:
    return {
        "company_id": row["company_id"],
        "fiscal_year": row["fiscal_year"],
        "rule": rule,
        "category": category,
        "explanation": explanation,
    }


def write_capital_allocation(output_dir: Path, cf_rows: list[dict], pl_by_key: dict[tuple, dict]) -> None:
    path = output_dir / "capital_allocation.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for cf in cf_rows:
            pl = pl_by_key.get((cf["company_id"], cf["fiscal_year"]), {})
            quality = cfo_quality_ratio(cf.get("operating_activity"), pl.get("net_profit"))
            writer.writerow(
                {
                    "company_id": cf["company_id"],
                    "year": cf["year"],
                    "cfo_sign": sign(cf.get("operating_activity")),
                    "cfi_sign": sign(cf.get("investing_activity")),
                    "cff_sign": sign(cf.get("financing_activity")),
                    "pattern_label": capital_allocation_pattern(
                        cf.get("operating_activity"),
                        cf.get("investing_activity"),
                        cf.get("financing_activity"),
                        quality,
                    ),
                }
            )


def write_edge_log(output_dir: Path, entries: list[dict[str, object]]) -> None:
    path = output_dir / "ratio_edge_cases.log"
    with path.open("w", encoding="utf-8") as handle:
        handle.write("company_id|fiscal_year|rule|category|explanation\n")
        for entry in entries:
            handle.write(
                f"{entry['company_id']}|{entry['fiscal_year']}|{entry['rule']}|{entry['category']}|{entry['explanation']}\n"
            )


def write_manual_spot_check(output_dir: Path, conn: sqlite3.Connection) -> None:
    query = """
    SELECT fr.company_id, fr.fiscal_year, fr.return_on_equity_pct, fr.revenue_cagr_5yr,
           p.net_profit, p.sales, b.equity_capital, b.reserves,
           p5.sales AS sales_5yr_ago
    FROM financial_ratios fr
    JOIN profitandloss p ON p.company_id=fr.company_id AND p.fiscal_year=fr.fiscal_year
    JOIN balancesheet b ON b.company_id=fr.company_id AND b.fiscal_year=fr.fiscal_year
    LEFT JOIN profitandloss p5 ON p5.company_id=fr.company_id AND p5.fiscal_year=fr.fiscal_year-5
    WHERE fr.company_id IN ('ABB','HDFCBANK','TCS') AND fr.revenue_cagr_5yr IS NOT NULL
    ORDER BY fr.company_id, fr.fiscal_year DESC
    """
    rows = rowdict(conn.cursor(), query)
    seen: set[str] = set()
    selected = []
    for row in rows:
        if row["company_id"] not in seen:
            selected.append(row)
            seen.add(row["company_id"])
    with (output_dir / "manual_spot_check.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "company_id",
            "fiscal_year",
            "db_roe",
            "manual_roe",
            "roe_diff_pct",
            "db_revenue_cagr_5yr",
            "manual_revenue_cagr_5yr",
            "revenue_cagr_diff_pct",
            "status",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in selected:
            manual_roe = return_on_equity(row["net_profit"], row["equity_capital"], row["reserves"])
            manual_cagr, _ = cagr_for_window(
                {row["fiscal_year"] - 5: row["sales_5yr_ago"], row["fiscal_year"]: row["sales"]},
                row["fiscal_year"],
                5,
            )
            roe_diff = abs((row["return_on_equity_pct"] or 0) - (manual_roe or 0))
            cagr_diff = abs((row["revenue_cagr_5yr"] or 0) - (manual_cagr or 0))
            writer.writerow(
                {
                    "company_id": row["company_id"],
                    "fiscal_year": row["fiscal_year"],
                    "db_roe": row["return_on_equity_pct"],
                    "manual_roe": manual_roe,
                    "roe_diff_pct": roe_diff,
                    "db_revenue_cagr_5yr": row["revenue_cagr_5yr"],
                    "manual_revenue_cagr_5yr": manual_cagr,
                    "revenue_cagr_diff_pct": cagr_diff,
                    "status": "PASS" if roe_diff < 0.1 and cagr_diff < 0.1 else "REVIEW",
                }
            )


def write_screener_preview(output_dir: Path, conn: sqlite3.Connection) -> None:
    query = """
    WITH latest AS (
      SELECT company_id, MAX(fiscal_year) AS fiscal_year
      FROM financial_ratios
      WHERE return_on_equity_pct IS NOT NULL AND debt_to_equity IS NOT NULL
      GROUP BY company_id
    )
    SELECT fr.company_id, fr.fiscal_year, ROUND(fr.return_on_equity_pct, 2) AS roe,
           ROUND(fr.debt_to_equity, 2) AS debt_to_equity
    FROM financial_ratios fr
    JOIN latest l USING(company_id, fiscal_year)
    WHERE fr.return_on_equity_pct > 15 AND fr.debt_to_equity < 1
    ORDER BY fr.return_on_equity_pct DESC
    """
    rows = rowdict(conn.cursor(), query)
    with (output_dir / "screener_preview.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["company_id", "fiscal_year", "roe", "debt_to_equity"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate Sprint 2 financial ratio KPIs.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "output"))
    args = parser.parse_args()
    summary = populate(Path(args.db), Path(args.output_dir))
    for key, value in summary.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
