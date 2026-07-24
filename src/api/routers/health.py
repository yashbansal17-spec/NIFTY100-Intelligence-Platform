from __future__ import annotations

import time

from fastapi import APIRouter

from api.db import one


router = APIRouter(tags=["health"])
START_TIME = time.perf_counter()
TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "financial_ratios",
    "peer_groups",
    "stock_prices",
    "market_cap",
]


@router.get("/health")
def health() -> dict:
    """Return API health, uptime, version, and core table row counts."""
    counts = {table: one(f"SELECT COUNT(*) AS count FROM {table}")["count"] for table in TABLES}
    return {
        "status": "ok",
        "db_row_counts": counts,
        "uptime_seconds": round(time.perf_counter() - START_TIME, 2),
        "version": "sprint6-v1",
    }
