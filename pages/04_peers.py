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
    "ROE": "return_on_equity_pct",
    "ROCE": "return_on_capital_employed_pct",
    "NPM": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
    "PAT CAGR": "pat_cagr_5yr",
    "Revenue CAGR": "revenue_cagr_5yr",
    "Composite": "composite_quality_score",
}


def style_benchmark(row):
    is_benchmark = row.get("Benchmark") == 1 or row.get("is_benchmark") == 1
    return [
        "background-color: rgba(16, 185, 129, 0.14); color: #ffffff;" if is_benchmark else ""
        for _ in row
    ]


def render() -> None:
    theme_mod.render_page_header(
        "Peer Benchmarking",
        "Peer Comparison",
        "",
    )
    groups = db.get_peer_group_names()["peer_group_name"].tolist()
    if not groups:
        st.warning("No peer groups available.")
        return
    group = st.selectbox("Peer group", groups, help=f"{len(groups)} peer groups loaded")
    peers = db.get_peers(group)
    if peers.empty:
        st.info("No companies available for this peer group.")
        return
    display_peers = peers.sort_values(["is_benchmark", "company_name"], ascending=[False, True]).drop_duplicates(
        subset=["company_id"],
        keep="first",
    )
    st.markdown('<div class="clean-rule"></div>', unsafe_allow_html=True)

    theme_mod.render_kpi_row(
        [
            {"title": "Peer Groups", "value": f"{len(groups):,}"},
            {"title": "Companies in Group", "value": f"{len(display_peers):,}"},
            {"title": "Rows in Table", "value": f"{len(display_peers):,}"},
            {"title": "Benchmarks", "value": f"{int(display_peers['is_benchmark'].fillna(0).sum()):,}"},
        ]
    )

    st.markdown('<div style="margin-top:1.2rem;"></div>', unsafe_allow_html=True)
    selected_label = st.selectbox(
        "Company in selected peer group",
        [f"{row.company_id} - {row.company_name}" for row in display_peers.itertuples()],
    )
    selected_id = selected_label.split(" - ")[0]
    selected = display_peers[display_peers["company_id"] == selected_id].iloc[0]
    avg = display_peers[list(METRICS.values())].mean(numeric_only=True)

    theta = list(METRICS.keys())
    company_values = [selected[column] if selected[column] == selected[column] else 0 for column in METRICS.values()]
    avg_values = [avg[column] if avg[column] == avg[column] else 0 for column in METRICS.values()]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=company_values,
            theta=theta,
            fill="toself",
            name=selected_id,
            line=dict(color=theme_mod.ACCENT, width=2.5),
            fillcolor="rgba(16, 185, 129, 0.22)",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=avg_values,
            theta=theta,
            name=f"{group} average",
            line=dict(color=theme_mod.ACCENT_2, width=2, dash="dash"),
            fillcolor="rgba(16, 185, 129, 0.08)",
        )
    )
    fig.update_layout(
        title=f"{selected_id} vs {group} Average",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, gridcolor=theme_mod.GRID, linecolor=theme_mod.LINE),
            angularaxis=dict(tickfont=dict(size=12, family=theme_mod.FONT_UI, color=theme_mod.MUTED), gridcolor=theme_mod.GRID),
        ),
    )
    theme_mod.style_plotly_chart(fig, height=560)
    st.plotly_chart(fig, width="stretch")

    display_cols = ["company_id", "company_name", "is_benchmark"] + list(METRICS.values())
    display = display_peers[display_cols].rename(
        columns={
            "company_id": "Ticker",
            "company_name": "Company",
            "is_benchmark": "Benchmark",
            "return_on_equity_pct": "ROE %",
            "return_on_capital_employed_pct": "ROCE %",
            "net_profit_margin_pct": "NPM %",
            "debt_to_equity": "D/E",
            "free_cash_flow_cr": "FCF Cr",
            "pat_cagr_5yr": "PAT CAGR %",
            "revenue_cagr_5yr": "Revenue CAGR %",
            "composite_quality_score": "Composite",
        }
    )
    table_height = min(520, max(120, 38 * (len(display) + 1)))
    st.dataframe(
        display.style.apply(style_benchmark, axis=1).format(
            {
                "ROE %": "{:.2f}",
                "ROCE %": "{:.2f}",
                "NPM %": "{:.2f}",
                "D/E": "{:.2f}",
                "FCF Cr": "{:.1f}",
                "PAT CAGR %": "{:.2f}",
                "Revenue CAGR %": "{:.2f}",
                "Composite": "{:.1f}",
            },
            na_rep="N/A",
        ),
        width="stretch",
        hide_index=True,
        height=table_height,
    )
