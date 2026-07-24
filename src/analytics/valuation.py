from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SUMMARY_COLUMNS = [
    "company_id",
    "company_name",
    "sector",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "FCF_yield_pct",
    "5yr_median_PE",
    "PE_vs_sector_median_pct",
    "flag",
]


def load_valuation_frame(db_path: str | Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    query = """
    WITH latest_market AS (
      SELECT mc.*,
             ROW_NUMBER() OVER (PARTITION BY mc.company_id ORDER BY mc.year DESC, mc.id DESC) AS rn
      FROM market_cap mc
    ),
    latest_ratios AS (
      SELECT fr.company_id, fr.fiscal_year, fr.free_cash_flow_cr,
             ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
      FROM financial_ratios fr
      WHERE fr.fiscal_year IS NOT NULL
    )
    SELECT c.id AS company_id,
           c.company_name,
           COALESCE(s.broad_sector, 'Unassigned') AS sector,
           lm.pe_ratio AS "P/E",
           lm.pb_ratio AS "P/B",
           lm.ev_ebitda AS "EV/EBITDA",
           lm.market_cap_crore,
           lr.free_cash_flow_cr
    FROM companies c
    LEFT JOIN sectors s ON s.company_id = c.id
    LEFT JOIN latest_market lm ON lm.company_id = c.id AND lm.rn = 1
    LEFT JOIN latest_ratios lr ON lr.company_id = c.id AND lr.rn = 1
    ORDER BY c.id
    """
    frame = pd.read_sql_query(query, conn)
    conn.close()
    return frame


def classify_valuation(pe_ratio: float | None, sector_median: float | None) -> str:
    if pd.isna(pe_ratio) or pd.isna(sector_median) or sector_median == 0:
        return "Fair"
    if pe_ratio > sector_median * 1.5:
        return "Caution"
    if pe_ratio < sector_median * 0.7:
        return "Discount"
    return "Fair"


def compute_valuation_summary(db_path: str | Path) -> pd.DataFrame:
    frame = load_valuation_frame(db_path)
    frame["FCF_yield_pct"] = (frame["free_cash_flow_cr"] / frame["market_cap_crore"]) * 100
    frame.loc[frame["market_cap_crore"].isna() | (frame["market_cap_crore"] == 0), "FCF_yield_pct"] = pd.NA
    sector_medians = frame.groupby("sector")["P/E"].median(numeric_only=True)
    frame["5yr_median_PE"] = frame["sector"].map(sector_medians)
    frame["PE_vs_sector_median_pct"] = (
        (frame["P/E"] - frame["5yr_median_PE"]) / frame["5yr_median_PE"] * 100
    )
    frame.loc[frame["5yr_median_PE"].isna() | (frame["5yr_median_PE"] == 0), "PE_vs_sector_median_pct"] = pd.NA
    frame["flag"] = frame.apply(lambda row: classify_valuation(row["P/E"], row["5yr_median_PE"]), axis=1)
    summary = frame[SUMMARY_COLUMNS].copy()
    for column in ["P/E", "P/B", "EV/EBITDA", "FCF_yield_pct", "5yr_median_PE", "PE_vs_sector_median_pct"]:
        summary[column] = pd.to_numeric(summary[column], errors="coerce").round(2)
    return summary


def write_valuation_outputs(db_path: str | Path, output_dir: str | Path) -> dict[str, int]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    summary = compute_valuation_summary(db_path)
    summary.to_excel(output_path / "valuation_summary.xlsx", index=False)
    flags = summary[summary["flag"].isin(["Caution", "Discount"])].copy()
    flags.to_csv(output_path / "valuation_flags.csv", index=False)
    return {
        "summary_rows": len(summary),
        "flag_rows": len(flags),
        "caution_rows": int((summary["flag"] == "Caution").sum()),
        "discount_rows": int((summary["flag"] == "Discount").sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Sprint 4 valuation outputs.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "output"))
    args = parser.parse_args()
    counts = write_valuation_outputs(args.db, args.output_dir)
    for key, value in counts.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
