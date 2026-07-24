from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def query(db_path: str | Path, sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def safe(value) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}"
    return str(value)


def latest_sector_frame(db_path: str | Path) -> pd.DataFrame:
    return query(
        db_path,
        """
        WITH latest AS (
          SELECT fr.*,
                 ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
          FROM financial_ratios fr
          WHERE fr.fiscal_year IS NOT NULL
        ),
        latest_market AS (
          SELECT mc.*,
                 ROW_NUMBER() OVER (PARTITION BY mc.company_id ORDER BY mc.year DESC, mc.id DESC) AS rn
          FROM market_cap mc
        )
        SELECT c.id AS company_id, c.company_name, COALESCE(s.broad_sector, 'Unassigned') AS sector,
               s.sub_sector, fr.return_on_equity_pct, fr.return_on_capital_employed_pct,
               fr.net_profit_margin_pct, fr.debt_to_equity, fr.free_cash_flow_cr,
               fr.revenue_cagr_5yr, fr.pat_cagr_5yr, fr.composite_quality_score,
               mc.pe_ratio
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        LEFT JOIN latest fr ON fr.company_id = c.id AND fr.rn = 1
        LEFT JOIN latest_market mc ON mc.company_id = c.id AND mc.rn = 1
        ORDER BY sector, c.id
        """,
    )


def build_sector_pdf(frame: pd.DataFrame, sector: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    cell = ParagraphStyle("cell", parent=styles["BodyText"], fontSize=7, leading=8)
    story = [Paragraph(f"{sector} Sector Report", styles["Heading1"])]
    story.append(Spacer(1, 8))
    story.append(Paragraph("SIMULATED: market_cap valuation inputs are simulated and should be interpreted as modelling data.", styles["BodyText"]))
    story.append(Spacer(1, 8))
    metrics = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "composite_quality_score",
    ]
    medians = frame[metrics].median(numeric_only=True)
    summary = [["Metric", "Median"]] + [[metric, safe(medians.get(metric))] for metric in metrics]
    summary_table = Table(summary, colWidths=[2.7 * inch, 1.4 * inch])
    summary_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12385f")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dce5ef"))]))
    story.append(summary_table)
    story.append(Spacer(1, 12))
    headers = ["Ticker", "Company", "Sub-sector", "ROE", "ROCE", "NPM", "D/E", "FCF", "Rev CAGR", "PAT CAGR", "Score"]
    rows = [headers]
    for row in frame.itertuples():
        rows.append(
            [
                row.company_id,
                Paragraph(str(row.company_name), cell),
                Paragraph(str(row.sub_sector or "N/A"), cell),
                safe(row.return_on_equity_pct),
                safe(row.return_on_capital_employed_pct),
                safe(row.net_profit_margin_pct),
                safe(row.debt_to_equity),
                safe(row.free_cash_flow_cr),
                safe(row.revenue_cagr_5yr),
                safe(row.pat_cagr_5yr),
                safe(row.composite_quality_score),
            ]
        )
    table = Table(rows, repeatRows=1, colWidths=[0.75 * inch, 1.7 * inch, 1.35 * inch, 0.65 * inch, 0.65 * inch, 0.65 * inch, 0.55 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch, 0.65 * inch])
    table.setStyle(TableStyle([("WORDWRAP", (0, 0), (-1, -1), "CJK"), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12385f")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dce5ef")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(table)
    doc.build(story)


def generate_sector_reports(db_path: str | Path, reports_dir: str | Path) -> dict[str, int]:
    frame = latest_sector_frame(db_path)
    sector_dir = Path(reports_dir) / "sector"
    count = 0
    for sector, group in frame.groupby("sector", dropna=False):
        safe_name = str(sector).replace("/", "-").replace("\\", "-").replace(" ", "_")
        build_sector_pdf(group, str(sector), sector_dir / f"{safe_name}_report.pdf")
        count += 1
    if count < 11:
        build_sector_pdf(frame, "NIFTY100 All Sectors", sector_dir / "NIFTY100_All_Sectors_report.pdf")
        count += 1
    return {"sector_reports": count}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Sprint 5 sector PDF reports.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--reports-dir", default=str(PROJECT_ROOT / "reports"))
    args = parser.parse_args()
    counts = generate_sector_reports(args.db, args.reports_dir)
    for key, value in counts.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
