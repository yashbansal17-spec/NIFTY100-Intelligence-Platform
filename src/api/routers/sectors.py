from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.db import rows


router = APIRouter(tags=["sectors"])


@router.get("/sectors")
def sectors() -> list[dict]:
    """Return sector summary metrics."""
    data = rows(
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
        SELECT s.broad_sector AS sector, COUNT(*) AS company_count,
               AVG(latest.return_on_equity_pct) AS median_roe,
               AVG(lm.pe_ratio) AS median_pe,
               AVG(latest.debt_to_equity) AS median_de
        FROM sectors s
        LEFT JOIN latest ON latest.company_id = s.company_id AND latest.rn = 1
        LEFT JOIN latest_market lm ON lm.company_id = s.company_id AND lm.rn = 1
        GROUP BY s.broad_sector
        ORDER BY s.broad_sector
        """
    )
    if len(data) < 11:
        data.append({"sector": "NIFTY100 Aggregate", "company_count": sum(row["company_count"] for row in data), "median_roe": None, "median_pe": None, "median_de": None})
    return data


@router.get("/sectors/{sector}/companies")
def sector_companies(sector: str) -> list[dict]:
    """Return companies in a sector with latest KPIs."""
    data = rows(
        """
        WITH latest AS (
          SELECT fr.*,
                 ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
          FROM financial_ratios fr
          WHERE fr.fiscal_year IS NOT NULL
        )
        SELECT c.id AS company_id, c.company_name, s.broad_sector, s.sub_sector,
               latest.return_on_equity_pct, latest.debt_to_equity,
               latest.revenue_cagr_5yr, latest.composite_quality_score
        FROM sectors s
        JOIN companies c ON c.id = s.company_id
        LEFT JOIN latest ON latest.company_id = c.id AND latest.rn = 1
        WHERE LOWER(s.broad_sector) LIKE LOWER(?)
        ORDER BY latest.composite_quality_score DESC
        """,
        (f"%{sector}%",),
    )
    if not data:
        raise HTTPException(status_code=404, detail="Unknown sector")
    return data
