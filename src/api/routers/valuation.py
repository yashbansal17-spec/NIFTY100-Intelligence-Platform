from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.db import rows


router = APIRouter(tags=["valuation"])


@router.get("/market-cap/{ticker}")
def market_cap(ticker: str) -> list[dict]:
    """Return historical valuation multiples for a company."""
    data = rows(
        """
        SELECT company_id, year, market_cap_crore, enterprise_value_crore,
               pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct
        FROM market_cap
        WHERE company_id = ?
        ORDER BY year
        """,
        (ticker.upper(),),
    )
    if not data:
        raise HTTPException(status_code=404, detail="Market-cap history not found")
    for row in data:
        row["data_source"] = "SIMULATED"
    return data
