from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from api.routers import companies, documents, health, peers, portfolio, screener, sectors, valuation


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="NIFTY100 Intelligence Platform API", version="sprint6-v1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log method, path, and response time for each API request."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logging.info("%s %s %.2fms", request.method, request.url.path, elapsed_ms)
    return response


for router in [
    health.router,
    companies.router,
    screener.router,
    sectors.router,
    peers.router,
    valuation.router,
    portfolio.router,
    documents.router,
]:
    app.include_router(router, prefix="/api/v1")
