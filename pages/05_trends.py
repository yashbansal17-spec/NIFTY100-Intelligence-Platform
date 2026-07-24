from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils import db
from dashboard.utils import theme as theme_mod


METRICS = {
    "Revenue": ("pl", "sales"),
    "Net Profit": ("pl", "net_profit"),
    "ROE": ("ratios", "return_on_equity_pct"),
    "ROCE": ("ratios", "return_on_capital_employed_pct"),
    "Debt to Equity": ("ratios", "debt_to_equity"),
    "Free Cash Flow": ("ratios", "free_cash_flow_cr"),
    "Revenue CAGR 5yr": ("ratios", "revenue_cagr_5yr"),
    "Composite Score": ("ratios", "composite_quality_score"),
}


def pick_company() -> str | None:
    companies = db.get_companies()
    if companies.empty:
        st.info("No companies available.")
        return None
    selected = st.selectbox("Search company or ticker", [f"{row.company_id} - {row.company_name}" for row in companies.itertuples()])
    return selected.split(" - ")[0]


def render() -> None:
    theme_mod.render_page_header(
        "Historical Trends",
        "Trend Analysis",
        "Overlay up to three metrics for any listed NIFTY100 company.",
    )
    ticker = pick_company()
    if not ticker:
        return
    selected_metrics = st.multiselect("Overlay up to 3 metrics", list(METRICS.keys()), default=["Revenue", "Net Profit"], max_selections=3)
    if not selected_metrics:
        st.info("Choose at least one metric.")
        return
    ratios = db.get_ratios(ticker).tail(10)
    pl = db.get_pl(ticker).tail(10)
    if len(ratios) < 10 or len(pl) < 10:
        st.caption("Data available note: this company has partial history, so the chart uses all available years.")

    fig = go.Figure()
    for metric in selected_metrics:
        source, column = METRICS[metric]
        frame = pl if source == "pl" else ratios
        if column not in frame.columns:
            continue
        values = frame[column]
        yoy = values.pct_change() * 100
        fig.add_trace(
            go.Scatter(
                x=frame["fiscal_year"],
                y=values,
                customdata=yoy,
                mode="lines+markers",
                name=metric,
                hovertemplate="Year %{x}<br>Value %{y:,.2f}<br>YoY %{customdata:+.1f}%<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_layout(
        title=f"{ticker} 10-Year Trend",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=560,
        margin=dict(l=50, r=30, t=70, b=55),
        xaxis_title="Fiscal Year",
        yaxis_title="Selected Metric Value",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
