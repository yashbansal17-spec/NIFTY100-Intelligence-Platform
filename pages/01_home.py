from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils import db
from dashboard.utils import theme as theme_mod


def metric_value(value, suffix: str = "") -> str:
    if value is None or value != value:
        return "N/A"
    return f"{value:,.2f}{suffix}"


def render() -> None:
    year = st.sidebar.selectbox("Analysis year", list(range(2019, 2025)), index=5)
    universe = db.get_year_universe(year)
    companies = db.get_companies()

    avg_roe = universe["return_on_equity_pct"].mean() if not universe.empty else None
    median_pe = universe["pe_ratio"].median() if not universe.empty else None

    theme_mod.render_hero(
        eyebrow="",
        title_lines=["NIFTY 100", "INTELLIGENCE PLATFORM"],
        subtitle=(
            "A full-universe view of quality, valuation, leverage, growth, and sector "
            f"composition across India's benchmark 100 &mdash; live for FY{year}."
        ),
        stats=[
            ("Companies Tracked", f"{len(companies):,}" if not companies.empty else "—"),
            ("Avg ROE", metric_value(avg_roe, "%") if avg_roe is not None else "—"),
            ("Median P/E", metric_value(median_pe) if median_pe is not None else "—"),
            ("Analysis Year", f"FY{year}"),
        ],
    )

    if universe.empty:
        st.warning("No data available for the selected year.")
        return

    st.caption("SIMULATED: valuation metrics derived from market_cap; stock price history is simulated where shown.")
    st.markdown("### Market Snapshot")
    cols = st.columns(6, gap="medium")
    cols[0].metric("Average ROE", metric_value(universe["return_on_equity_pct"].mean(), "%"))
    cols[1].metric("Median P/E", metric_value(universe["pe_ratio"].median()))
    cols[2].metric("Median D/E", metric_value(universe["debt_to_equity"].median()))
    cols[3].metric("Total Companies", f"{len(companies):,}")
    cols[4].metric("Median Revenue CAGR 5yr", metric_value(universe["revenue_cagr_5yr"].median(), "%"))
    debt_free = int((universe["debt_to_equity"].fillna(999) <= 0.01).sum())
    cols[5].metric("Debt-Free Companies", f"{debt_free:,}")

    st.markdown("### Market Structure")
    left, right = st.columns([1.05, 1], gap="large")
    sector_counts = companies.groupby("broad_sector", dropna=False)["company_id"].count().reset_index()
    sector_counts.columns = ["Sector", "Companies"]
    fig = px.pie(sector_counts, names="Sector", values="Companies", hole=0.45, title="Sector Breakdown")
    fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}<br>%{value} companies<extra></extra>")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=420,
        margin=dict(l=20, r=20, t=60, b=45),
        legend=dict(orientation="v", y=0.5, yanchor="middle", x=1.02),
        uniformtext_minsize=11,
        uniformtext_mode="hide",
    )
    left.plotly_chart(fig, use_container_width=True)

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
    right.subheader("Top 5 by Composite Quality")
    right.dataframe(top, use_container_width=True, hide_index=True)

    st.markdown("### Universe Snapshot")
    sector_quality = (
        universe.groupby("broad_sector", dropna=False)
        .agg(
            Companies=("company_id", "count"),
            Median_ROE=("return_on_equity_pct", "median"),
            Median_PE=("pe_ratio", "median"),
            Median_DE=("debt_to_equity", "median"),
            Median_Quality=("composite_quality_score", "median"),
        )
        .reset_index()
        .rename(columns={"broad_sector": "Sector"})
        .sort_values("Companies", ascending=False)
    )
    st.dataframe(sector_quality, use_container_width=True, hide_index=True)
