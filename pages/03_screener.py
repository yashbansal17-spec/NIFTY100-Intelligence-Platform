from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils import db
from dashboard.utils import theme as theme_mod
from dashboard.utils import live_data

PRESETS = {
    "Quality": {"roe": 15.0, "de": 1.0, "fcf": 0.0, "rev": 10.0},
    "Value": {"pe": 20.0, "pb": 3.0, "de": 2.0, "div": 1.0},
    "Growth": {"pat": 20.0, "rev": 15.0, "de": 2.0},
    "Dividend": {"div": 2.0, "fcf": 0.0},
    "52W High Momentum": {"near_high": -10.0, "ret1m": 0.0},
    "Debt-Free": {"de": 0.01, "roe": 12.0},
}

DEFAULTS = {
    "roe": 0.0,
    "de": 10.0,
    "fcf": -50000.0,
    "rev": -50.0,
    "pat": -50.0,
    "opm": -50.0,
    "pe": 200.0,
    "pb": 50.0,
    "div": 0.0,
    "icr": -100.0,
    "ret1m": -50.0,
    "near_high": -100.0,
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(f"screener_{key}", value)


def apply_preset(preset: dict) -> None:
    for key, value in DEFAULTS.items():
        st.session_state[f"screener_{key}"] = preset.get(key, value)


def filter_universe(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result = result[result["return_on_equity_pct"].fillna(-999) >= st.session_state.screener_roe]
    result = result[(result["broad_sector"] == "Financials") | (result["debt_to_equity"].fillna(999) <= st.session_state.screener_de)]
    result = result[result["free_cash_flow_cr"].fillna(-999999) >= st.session_state.screener_fcf]
    result = result[result["revenue_cagr_5yr"].fillna(-999) >= st.session_state.screener_rev]
    result = result[result["pat_cagr_5yr"].fillna(-999) >= st.session_state.screener_pat]
    result = result[result["operating_profit_margin_pct"].fillna(-999) >= st.session_state.screener_opm]
    result = result[result["pe_ratio"].fillna(999999) <= st.session_state.screener_pe]
    result = result[result["pb_ratio"].fillna(999999) <= st.session_state.screener_pb]
    result = result[result["dividend_yield_pct"].fillna(-999) >= st.session_state.screener_div]
    
    if "return_1m_pct" in result.columns:
        result = result[result["return_1m_pct"].fillna(-999) >= st.session_state.screener_ret1m]
    if "pct_from_52w_high" in result.columns:
        result = result[result["pct_from_52w_high"].fillna(-999) >= st.session_state.screener_near_high]

    return result.sort_values("composite_quality_score", ascending=False)


def render() -> None:
    theme_mod.render_page_header(
        "Quantitative Screener",
        "Multi-Factor Screener",
        "Filter the NIFTY 100 benchmark by fundamentals, quality scores, and real-time monthly market stats & 52-week High proximity.",
    )
    init_state()

    st.sidebar.markdown("### Preset Filters")
    preset_cols = st.sidebar.columns(2)
    for idx, (name, values) in enumerate(PRESETS.items()):
        if preset_cols[idx % 2].button(name, use_container_width=True):
            apply_preset(values)

    st.sidebar.markdown("### Recent Stats & Momentum")
    st.sidebar.slider("1-Month Return % min", -50.0, 50.0, key="screener_ret1m")
    st.sidebar.slider("% From 52W High min", -100.0, 0.0, key="screener_near_high")

    st.sidebar.markdown("### Fundamental Thresholds")
    st.sidebar.slider("ROE min", -50.0, 100.0, key="screener_roe")
    st.sidebar.slider("D/E max", 0.0, 10.0, key="screener_de")
    st.sidebar.slider("FCF min", -50000.0, 50000.0, key="screener_fcf")
    st.sidebar.slider("Revenue CAGR min", -50.0, 100.0, key="screener_rev")
    st.sidebar.slider("PAT CAGR min", -50.0, 100.0, key="screener_pat")
    st.sidebar.slider("OPM min", -50.0, 100.0, key="screener_opm")
    st.sidebar.slider("P/E max", 0.0, 200.0, key="screener_pe")
    st.sidebar.slider("P/B max", 0.0, 50.0, key="screener_pb")
    st.sidebar.slider("Dividend Yield min", 0.0, 20.0, key="screener_div")

    universe = db.get_latest_universe()
    live_df = live_data.get_cached_live_market()

    if not live_df.empty:
        # Merge live market stats into universe
        live_sub = live_df[["company_id", "current_price", "high_52w", "low_52w", "return_1m_pct", "pct_from_52w_high"]]
        universe = pd.merge(universe, live_sub, on="company_id", how="left")

    filtered = filter_universe(universe)
    
    columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "current_price",
        "return_1m_pct",
        "high_52w",
        "pct_from_52w_high",
        "composite_quality_score",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pe_ratio",
    ]
    visible = filtered[[column for column in columns if column in filtered.columns]].copy()
    visible = visible.rename(
        columns={
            "company_id": "Ticker",
            "company_name": "Company",
            "broad_sector": "Sector",
            "current_price": "Price (₹)",
            "return_1m_pct": "1M Return %",
            "high_52w": "52W High (₹)",
            "pct_from_52w_high": "% From High",
            "composite_quality_score": "Quality Score",
            "return_on_equity_pct": "ROE %",
            "debt_to_equity": "D/E",
            "free_cash_flow_cr": "FCF Cr",
            "revenue_cagr_5yr": "Rev CAGR 5yr %",
            "pe_ratio": "P/E",
        }
    )

    st.markdown('<div class="clean-rule"></div>', unsafe_allow_html=True)
    count_col, download_col = st.columns([3, 1], gap="large")
    count_col.subheader(f"{len(visible)} Companies Match Criteria")
    download_col.download_button(
        "Download Results CSV",
        visible.to_csv(index=False).encode("utf-8"),
        file_name="screener_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.dataframe(visible, use_container_width=True, hide_index=True, height=560)
