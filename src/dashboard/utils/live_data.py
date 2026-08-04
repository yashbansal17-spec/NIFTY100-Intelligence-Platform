"""
Dashboard live market data utility module.
Provides cached access to real-time market data, monthly statistics,
52-week High/Low indicators, and API connection status.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse
import requests
import streamlit as st
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
import sys
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from analytics.live_market import fetch_live_market_data, get_monthly_market_summary


@st.cache_data(ttl=900, show_spinner="Fetching latest market stats...")
def get_cached_live_market(force_refresh: bool = False) -> pd.DataFrame:
    """Cached wrapper for fetching live market quotes, 52W Highs/Lows, and 1M returns."""
    return fetch_live_market_data(force_refresh=force_refresh)


@st.cache_data(ttl=900)
def get_cached_monthly_summary() -> dict:
    """Cached summary of top gainers, losers, 52W breakouts, and market breadths."""
    df = get_cached_live_market()
    return get_monthly_market_summary(df)


def normalize_api_url(user_url: str) -> str:
    """Normalizes API base URL by stripping trailing paths like /docs, /api/v1, etc."""
    clean = user_url.strip()
    if not clean.startswith("http://") and not clean.startswith("https://"):
        clean = "http://" + clean
    parsed = urlparse(clean)
    base = f"{parsed.scheme}://{parsed.netloc}"
    return base if parsed.netloc else clean.rstrip("/")


def check_api_server_status(base_url: str = "http://localhost:8000", api_key: str | None = None) -> dict:
    """
    Pings the FastAPI server health and root endpoints with fallback handling.
    Returns connectivity status dict.
    """
    primary_base = normalize_api_url(base_url)
    
    # Generate target candidate URLs (including 127.0.0.1 fallback for localhost)
    candidates = [primary_base]
    if "localhost" in primary_base:
        candidates.append(primary_base.replace("localhost", "127.0.0.1"))
    elif "127.0.0.1" in primary_base:
        candidates.append(primary_base.replace("127.0.0.1", "localhost"))

    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    for candidate in candidates:
        # Check /api/v1/health first, then /
        for path in ["/api/v1/health", "/"]:
            target_url = f"{candidate}{path}"
            try:
                resp = requests.get(target_url, headers=headers, timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    return {
                        "online": True,
                        "status_code": 200,
                        "version": data.get("version", "sprint6-v1"),
                        "uptime": data.get("uptime_seconds", 0),
                        "url": candidate,
                        "message": f"Connected to FastAPI server at {candidate}",
                    }
            except Exception:
                continue

    return {
        "online": False,
        "status_code": None,
        "url": primary_base,
        "message": f"Cannot connect to {primary_base}",
    }
