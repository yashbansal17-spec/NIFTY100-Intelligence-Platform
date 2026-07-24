from __future__ import annotations

import csv

from fastapi import APIRouter

from api.db import PROJECT_ROOT


router = APIRouter(tags=["portfolio"])


@router.get("/portfolio/stats")
def portfolio_stats() -> list[dict]:
    """Return portfolio KPI percentile table."""
    path = PROJECT_ROOT / "output" / "portfolio_stats.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
