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
    return ["background-color: #5b4a14" if is_benchmark else "" for _ in row]


def render() -> None:
    theme_mod.render_page_header(
        "Peer Benchmarking",
        "Peer Comparison",
        "Choose any peer group, then compare all companies assigned to that group.",
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
    summary_cols = st.columns(4, gap="medium")
    summary_cols[0].metric("Peer Groups", f"{len(groups):,}")
    summary_cols[1].metric("Companies in Group", f"{len(display_peers):,}")
    summary_cols[2].metric("Rows in Table", f"{len(display_peers):,}")
    summary_cols[3].metric("Benchmarks", f"{int(display_peers['is_benchmark'].fillna(0).sum()):,}")
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
    fig.add_trace(go.Scatterpolar(r=company_values, theta=theta, fill="toself", name=selected_id))
    fig.add_trace(go.Scatterpolar(r=avg_values, theta=theta, name=f"{group} average", line=dict(dash="dash")))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=560,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        polar=dict(radialaxis=dict(visible=True), angularaxis=dict(tickfont=dict(size=12))),
        title=f"{selected_id} vs {group} Average",
    )
    st.plotly_chart(fig, use_container_width=True)

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
    st.dataframe(display.style.apply(style_benchmark, axis=1), use_container_width=True, hide_index=True, height=table_height)
