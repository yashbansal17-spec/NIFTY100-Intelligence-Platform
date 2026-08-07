from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
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

    st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)

    # 3. Glassmorphic KPI Cards (HTML, not st.metric)
    avg_1m = monthly_summary.get("avg_1m_return", 0.0)
    pct_adv = monthly_summary.get("pct_advancing", 0.0)
    near_high_cnt = len(monthly_summary.get("near_52w_high", []))
    near_low_cnt = len(monthly_summary.get("near_52w_low", []))
    top_gainer = monthly_summary.get("top_gainers")

    if top_gainer is not None and not top_gainer.empty:
        g_ticker = top_gainer.iloc[0]["company_id"]
        g_ret = top_gainer.iloc[0]["return_1m_pct"]
        gainer_value = g_ticker
        gainer_delta = f"+{g_ret:.2f}% 1M"
    else:
        gainer_value = "N/A"
        gainer_delta = None

    st.markdown("###  Recent Market & Monthly Update Stats")
    theme_mod.render_kpi_row(
        [
            {
                "title": "Monthly Market Return (1M)",
                "value": f"{avg_1m:+.2f}%",
                "delta": f"{pct_adv}% Advancing",
                "positive": avg_1m >= 0,
            },
            {
                "title": "Stocks Near 52W High (≤5%)",
                "value": f"{near_high_cnt}",
                "delta": "Bullish Momentum",
                "positive": True,
            },
            {
                "title": "Top Monthly Gainer",
                "value": gainer_value,
                "delta": gainer_delta,
                "positive": True if gainer_delta else None,
            },
            {
                "title": "Stocks Near 52W Low (≤5%)",
                "value": f"{near_low_cnt}",
                "delta": "-Value Opportunities" if near_low_cnt > 0 else "Low Risk",
                "positive": False if near_low_cnt > 0 else True,
            },
        ]
    )

    st.markdown('<div class="clean-rule"></div>', unsafe_allow_html=True)

    # 4. Core Market Structure & Quality Ranking
    st.markdown("###  Sector Structure & Quality Leaders")
    left, right = st.columns([1.05, 1], gap="large")

    sector_counts = companies.groupby("broad_sector", dropna=False)["company_id"].count().reset_index()
    sector_counts.columns = ["Sector", "Companies"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=sector_counts["Sector"],
                values=sector_counts["Companies"],
                hole=0.65,
                textposition="outside",
                textinfo="percent",
                marker=dict(
                    colors=theme_mod.PLOTLY_SEQUENCE,
                    line=dict(color=theme_mod.BG, width=2),
                ),
                hovertemplate="<b>%{label}</b><br>%{value} companies (%{percent})<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Sector Breakdown",
        annotations=[
            dict(
                text=f"{len(companies):,}<br><span style='font-size:11px;color:#8B98AC'>Companies</span>",
                x=0.5,
                y=0.5,
                font=dict(size=22, color="#ffffff", family=theme_mod.FONT_MONO),
                showarrow=False,
            )
        ],
        showlegend=True,
    )
    theme_mod.style_plotly_chart(fig, height=400)
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
    ].copy()
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
    right.dataframe(
        top,
        width="stretch",
        hide_index=True,
        column_config={
            "Quality Score": st.column_config.ProgressColumn(
                "Quality Score",
                help="Composite quality score (0-100)",
                format="%.1f",
                min_value=0,
                max_value=100,
            ),
            "ROE %": st.column_config.NumberColumn("ROE %", format="%.2f%%"),
            "D/E": st.column_config.NumberColumn("D/E", format="%.2f"),
        },
    )

    # 5. Monthly Updates Tabs
    st.markdown("### Recent Updates & Monthly Leaders")
    tab1, tab2, tab3 = st.tabs(["Top Gainers (1M)", "Top Losers (1M)", "Near 52-Week High"])

    with tab1:
        if top_gainer is not None and not top_gainer.empty:
            df_g = top_gainer.copy()
            df_g.columns = ["Ticker", "Company Name", "Current Price (₹)", "1-Month Return %"]
            st.dataframe(
                df_g,
                width="stretch",
                hide_index=True,
                column_config={
                    "Current Price (₹)": st.column_config.NumberColumn("Current Price (₹)", format="₹%.2f"),
                    "1-Month Return %": st.column_config.NumberColumn("1-Month Return %", format="%.2f%%"),
                },
            )
        else:
            st.info("No gainer data available.")

    with tab2:
        top_loser = monthly_summary.get("top_losers")
        if top_loser is not None and not top_loser.empty:
            df_l = top_loser.copy()
            df_l.columns = ["Ticker", "Company Name", "Current Price (₹)", "1-Month Return %"]
            st.dataframe(
                df_l,
                width="stretch",
                hide_index=True,
                column_config={
                    "Current Price (₹)": st.column_config.NumberColumn("Current Price (₹)", format="₹%.2f"),
                    "1-Month Return %": st.column_config.NumberColumn("1-Month Return %", format="%.2f%%"),
                },
            )
        else:
            st.info("No loser data available.")

    with tab3:
        near_high = monthly_summary.get("near_52w_high")
        if near_high is not None and not near_high.empty:
            df_h = near_high.copy()
            df_h.columns = ["Ticker", "Company Name", "Current Price (₹)", "52W High (₹)", "% From High"]
            st.dataframe(
                df_h,
                width="stretch",
                hide_index=True,
                column_config={
                    "Current Price (₹)": st.column_config.NumberColumn("Current Price (₹)", format="₹%.2f"),
                    "52W High (₹)": st.column_config.NumberColumn("52W High (₹)", format="₹%.2f"),
                    "% From High": st.column_config.NumberColumn("% From High", format="%.2f%%"),
                },
            )
        else:
            st.info("No companies currently within 5% of 52-week high.")
