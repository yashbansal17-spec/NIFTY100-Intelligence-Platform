from __future__ import annotations

import argparse
import csv
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def query(db_path: str | Path, sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def safe(value, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}{suffix}"
    return str(value)


def add_light_texture(image: Image.Image) -> None:
    pixels = image.load()
    width, height = image.size
    for y in range(0, height, 3):
        for x in range(0, width, 3):
            shade = 246 + ((x * 17 + y * 31) % 9)
            pixels[x, y] = (shade, shade, min(255, shade + 2))


def draw_trend_chart(path: Path, pl: pd.DataFrame, ratios: pd.DataFrame) -> None:
    image = Image.new("RGB", (900, 360), "white")
    add_light_texture(image)
    draw = ImageDraw.Draw(image)
    draw.text((20, 15), "Revenue, Net Profit, ROE and ROCE trend", fill=(12, 35, 64))
    left, top, width, height = 60, 70, 780, 220
    draw.rectangle((left, top, left + width, top + height), outline=(210, 210, 210))
    data = pl.dropna(subset=["fiscal_year"]).tail(10).copy()
    if data.empty:
        image.save(path, format="JPEG", quality=95)
        return
    max_value = max(float(data["sales"].max() or 1), float(data["net_profit"].max() or 1), 1)
    step = width / max(len(data), 1)
    for idx, row in enumerate(data.itertuples()):
        x = left + idx * step + 8
        sales_h = max(1, float(row.sales or 0) / max_value * height)
        profit_h = max(1, float(row.net_profit or 0) / max_value * height)
        draw.rectangle((x, top + height - sales_h, x + 18, top + height), fill=(44, 99, 235))
        draw.rectangle((x + 22, top + height - profit_h, x + 40, top + height), fill=(21, 128, 61))
        draw.text((x - 4, top + height + 10), str(int(row.fiscal_year)), fill=(70, 70, 70))
    ratio_data = ratios.dropna(subset=["fiscal_year"]).tail(10)
    for column, color in [("return_on_equity_pct", (220, 80, 50)), ("return_on_capital_employed_pct", (120, 70, 180))]:
        points = []
        values = pd.to_numeric(ratio_data[column], errors="coerce")
        max_ratio = max(float(values.max() or 1), 1)
        for idx, value in enumerate(values):
            if pd.isna(value):
                continue
            x = left + idx * step + 24
            y = top + height - (float(value) / max_ratio * height)
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=color, width=3)
    draw.text((60, 320), "Blue: Revenue | Green: Net Profit | Red: ROE | Purple: ROCE", fill=(70, 70, 70))
    image.save(path, format="JPEG", quality=95)


def draw_balance_cash_chart(path: Path, bs: pd.DataFrame, cf: pd.DataFrame) -> None:
    image = Image.new("RGB", (900, 360), "white")
    add_light_texture(image)
    draw = ImageDraw.Draw(image)
    draw.text((20, 15), "Balance sheet composition and latest cash-flow waterfall", fill=(12, 35, 64))
    left, top, width, height = 60, 70, 480, 220
    draw.rectangle((left, top, left + width, top + height), outline=(210, 210, 210))
    data = bs.dropna(subset=["fiscal_year"]).tail(8).copy()
    max_total = max(float(data["total_liabilities"].max() or 1), 1) if not data.empty else 1
    step = width / max(len(data), 1)
    for idx, row in enumerate(data.itertuples()):
        x = left + idx * step + 8
        y = top + height
        pieces = [
            (float(row.equity_capital or 0) + float(row.reserves or 0), (44, 99, 235)),
            (float(row.borrowings or 0), (220, 80, 50)),
            (float(row.other_liabilities or 0), (120, 120, 120)),
        ]
        for value, color in pieces:
            piece_h = value / max_total * height
            draw.rectangle((x, y - piece_h, x + 34, y), fill=color)
            y -= piece_h
        draw.text((x - 2, top + height + 10), str(int(row.fiscal_year)), fill=(70, 70, 70))
    latest_cf = cf.dropna(subset=["fiscal_year"]).tail(1)
    if not latest_cf.empty:
        row = latest_cf.iloc[0]
        x0, y0 = 610, 250
        for idx, (label, value) in enumerate(
            [
                ("CFO", row.get("operating_activity")),
                ("CFI", row.get("investing_activity")),
                ("CFF", row.get("financing_activity")),
                ("Net", row.get("net_cash_flow")),
            ]
        ):
            val = float(value or 0)
            bar_h = min(120, abs(val) / max(abs(float(row.get("operating_activity") or 1)), 1) * 120)
            color = (21, 128, 61) if val >= 0 else (220, 80, 50)
            x = x0 + idx * 65
            draw.rectangle((x, y0 - bar_h, x + 38, y0), fill=color)
            draw.text((x, y0 + 8), label, fill=(70, 70, 70))
    draw.text((60, 320), "Blue: Equity/reserves | Red: Borrowings | Grey: Other liabilities", fill=(70, 70, 70))
    image.save(path, format="JPEG", quality=95)


def wrapped_list(items: list[str], color) -> list:
    style = ParagraphStyle("wrapped", fontSize=8, leading=10, textColor=color)
    return [[Paragraph(item, style)] for item in items[:6]] or [[Paragraph("N/A", style)]]


def company_data(db_path: str | Path, ticker: str) -> dict[str, pd.DataFrame]:
    return {
        "profile": query(
            db_path,
            """
            SELECT c.id AS company_id, c.company_name, c.about_company,
                   COALESCE(s.broad_sector, 'Unassigned') AS sector, s.sub_sector
            FROM companies c
            LEFT JOIN sectors s ON s.company_id = c.id
            WHERE c.id = ?
            """,
            (ticker,),
        ),
        "ratios": query(db_path, "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY fiscal_year", (ticker,)),
        "pl": query(db_path, "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY fiscal_year", (ticker,)),
        "bs": query(db_path, "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY fiscal_year", (ticker,)),
        "cf": query(db_path, "SELECT * FROM cashflow WHERE company_id = ? ORDER BY fiscal_year", (ticker,)),
    }


def generated_pros_cons(output_dir: Path, ticker: str) -> tuple[list[str], list[str]]:
    path = output_dir / "pros_cons_generated.csv"
    if not path.exists():
        return [], []
    frame = pd.read_csv(path)
    company = frame[frame["company_id"] == ticker]
    return company[company["type"] == "pro"]["text"].tolist(), company[company["type"] == "con"]["text"].tolist()


def build_tearsheet(db_path: str | Path, output_dir: Path, ticker: str, pdf_path: Path) -> bool:
    data = company_data(db_path, ticker)
    partial_history = data["pl"].dropna(subset=["fiscal_year"])["fiscal_year"].nunique() < 3
    profile = data["profile"].iloc[0]
    ratios = data["ratios"]
    latest = ratios.tail(1).iloc[0] if not ratios.empty else {}
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], textColor=colors.white, fontSize=18, leading=22)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=8, leading=10)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    story = []
    header = Table([[Paragraph(f"{profile['company_name']} ({ticker})", title_style)]], colWidths=[7.3 * inch])
    header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#12385f")), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story.append(header)
    story.append(Spacer(1, 10))
    kpis = [
        ("ROE", safe(latest.get("return_on_equity_pct"), "%")),
        ("ROCE", safe(latest.get("return_on_capital_employed_pct"), "%")),
        ("NPM", safe(latest.get("net_profit_margin_pct"), "%")),
        ("D/E", safe(latest.get("debt_to_equity"))),
        ("Revenue CAGR", safe(latest.get("revenue_cagr_5yr"), "%")),
        ("FCF", safe(latest.get("free_cash_flow_cr"))),
    ]
    table = Table([[f"{label}\n{value}" for label, value in kpis[:3]], [f"{label}\n{value}" for label, value in kpis[3:]]], colWidths=[2.42 * inch] * 3)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4fb")), ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor("#b7c9dc")), ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.white), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Sector:</b> {profile['sector']} | <b>Sub-sector:</b> {safe(profile.get('sub_sector'))}", body))
    story.append(Paragraph("<b>SIMULATED:</b> stock_prices and market_cap datasets are simulated where used for valuation or price context.", body))
    if partial_history:
        story.append(Paragraph("<b>Data available note:</b> fewer than 3 years of history is available for this company.", body))
    story.append(Paragraph(safe(profile.get("about_company")), body))
    with tempfile.TemporaryDirectory() as tmp:
        trend = Path(tmp) / f"{ticker}_trend.jpg"
        balance = Path(tmp) / f"{ticker}_balance.jpg"
        draw_trend_chart(trend, data["pl"], ratios)
        story.append(RLImage(str(trend), width=7.1 * inch, height=2.85 * inch))
        story.append(PageBreak())
        draw_balance_cash_chart(balance, data["bs"], data["cf"])
        story.append(RLImage(str(balance), width=7.1 * inch, height=2.85 * inch))
        story.append(Spacer(1, 10))
        pros, cons = generated_pros_cons(output_dir, ticker)
        pc_table = Table(
            [[Paragraph("<b>Pros</b>", body), Paragraph("<b>Cons</b>", body)]] + list(zip([row[0] for row in wrapped_list(pros, colors.darkgreen)], [row[0] for row in wrapped_list(cons, colors.darkred)])),
            colWidths=[3.55 * inch, 3.55 * inch],
        )
        pc_table.setStyle(TableStyle([("WORDWRAP", (0, 0), (-1, -1), "CJK"), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor("#b7c9dc")), ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dce5ef"))]))
        story.append(pc_table)
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>Capital Allocation:</b> {safe(latest.get('capital_allocation_pattern'))}", body))
        doc.build(story)
    return True


def trend_arrow(values: pd.Series) -> str:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if len(clean) < 2:
        return "flat"
    previous, latest = clean.iloc[-2], clean.iloc[-1]
    if previous == 0:
        return "flat"
    change = (latest - previous) / abs(previous) * 100
    if change > 2:
        return "up"
    if change < -2:
        return "down"
    return "flat"


def build_portfolio_summary(db_path: str | Path, reports_dir: Path) -> int:
    reports_dir.mkdir(parents=True, exist_ok=True)
    companies = query(db_path, "SELECT id AS company_id, company_name FROM companies ORDER BY id")
    path = reports_dir / "portfolio_summary.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    story = []
    for idx, row in enumerate(companies.itertuples()):
        data = company_data(db_path, row.company_id)
        ratios = data["ratios"]
        latest = ratios.tail(1).iloc[0] if not ratios.empty else {}
        profile = data["profile"].iloc[0]
        story.append(Paragraph(f"{row.company_id} - {row.company_name}", styles["Heading1"]))
        story.append(Paragraph(f"Sector: {profile['sector']}", styles["BodyText"]))
        story.append(Paragraph("SIMULATED: stock_prices and market_cap datasets are simulated where used for valuation or price context.", styles["BodyText"]))
        metric_rows = []
        for label, column, suffix in [
            ("ROE", "return_on_equity_pct", "%"),
            ("ROCE", "return_on_capital_employed_pct", "%"),
            ("NPM", "net_profit_margin_pct", "%"),
            ("D/E", "debt_to_equity", ""),
            ("FCF", "free_cash_flow_cr", ""),
            ("Composite", "composite_quality_score", ""),
        ]:
            metric_rows.append([label, safe(latest.get(column), suffix), trend_arrow(ratios[column]) if column in ratios else "flat"])
        table = Table([["Metric", "Latest", "Trend"]] + metric_rows, colWidths=[2.2 * inch, 2.2 * inch, 2.2 * inch])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12385f")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dce5ef"))]))
        story.append(table)
        if idx < len(companies) - 1:
            story.append(PageBreak())
    doc.build(story)
    return len(companies)


def generate_tearsheets(db_path: str | Path, output_dir: str | Path, reports_dir: str | Path) -> dict[str, int]:
    output_path = Path(output_dir)
    reports_path = Path(reports_dir)
    tearsheet_dir = reports_path / "tearsheets"
    portfolio_dir = reports_path / "portfolio"
    tearsheet_dir.mkdir(parents=True, exist_ok=True)
    companies = query(db_path, "SELECT id AS company_id FROM companies ORDER BY id")
    skipped = []
    generated = 0
    for row in companies.itertuples():
        pdf_path = tearsheet_dir / f"{row.company_id}_tearsheet.pdf"
        build_tearsheet(db_path, output_path, row.company_id, pdf_path)
        generated += 1
        history_count = query(db_path, "SELECT COUNT(DISTINCT fiscal_year) AS years FROM profitandloss WHERE company_id=? AND fiscal_year IS NOT NULL", (row.company_id,))["years"].iloc[0]
        if history_count < 3:
            skipped.append({"company_id": row.company_id, "reason": "data_limited_tearsheet_generated"})
    with (output_path / "skipped_tearsheets.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["company_id", "reason"])
        writer.writeheader()
        writer.writerows(skipped)
    portfolio_pages = build_portfolio_summary(db_path, portfolio_dir)
    return {"tearsheets": generated, "skipped": len(skipped), "portfolio_pages": portfolio_pages}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Sprint 5 company tearsheets and portfolio summary.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "output"))
    parser.add_argument("--reports-dir", default=str(PROJECT_ROOT / "reports"))
    args = parser.parse_args()
    counts = generate_tearsheets(args.db, args.output_dir, args.reports_dir)
    for key, value in counts.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
