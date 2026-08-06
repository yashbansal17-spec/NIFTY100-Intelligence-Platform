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
from dashboard.utils import live_data


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
        "Select any NIFTY 100 benchmark company to inspect its real-time market stats, 52-week range, and 10-year financial trend.",
    )

    live_df = live_data.get_cached_live_market()
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
    
    # Header with live price and 52W metrics
    c_live = live_df[live_df["company_id"] == ticker] if not live_df.empty else None
    
    head_left, head_right = st.columns([2, 1])
    with head_left:
        st.subheader(f"{company['company_id']} - {company['company_name']}")
        meta_cols = st.columns([1, 1, 2], gap="medium")
        meta_cols[0].markdown(f"**Sector**  \n{company['broad_sector']}")
        meta_cols[1].markdown(f"**Sub-sector**  \n{company.get('sub_sector') or 'N/A'}")
        meta_cols[2].markdown(f"**Website**  \n{company.get('website') or 'N/A'}")
    
    with head_right:
        if c_live is not None and not c_live.empty:
            l_row = c_live.iloc[0]
            cp = l_row["current_price"]
            ret1m = l_row["return_1m_pct"]
            h52 = l_row["high_52w"]
            l52 = l_row["low_52w"]
            sign = "+" if ret1m >= 0 else ""
            badge_cls = "badge-pos" if ret1m >= 0 else "badge-neg"

            st.markdown(
                f"""
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(0, 230, 118, 0.25); border-radius: 12px; padding: 1rem; text-align: right;">
                    <div style="font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; color: var(--muted); text-transform: uppercase;">Current Live Quote</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #ffffff;">₹{cp:,.2f}</div>
                    <div style="margin-top: 4px;">
                        <span class="{badge_cls}">{sign}{ret1m:.2f}% (1M)</span>
                    </div>
                    <div style="font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; color: var(--muted); margin-top: 8px;">
                        52W High: ₹{h52:,.2f} &middot; 52W Low: ₹{l52:,.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write(company.get("about_company") or "No company description available.")

    latest = ratios.sort_values("fiscal_year").tail(1)
    latest_row = latest.iloc[0] if not latest.empty else {}
    cols = st.columns(6, gap="medium")
    cols[0].metric("ROE", fmt(latest_row.get("return_on_equity_pct"), "%"))
    cols[1].metric("ROCE", fmt(latest_row.get("return_on_capital_employed_pct"), "%"))
    cols[2].metric("Net Profit Margin", fmt(latest_row.get("net_profit_margin_pct"), "%"))
    cols[3].metric("D/E", fmt(latest_row.get("debt_to_equity")))
    cols[4].metric("Revenue CAGR 5yr", fmt(latest_row.get("revenue_cagr_5yr"), "%"))
    cols[5].metric("FCF (Cr)", fmt(latest_row.get("free_cash_flow_cr")))

    # 10-Year P&L Bar Chart
    chart_pl = pl.tail(10)
    bar = go.Figure()
    bar.add_bar(x=chart_pl["fiscal_year"], y=chart_pl["sales"], name="Revenue", marker_color="#00e676")
    bar.add_bar(x=chart_pl["fiscal_year"], y=chart_pl["net_profit"], name="Net Profit", marker_color="#38bdf8")
    bar.update_layout(
        title="10-Year Revenue and Net Profit History (INR Crore)",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        barmode="group",
        height=420,
        margin=dict(l=40, r=20, t=60, b=50),
        xaxis_title="Fiscal Year",
        yaxis_title="INR Crore",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(bar, width="stretch")

    # 10-Year ROE / ROCE Line Chart
    chart_ratios = ratios.tail(10)
    line = make_subplots(specs=[[{"secondary_y": True}]])
    line.add_trace(go.Scatter(x=chart_ratios["fiscal_year"], y=chart_ratios["return_on_equity_pct"], name="ROE %", line=dict(color="#00e676", width=3)), secondary_y=False)
    line.add_trace(go.Scatter(x=chart_ratios["fiscal_year"], y=chart_ratios["return_on_capital_employed_pct"], name="ROCE %", line=dict(color="#f43f5e", width=3, dash="dot")), secondary_y=True)
    line.update_layout(
        title="ROE & ROCE Return Trends (%)",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=420,
        margin=dict(l=40, r=50, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    line.update_xaxes(title_text="Fiscal Year")
    line.update_yaxes(title_text="ROE %", secondary_y=False)
    line.update_yaxes(title_text="ROCE %", secondary_y=True)
    st.plotly_chart(line, width="stretch")
