from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from api.db import PROJECT_ROOT, one, rows


router = APIRouter(tags=["companies"])


def year_clause(column: str, from_year: str | None, to_year: str | None) -> tuple[str, list]:
    """Build a fiscal-year filter from YYYY or YYYY-MM query values."""
    clauses = []
    params: list = []
    if from_year:
        clauses.append(f"{column} >= ?")
        params.append(int(from_year[:4]))
    if to_year:
        clauses.append(f"{column} <= ?")
        params.append(int(to_year[:4]))
    return (" AND " + " AND ".join(clauses)) if clauses else "", params


@router.get("/companies")
def companies(
    sector: str | None = None,
    market_cap_category: str | None = None,
    search: str | None = None,
) -> list[dict]:
    """Return all companies with optional sector/category/search filters."""
    sql = """
    SELECT c.id, c.company_name, s.broad_sector, s.sub_sector, s.market_cap_category,
           c.roe_percentage AS roe_pct, c.roce_percentage AS roce_pct
    FROM companies c
    LEFT JOIN sectors s ON s.company_id = c.id
    WHERE 1=1
    """
    params: list = []
    if sector:
        sql += " AND LOWER(s.broad_sector) LIKE LOWER(?)"
        params.append(f"%{sector}%")
    if market_cap_category:
        sql += " AND LOWER(s.market_cap_category) = LOWER(?)"
        params.append(market_cap_category)
    if search:
        sql += " AND (LOWER(c.id) LIKE LOWER(?) OR LOWER(c.company_name) LIKE LOWER(?))"
        params.extend([f"%{search}%", f"%{search}%"])
    sql += " ORDER BY c.id"
    return rows(sql, tuple(params))


@router.get("/companies/{ticker}")
def company_profile(ticker: str) -> dict:
    """Return full company profile with latest KPIs and sector fields."""
    data = one(
        """
        WITH latest AS (
          SELECT fr.*,
                 ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
          FROM financial_ratios fr
          WHERE fr.fiscal_year IS NOT NULL
        )
        SELECT c.*, s.broad_sector, s.sub_sector, s.market_cap_category,
               latest.fiscal_year AS latest_year, latest.return_on_equity_pct,
               latest.return_on_capital_employed_pct, latest.net_profit_margin_pct,
               latest.debt_to_equity, latest.revenue_cagr_5yr, latest.free_cash_flow_cr,
               latest.composite_quality_score
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        LEFT JOIN latest ON latest.company_id = c.id AND latest.rn = 1
        WHERE c.id = ?
        """,
        (ticker.upper(),),
    )
    if not data:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return data


@router.get("/companies/{ticker}/pl")
def company_pl(ticker: str, from_year: str | None = None, to_year: str | None = None) -> list[dict]:
    """Return profit and loss history for a company."""
    clause, params = year_clause("fiscal_year", from_year, to_year)
    return rows(f"SELECT * FROM profitandloss WHERE company_id = ? {clause} ORDER BY fiscal_year", (ticker.upper(), *params))


@router.get("/companies/{ticker}/bs")
def company_bs(ticker: str, from_year: str | None = None, to_year: str | None = None) -> list[dict]:
    """Return balance sheet history for a company."""
    clause, params = year_clause("fiscal_year", from_year, to_year)
    return rows(f"SELECT * FROM balancesheet WHERE company_id = ? {clause} ORDER BY fiscal_year", (ticker.upper(), *params))


@router.get("/companies/{ticker}/cashflow")
def company_cashflow(ticker: str, from_year: str | None = None, to_year: str | None = None) -> list[dict]:
    """Return cash-flow history for a company."""
    clause, params = year_clause("fiscal_year", from_year, to_year)
    return rows(f"SELECT * FROM cashflow WHERE company_id = ? {clause} ORDER BY fiscal_year", (ticker.upper(), *params))


@router.get("/companies/{ticker}/ratios")
def company_ratios(ticker: str, year: int | None = None) -> list[dict] | dict:
    """Return computed KPI ratios for a company, optionally one year."""
    if year is not None:
        data = one(
            "SELECT * FROM financial_ratios WHERE company_id = ? AND fiscal_year = ?",
            (ticker.upper(), year),
        )
        if not data:
            raise HTTPException(status_code=404, detail="Ratio row not found")
        return data
    return rows("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY fiscal_year", (ticker.upper(),))


@router.get("/companies/{ticker}/tearsheet")
def company_tearsheet(ticker: str) -> FileResponse:
    """Return pre-generated company tearsheet PDF."""
    path = PROJECT_ROOT / "reports" / "tearsheets" / f"{ticker.upper()}_tearsheet.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Tearsheet not found")
    return FileResponse(str(path), media_type="application/pdf", filename=path.name)
