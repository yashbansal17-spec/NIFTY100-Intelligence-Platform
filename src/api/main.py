from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from api.routers import companies, documents, health, peers, portfolio, screener, sectors, valuation

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(
    title="NIFTY100 Intelligence Platform API",
    description="High-performance financial analytics and intelligence API for India's benchmark NIFTY 100 universe.",
    version="sprint6-v1",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup for web dashboard and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def validate_api_key_and_log(request: Request, call_next):
    """
    Async HTTP Middleware logging request timing and validating optional API key.
    Supports X-API-Key header or api_key query parameter.
    """
    start = time.perf_counter()
    
    # Check if API Key validation is configured
    configured_key = os.getenv("NIFTY_API_KEY", os.getenv("API_KEY", None))
    header_key = request.headers.get("X-API-Key", None)
    query_key = request.query_params.get("api_key", None)
    provided_key = header_key or query_key

    # Exclude public paths like docs, health, openapi
    public_paths = {"/", "/docs", "/redoc", "/openapi.json", "/api/v1/health"}
    
    if configured_key and request.url.path not in public_paths:
        if not provided_key or provided_key != configured_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "detail": "Invalid or missing API key. Provide valid X-API-Key header or ?api_key= parameter.",
                    "docs": "/docs"
                }
            )

    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    status_code = getattr(response, "status_code", 200)
    logging.info("%s %s %.2fms %s", request.method, request.url.path, elapsed_ms, status_code)
    return response


@app.get("/", tags=["root"])
def root_endpoint():
    """Root endpoint welcome & status landing page."""
    return {
        "title": "NIFTY100 Intelligence Platform API",
        "status": "online",
        "version": "sprint6-v1",
        "documentation": "/docs",
        "interactive_redoc": "/redoc",
        "health_check": "/api/v1/health",
        "endpoints": {
            "companies": "/api/v1/companies",
            "screener": "/api/v1/screener",
            "sectors": "/api/v1/sectors",
            "peers": "/api/v1/peers",
            "valuation": "/api/v1/valuation",
            "portfolio": "/api/v1/portfolio",
            "documents": "/api/v1/documents",
        },
        "message": "NIFTY100 Intelligence API active. Visit /docs for interactive OpenAPI documentation."
    }


# Register routers
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
