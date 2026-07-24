from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils import db
from dashboard.utils import theme as theme_mod


def fmt(value, suffix: str = "") -> str:
    if value is None or value != value:
        return "N/A"
    return f"{value:,.2f}{suffix}"


def company_picker(label: str = "Search company or ticker") -> str | None:
    companies = db.get_companies()
    options = [f"{row.company_id} - {row.company_name}" for row in companies.itertuples()]
    if not options:
        st.info("No companies available.")
        return None
    selected = st.selectbox(label, options, index=0)
    return selected.split(" - ")[0]


def render() -> None:
    theme_mod.render_page_header(
        "Company Intelligence",
        "Company Profile",
        "Select any NIFTY100 company and inspect its latest fundamentals and 10-year trend.",
    )
    ticker = company_picker()
    if not ticker:
        return
    companies = db.get_companies()
    row = companies[companies["company_id"] == ticker]
    if row.empty:
        st.info("Ticker not found - please try another")
        return
    company = row.iloc[0]
    ratios = db.get_ratios(ticker)
    pl = db.get_pl(ticker)

    st.markdown('<div class="clean-rule"></div>', unsafe_allow_html=True)
    st.subheader(f"{company['company_id']} - {company['company_name']}")
    meta_cols = st.columns([1, 1, 2], gap="medium")
    meta_cols[0].markdown(f"**Sector**  \n{company['broad_sector']}")
    meta_cols[1].markdown(f"**Sub-sector**  \n{company.get('sub_sector') or 'N/A'}")
    meta_cols[2].markdown(f"**Website**  \n{company.get('website') or 'N/A'}")
    st.write(company.get("about_company") or "No company description available.")

    latest = ratios.sort_values("fiscal_year").tail(1)
    latest_row = latest.iloc[0] if not latest.empty else {}
    cols = st.columns(6, gap="medium")
    cols[0].metric("ROE", fmt(latest_row.get("return_on_equity_pct"), "%"))
    cols[1].metric("ROCE", fmt(latest_row.get("return_on_capital_employed_pct"), "%"))
    cols[2].metric("Net Profit Margin", fmt(latest_row.get("net_profit_margin_pct"), "%"))
    cols[3].metric("D/E", fmt(latest_row.get("debt_to_equity")))
    cols[4].metric("Revenue CAGR 5yr", fmt(latest_row.get("revenue_cagr_5yr"), "%"))
    cols[5].metric("FCF", fmt(latest_row.get("free_cash_flow_cr")))

    if len(pl) < 10:
        st.caption("Data available note: this company has fewer than 10 years of profit and loss history in the current dataset.")
    chart_pl = pl.tail(10)
    bar = go.Figure()
    bar.add_bar(x=chart_pl["fiscal_year"], y=chart_pl["sales"], name="Revenue")
    bar.add_bar(x=chart_pl["fiscal_year"], y=chart_pl["net_profit"], name="Net Profit")
    bar.update_layout(
        title="10-Year Revenue and Net Profit",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        barmode="group",
        height=460,
        margin=dict(l=40, r=20, t=60, b=50),
        xaxis_title="Fiscal Year",
        yaxis_title="INR Crore",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(bar, use_container_width=True)

    chart_ratios = ratios.tail(10)
    line = make_subplots(specs=[[{"secondary_y": True}]])
    line.add_trace(go.Scatter(x=chart_ratios["fiscal_year"], y=chart_ratios["return_on_equity_pct"], name="ROE"), secondary_y=False)
    line.add_trace(go.Scatter(x=chart_ratios["fiscal_year"], y=chart_ratios["return_on_capital_employed_pct"], name="ROCE"), secondary_y=True)
    line.update_layout(
        title="ROE and ROCE Trend",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=460,
        margin=dict(l=40, r=50, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    line.update_xaxes(title_text="Fiscal Year")
    line.update_yaxes(title_text="ROE %", secondary_y=False)
    line.update_yaxes(title_text="ROCE %", secondary_y=True)
    st.plotly_chart(line, use_container_width=True)
