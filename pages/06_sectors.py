from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils import db
from dashboard.utils import theme as theme_mod


def render() -> None:
    theme_mod.render_page_header(
        "Sector Intelligence",
        "Sector Analysis",
        "",
    )
    universe = db.get_latest_universe()
    sectors = sorted(universe["broad_sector"].dropna().unique())
    if not sectors:
        st.warning("No sector data available.")
        return
    sector = st.selectbox("Sector", sectors)
    frame = universe[universe["broad_sector"] == sector].copy()
    if frame.empty:
        st.info("No companies available for this sector.")
        return
    st.caption("SIMULATED: bubble size uses market_cap data.")
    st.subheader(f"{sector}: Revenue vs ROE")
    fig = px.scatter(
        frame,
        x="sales",
        y="return_on_equity_pct",
        size="market_cap_crore",
        color="sub_sector",
        hover_name="company_name",
        hover_data=["company_id", "pe_ratio", "debt_to_equity"],
        size_max=52,
        labels={
            "sales": "Revenue (INR Crore)",
            "return_on_equity_pct": "ROE %",
            "market_cap_crore": "Market Cap (INR Crore, SIMULATED)",
            "sub_sector": "Sub-sector",
        },
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=540,
        margin=dict(l=55, r=30, t=115, b=55),
        legend=dict(
            title="Sub-sector",
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

    label_map = {
        "return_on_equity_pct": "ROE",
        "return_on_capital_employed_pct": "ROCE",
        "net_profit_margin_pct": "NPM",
        "debt_to_equity": "D/E",
        "revenue_cagr_5yr": "Rev CAGR",
        "pat_cagr_5yr": "PAT CAGR",
        "composite_quality_score": "Quality",
    }
    full_label_map = {
        "return_on_equity_pct": "Return on Equity %",
        "return_on_capital_employed_pct": "Return on Capital Employed %",
        "net_profit_margin_pct": "Net Profit Margin %",
        "debt_to_equity": "Debt to Equity",
        "revenue_cagr_5yr": "Revenue CAGR 5yr %",
        "pat_cagr_5yr": "PAT CAGR 5yr %",
        "composite_quality_score": "Composite Quality Score",
    }
    medians = (
        frame[
            list(label_map.keys())
        ]
        .median(numeric_only=True)
        .reset_index()
    )
    medians.columns = ["Metric", "Median"]
    medians["Full Metric"] = medians["Metric"].map(full_label_map)
    medians["Metric"] = medians["Metric"].map(label_map)
    medians["Label"] = medians["Median"].round(2).astype(str)
    st.subheader(f"{sector}: Median KPI Profile")
    bar = px.bar(
        medians,
        x="Metric",
        y="Median",
        text="Label",
        hover_data={"Full Metric": True, "Metric": False, "Median": ":.2f", "Label": False},
        labels={"Metric": "", "Median": "Median Value"},
    )
    bar.update_traces(textposition="outside", cliponaxis=False)
    bar.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=500,
        margin=dict(l=55, r=30, t=35, b=70),
        xaxis_tickangle=0,
        uniformtext_minsize=10,
        uniformtext_mode="show",
    )
    st.plotly_chart(bar, use_container_width=True)
