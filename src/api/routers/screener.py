from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.db import rows


router = APIRouter(tags=["screener"])


@router.get("/screener")
def screener(
    min_roe: float | None = None,
    max_de: float | None = None,
    min_fcf: float | None = None,
    sector: str | None = None,
    min_rev_cagr_5yr: float | None = None,
    min_pat_cagr_5yr: float | None = None,
    max_pe: float | None = None,
) -> list[dict]:
    """Return ranked screener results from latest company KPIs."""
    for name, value in {
        "min_roe": min_roe,
        "max_de": max_de,
        "min_fcf": min_fcf,
        "min_rev_cagr_5yr": min_rev_cagr_5yr,
        "min_pat_cagr_5yr": min_pat_cagr_5yr,
        "max_pe": max_pe,
    }.items():
        if value is not None and abs(value) > 1_000_000:
            raise HTTPException(status_code=400, detail=f"Invalid parameter value for {name}")
    sql = """
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
    SELECT c.id AS company_id, c.company_name, s.broad_sector, latest.return_on_equity_pct,
           latest.debt_to_equity, latest.free_cash_flow_cr, latest.revenue_cagr_5yr,
           latest.pat_cagr_5yr, latest.operating_profit_margin_pct,
           lm.pe_ratio, lm.pb_ratio, latest.composite_quality_score
    FROM companies c
    LEFT JOIN sectors s ON s.company_id = c.id
    LEFT JOIN latest ON latest.company_id = c.id AND latest.rn = 1
    LEFT JOIN latest_market lm ON lm.company_id = c.id AND lm.rn = 1
    WHERE 1=1
    """
    params: list = []
    if min_roe is not None:
        sql += " AND latest.return_on_equity_pct >= ?"
        params.append(min_roe)
    if max_de is not None:
        sql += " AND (s.broad_sector = 'Financials' OR latest.debt_to_equity <= ?)"
        params.append(max_de)
    if min_fcf is not None:
        sql += " AND latest.free_cash_flow_cr >= ?"
        params.append(min_fcf)
    if sector:
        sql += " AND LOWER(s.broad_sector) LIKE LOWER(?)"
        params.append(f"%{sector}%")
    if min_rev_cagr_5yr is not None:
        sql += " AND latest.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)
    if min_pat_cagr_5yr is not None:
        sql += " AND latest.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)
    if max_pe is not None:
        sql += " AND lm.pe_ratio <= ?"
        params.append(max_pe)
    sql += " ORDER BY latest.composite_quality_score DESC"
    return rows(sql, tuple(params))
