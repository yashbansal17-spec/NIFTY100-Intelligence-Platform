from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils import db
from dashboard.utils import theme as theme_mod
from dashboard.utils import live_data


def metric_value(value, suffix: str = "") -> str:
    if value is None or value != value:
        return "N/A"
    return f"{value:,.2f}{suffix}"


def render() -> None:
    # 1. Live Market Data Ticker
    live_df = live_data.get_cached_live_market()
    monthly_summary = live_data.get_cached_monthly_summary()
    theme_mod.render_live_ticker(live_df)

    # 2. Hero Section & Benchmark Universe
    universe = db.get_latest_universe()
    companies = db.get_companies()

    avg_roe = universe["return_on_equity_pct"].mean() if not universe.empty else None
    median_pe = universe["pe_ratio"].median() if not universe.empty else None

    theme_mod.render_hero(
        eyebrow="",
        title_lines=["NIFTY 100", "INTELLIGENCE PLATFORM"],
        subtitle="",
        stats=[
            ("Companies Tracked", f"{len(companies):,}" if not companies.empty else "—"),
            ("Avg ROE", metric_value(avg_roe, "%") if avg_roe is not None else "—"),
            ("Median P/E", metric_value(median_pe) if median_pe is not None else "—"),
            ("Market Universe", "NIFTY 100"),
        ],
    )

    # # 3. Monthly Market Update Banner
    # theme_mod.render_monthly_update_summary(monthly_summary)

    # 4. Recent Market Stats Grid
    st.markdown("###  Recent Market & Monthly Update Stats")
    m_cols = st.columns(4, gap="medium")
    
    avg_1m = monthly_summary.get("avg_1m_return", 0.0)
    m_cols[0].metric(
        "Monthly Market Return (1M)",
        f"{avg_1m:+.2f}%",
        delta=f"{monthly_summary.get('pct_advancing', 0)}% Advancing",
    )
    
    near_high_cnt = len(monthly_summary.get("near_52w_high", []))
    m_cols[1].metric(
        "Stocks Near 52W High (≤5%)",
        f"{near_high_cnt} Stocks",
        delta="Bullish Momentum",
    )
    
    top_gainer = monthly_summary.get("top_gainers")
    if top_gainer is not None and not top_gainer.empty:
        g_ticker = top_gainer.iloc[0]["company_id"]
        g_ret = top_gainer.iloc[0]["return_1m_pct"]
        m_cols[2].metric("Top Monthly Gainer", f"{g_ticker}", delta=f"+{g_ret:.2f}% 1M")
    else:
        m_cols[2].metric("Top Monthly Gainer", "N/A")

    near_low_cnt = len(monthly_summary.get("near_52w_low", []))
    m_cols[3].metric(
        "Stocks Near 52W Low (≤5%)",
        f"{near_low_cnt} Stocks",
        delta="-Value Opportunities" if near_low_cnt > 0 else "Low Risk",
        delta_color="inverse",
    )

    st.markdown('<div class="clean-rule"></div>', unsafe_allow_html=True)

    # 5. Core Market Structure & Quality Ranking
    st.markdown("###  Sector Structure & Quality Leaders")
    left, right = st.columns([1.05, 1], gap="large")

    sector_counts = companies.groupby("broad_sector", dropna=False)["company_id"].count().reset_index()
    sector_counts.columns = ["Sector", "Companies"]
    fig = px.pie(sector_counts, names="Sector", values="Companies", hole=0.48, title="Sector Breakdown")
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>%{value} companies (%{percent})<extra></extra>",
        marker=dict(line=dict(color='#05070a', width=2)),
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=25, r=25, t=50, b=30),
        legend=dict(orientation="v", y=0.5, yanchor="middle", x=1.02),
        uniformtext_minsize=11,
        uniformtext_mode="hide",
    )
    left.plotly_chart(fig, width="stretch")

    top = universe.sort_values("composite_quality_score", ascending=False).head(5)
    top = top[
        [
            "company_id",
            "company_name",
            "broad_sector",
            "return_on_equity_pct",
            "debt_to_equity",
            "composite_quality_score",
        ]
    ]
    top = top.rename(
        columns={
            "company_id": "Ticker",
            "company_name": "Company",
            "broad_sector": "Sector",
            "return_on_equity_pct": "ROE %",
            "debt_to_equity": "D/E",
            "composite_quality_score": "Quality Score",
        }
    )
    right.subheader("Top 5 Quality Score Companies")
    right.dataframe(top, width="stretch", hide_index=True)

    # 6. Monthly Updates Tabs
    st.markdown("### Recent Updates & Monthly Leaders")
    tab1, tab2, tab3 = st.tabs(["Top Gainers (1M)", "Top Losers (1M)", "Near 52-Week High"])

    with tab1:
        if top_gainer is not None and not top_gainer.empty:
            df_g = top_gainer.copy()
            df_g.columns = ["Ticker", "Company Name", "Current Price (₹)", "1-Month Return %"]
            st.dataframe(df_g, width="stretch", hide_index=True)
        else:
            st.info("No gainer data available.")

    with tab2:
        top_loser = monthly_summary.get("top_losers")
        if top_loser is not None and not top_loser.empty:
            df_l = top_loser.copy()
            df_l.columns = ["Ticker", "Company Name", "Current Price (₹)", "1-Month Return %"]
            st.dataframe(df_l, width="stretch", hide_index=True)
        else:
            st.info("No loser data available.")

    with tab3:
        near_high = monthly_summary.get("near_52w_high")
        if near_high is not None and not near_high.empty:
            df_h = near_high.copy()
            df_h.columns = ["Ticker", "Company Name", "Current Price (₹)", "52W High (₹)", "% From High"]
            st.dataframe(df_h, width="stretch", hide_index=True)
        else:
            st.info("No companies currently within 5% of 52-week high.")
