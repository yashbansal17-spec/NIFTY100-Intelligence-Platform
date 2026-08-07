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
        "",
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

    # ---------------- Executive Header ----------------
    c_live = live_df[live_df["company_id"] == ticker] if not live_df.empty else None

    head_left, head_right = st.columns([2, 1.2])
    with head_left:
        st.subheader(f"{company['company_id']} — {company['company_name']}")
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
            badge_html = theme_mod.badge(ret1m, suffix="% (1M)")

            st.markdown(
                f"""
                <div class="kpi-card" style="text-align:right;">
                    <div class="kpi-title">Current Live Quote</div>
                    <div class="kpi-value" style="font-size:1.9rem;">₹{cp:,.2f}</div>
                    <div style="margin-top:6px;">{badge_html}</div>
                    <div style="margin-top:12px;">
                        {theme_mod.range_bar(cp, l52, h52, f"₹{l52:,.0f}", f"₹{h52:,.0f}")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="clean-rule"></div>', unsafe_allow_html=True)
    st.write(company.get("about_company") or "No company description available.")

    # ---------------- Key Ratios Strip ----------------
    latest = ratios.sort_values("fiscal_year").tail(1)
    latest_row = latest.iloc[0] if not latest.empty else {}

    theme_mod.render_kpi_row(
        [
            {"title": "ROE", "value": fmt(latest_row.get("return_on_equity_pct"), "%")},
            {"title": "ROCE", "value": fmt(latest_row.get("return_on_capital_employed_pct"), "%")},
            {"title": "Net Profit Margin", "value": fmt(latest_row.get("net_profit_margin_pct"), "%")},
            {"title": "D/E", "value": fmt(latest_row.get("debt_to_equity"))},
            {"title": "Revenue CAGR 5yr", "value": fmt(latest_row.get("revenue_cagr_5yr"), "%")},
            {"title": "FCF (Cr)", "value": fmt(latest_row.get("free_cash_flow_cr"))},
        ]
    )

    st.markdown('<div style="margin-top:1.4rem;"></div>', unsafe_allow_html=True)

    # ---------------- 10-Year Revenue vs Net Profit (area gradient, dual) ----------------
    chart_pl = pl.tail(10)
    bar = go.Figure()
    bar.add_trace(
        go.Scatter(
            x=chart_pl["fiscal_year"],
            y=chart_pl["sales"],
            name="Revenue",
            mode="lines",
            line=dict(color=theme_mod.ACCENT, width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.18)",
        )
    )
    bar.add_trace(
        go.Scatter(
            x=chart_pl["fiscal_year"],
            y=chart_pl["net_profit"],
            name="Net Profit",
            mode="lines",
            line=dict(color=theme_mod.ACCENT_2, width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.15)",
        )
    )
    bar.update_layout(title="10-Year Revenue and Net Profit History (INR Crore)", xaxis_title="Fiscal Year", yaxis_title="INR Crore")
    theme_mod.style_plotly_chart(bar, height=420)
    st.plotly_chart(bar, width="stretch")

    # ---------------- 10-Year ROE / ROCE Line Chart (smooth splines, secondary axis) ----------------
    chart_ratios = ratios.tail(10)
    line = make_subplots(specs=[[{"secondary_y": True}]])
    line.add_trace(
        go.Scatter(
            x=chart_ratios["fiscal_year"],
            y=chart_ratios["return_on_equity_pct"],
            name="ROE %",
            line=dict(color=theme_mod.ACCENT, width=3, shape="spline"),
        ),
        secondary_y=False,
    )
    line.add_trace(
        go.Scatter(
            x=chart_ratios["fiscal_year"],
            y=chart_ratios["return_on_capital_employed_pct"],
            name="ROCE %",
            line=dict(color=theme_mod.WARNING, width=3, dash="dot", shape="spline"),
        ),
        secondary_y=True,
    )
    line.update_layout(title="ROE & ROCE Return Trends (%)")
    theme_mod.style_plotly_chart(line, height=420)
    line.update_xaxes(title_text="Fiscal Year")
    line.update_yaxes(title_text="ROE %", secondary_y=False, gridcolor=theme_mod.GRID)
    line.update_yaxes(title_text="ROCE %", secondary_y=True, showgrid=False)
    st.plotly_chart(line, width="stretch")
