from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def sign(value: float | None) -> str:
    if value is None or value == 0:
        return "0"
    return "+" if value > 0 else "-"


def free_cash_flow(operating_activity: float | None, investing_activity: float | None) -> float | None:
    if operating_activity is None and investing_activity is None:
        return None
    return (operating_activity or 0) + (investing_activity or 0)


def cfo_quality_ratio(cfo: float | None, pat: float | None) -> float | None:
    if cfo is None or pat in (None, 0):
        return None
    return cfo / pat


def cfo_quality_label(ratio: float | None) -> str | None:
    if ratio is None:
        return None
    if ratio > 1.0:
        return "High Quality"
    if ratio >= 0.5:
        return "Moderate"
    return "Accrual Risk"


def capex_intensity(investing_activity: float | None, sales: float | None) -> tuple[float | None, str | None]:
    if investing_activity is None or sales in (None, 0):
        return None, None
    value = abs(investing_activity) / sales * 100
    if value < 3:
        return value, "Asset Light"
    if value <= 8:
        return value, "Moderate"
    return value, "Capital Intensive"


def fcf_conversion_rate(fcf: float | None, operating_profit: float | None) -> float | None:
    if fcf is None or operating_profit in (None, 0):
        return None
    return fcf / operating_profit * 100


def capital_allocation_pattern(
    cfo: float | None,
    cfi: float | None,
    cff: float | None,
    cfo_pat_ratio: float | None = None,
) -> str:
    pattern = (sign(cfo), sign(cfi), sign(cff))
    if pattern == ("+", "-", "-") and cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
        return "Shareholder Returns"
    labels = {
        ("+", "-", "-"): "Reinvestor",
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue",
        ("+", "-", "+"): "Mixed",
    }
    return labels.get(pattern, "Mixed")


def fcf_cagr(values: list[float | None]) -> float | None:
    series = [value for value in values if value is not None]
    if len(series) < 6:
        return None
    start = series[-6]
    end = series[-1]
    if start <= 0 or end <= 0:
        return None
    return ((end / start) ** (1 / 5) - 1) * 100


def rowdict(cursor: sqlite3.Cursor, sql: str, params: tuple = ()) -> list[dict]:
    cursor.execute(sql, params)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def generate_cashflow_intelligence(db_path: str | Path, output_dir: str | Path) -> dict[str, int]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    rows = rowdict(
        conn.cursor(),
        """
        SELECT c.id AS company_id, c.company_name, COALESCE(s.broad_sector, 'Unassigned') AS sector,
               fr.fiscal_year, fr.cfo_quality_score, fr.cfo_quality_label,
               fr.capex_intensity_pct, fr.capex_intensity_label, fr.free_cash_flow_cr,
               fr.fcf_conversion_rate_pct, fr.capital_allocation_pattern,
               cf.operating_activity, cf.financing_activity, p.net_profit,
               b.borrowings
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        LEFT JOIN financial_ratios fr ON fr.company_id = c.id
        LEFT JOIN cashflow cf ON cf.company_id = fr.company_id AND cf.fiscal_year = fr.fiscal_year
        LEFT JOIN profitandloss p ON p.company_id = fr.company_id AND p.fiscal_year = fr.fiscal_year
        LEFT JOIN balancesheet b ON b.company_id = fr.company_id AND b.fiscal_year = fr.fiscal_year
        ORDER BY c.id, fr.fiscal_year
        """,
    )
    conn.close()
    frame = pd.DataFrame(rows)
    output_rows = []
    pattern_changes = []
    distress_rows = []
    for company_id, group in frame.groupby("company_id"):
        group = group.dropna(subset=["fiscal_year"]).sort_values("fiscal_year").copy()
        if group.empty:
            first = frame[frame["company_id"] == company_id].iloc[0]
            output_rows.append(
                {
                    "company_id": company_id,
                    "sector": first.get("sector"),
                    "cfo_quality_score": None,
                    "cfo_quality_label": "N/A",
                    "capex_intensity_pct": None,
                    "capex_label": "N/A",
                    "fcf_cagr_5yr": None,
                    "fcf_conversion_pct": None,
                    "distress_flag": False,
                    "deleveraging_flag": False,
                    "capital_allocation_label": "Unclassified",
                }
            )
            continue
        latest = group.iloc[-1]
        previous = group.iloc[-2] if len(group) > 1 else None
        fcf_series = group["free_cash_flow_cr"].tolist()
        distress = bool((latest.get("operating_activity") or 0) < 0 and (latest.get("financing_activity") or 0) > 0)
        deleveraging = False
        if previous is not None:
            deleveraging = bool((latest.get("financing_activity") or 0) < 0 and (latest.get("borrowings") or 0) < (previous.get("borrowings") or 0))
            if latest.get("capital_allocation_pattern") != previous.get("capital_allocation_pattern"):
                pattern_changes.append(
                    {
                        "company_id": company_id,
                        "company_name": latest.get("company_name"),
                        "previous_year": int(previous.get("fiscal_year")),
                        "latest_year": int(latest.get("fiscal_year")),
                        "previous_pattern": previous.get("capital_allocation_pattern"),
                        "latest_pattern": latest.get("capital_allocation_pattern"),
                    }
                )
        output_rows.append(
            {
                "company_id": company_id,
                "sector": latest.get("sector"),
                "cfo_quality_score": latest.get("cfo_quality_score"),
                "cfo_quality_label": latest.get("cfo_quality_label"),
                "capex_intensity_pct": latest.get("capex_intensity_pct"),
                "capex_label": latest.get("capex_intensity_label"),
                "fcf_cagr_5yr": fcf_cagr(fcf_series),
                "fcf_conversion_pct": latest.get("fcf_conversion_rate_pct"),
                "distress_flag": distress,
                "deleveraging_flag": deleveraging,
                "capital_allocation_label": latest.get("capital_allocation_pattern"),
            }
        )
        if distress:
            distress_rows.append(
                {
                    "company_id": company_id,
                    "company_name": latest.get("company_name"),
                    "sector": latest.get("sector"),
                    "cfo_value": latest.get("operating_activity"),
                    "cff_value": latest.get("financing_activity"),
                    "latest_net_profit": latest.get("net_profit"),
                }
            )
    intelligence = pd.DataFrame(output_rows)
    intelligence.to_excel(output_path / "cashflow_intelligence.xlsx", index=False)
    pd.DataFrame(distress_rows).to_csv(output_path / "distress_alerts.csv", index=False)
    pd.DataFrame(pattern_changes).to_csv(output_path / "pattern_changes.csv", index=False)
    latest_patterns = intelligence.groupby("capital_allocation_label").size().reset_index(name="company_count")
    latest_patterns.to_csv(output_path / "capital_allocation_distribution.csv", index=False)
    return {
        "cashflow_intelligence_rows": len(intelligence),
        "distress_alert_rows": len(distress_rows),
        "pattern_change_rows": len(pattern_changes),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Sprint 5 cash-flow intelligence outputs.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "output"))
    args = parser.parse_args()
    counts = generate_cashflow_intelligence(args.db, args.output_dir)
    for key, value in counts.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
