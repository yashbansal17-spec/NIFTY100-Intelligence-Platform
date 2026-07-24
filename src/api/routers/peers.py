from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.db import rows


router = APIRouter(tags=["peers"])
RADAR_METRICS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "composite_quality_score",
]


@router.get("/peers/{group_name}")
def peer_group(group_name: str) -> list[dict]:
    """Return peer percentile data for a peer group."""
    data = rows(
        """
        SELECT pp.*, c.company_name
        FROM peer_percentiles pp
        JOIN companies c ON c.id = pp.company_id
        WHERE LOWER(pp.peer_group_name) LIKE LOWER(?)
        ORDER BY pp.company_id, pp.metric
        """,
        (f"%{group_name}%",),
    )
    if not data:
        raise HTTPException(status_code=404, detail="Unknown peer group")
    return data


@router.get("/companies/{ticker}/peers/compare")
def peer_compare(ticker: str) -> dict:
    """Return radar values for company, peer average, and benchmark company."""
    group = rows("SELECT peer_group_name, is_benchmark FROM peer_groups WHERE company_id = ?", (ticker.upper(),))
    if not group:
        raise HTTPException(status_code=404, detail="No peer group assigned")
    group_name = group[0]["peer_group_name"]
    benchmark = rows(
        """
        SELECT pg.company_id, c.company_name
        FROM peer_groups pg
        JOIN companies c ON c.id = pg.company_id
        WHERE pg.peer_group_name = ? AND pg.is_benchmark = 1
        LIMIT 1
        """,
        (group_name,),
    )
    company_values = rows(
        """
        WITH latest AS (
          SELECT fr.*,
                 ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY fiscal_year DESC, id DESC) AS rn
          FROM financial_ratios fr
          WHERE fiscal_year IS NOT NULL
        )
        SELECT * FROM latest WHERE company_id = ? AND rn = 1
        """,
        (ticker.upper(),),
    )
    peer_avg = rows(
        """
        WITH latest AS (
          SELECT fr.*,
                 ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
          FROM financial_ratios fr
          WHERE fr.fiscal_year IS NOT NULL
        )
        SELECT AVG(return_on_equity_pct) AS return_on_equity_pct,
               AVG(return_on_capital_employed_pct) AS return_on_capital_employed_pct,
               AVG(net_profit_margin_pct) AS net_profit_margin_pct,
               AVG(debt_to_equity) AS debt_to_equity,
               AVG(free_cash_flow_cr) AS free_cash_flow_cr,
               AVG(pat_cagr_5yr) AS pat_cagr_5yr,
               AVG(revenue_cagr_5yr) AS revenue_cagr_5yr,
               AVG(composite_quality_score) AS composite_quality_score
        FROM peer_groups pg
        JOIN latest ON latest.company_id = pg.company_id AND latest.rn = 1
        WHERE pg.peer_group_name = ?
        """,
        (group_name,),
    )
    if not company_values:
        raise HTTPException(status_code=404, detail="Company ratios not found")
    return {
        "company_id": ticker.upper(),
        "peer_group_name": group_name,
        "benchmark_company": benchmark[0] if benchmark else None,
        "company": {metric: company_values[0].get(metric) for metric in RADAR_METRICS},
        "peer_average": {metric: peer_avg[0].get(metric) for metric in RADAR_METRICS},
    }
