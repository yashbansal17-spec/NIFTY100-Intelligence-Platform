from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.db import rows


router = APIRouter(tags=["documents"])


@router.get("/companies/{ticker}/documents")
def company_documents(ticker: str) -> list[dict]:
    """Return annual report links for a company."""
    data = rows(
        """
        SELECT year, annual_report,
               CASE WHEN annual_report IS NOT NULL AND TRIM(annual_report) <> '' THEN 1 ELSE 0 END AS is_url_valid
        FROM documents
        WHERE company_id = ?
        ORDER BY year DESC
        """,
        (ticker.upper(),),
    )
    if not data:
        raise HTTPException(status_code=404, detail="No documents found")
    for row in data:
        row["is_url_valid"] = bool(row["is_url_valid"])
    return data
