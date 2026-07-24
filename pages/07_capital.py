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
        "Capital Deployment",
        "Capital Allocation Map",
        "View how companies are classified by their latest capital allocation pattern.",
    )
    frame = db.get_capital_allocation()
    if frame.empty:
        st.warning("No capital allocation data available.")
        return

    patterns = sorted(frame["capital_allocation_pattern"].dropna().unique())
    selected = st.selectbox("Focus pattern", ["All patterns"] + patterns)
    focused = frame if selected == "All patterns" else frame[frame["capital_allocation_pattern"] == selected]
    table_source = focused.sort_values(["capital_allocation_pattern", "company_name"]).drop_duplicates(
        subset=["company_id"],
        keep="first",
    )

    metric_cols = st.columns(5, gap="medium")
    metric_cols[0].metric("Companies", f"{len(table_source):,}")
    metric_cols[1].metric("Rows in Table", f"{len(table_source):,}")
    metric_cols[2].metric("Patterns", f"{frame['capital_allocation_pattern'].nunique():,}")
    metric_cols[3].metric("Sectors", f"{table_source['broad_sector'].nunique():,}")
    top_pattern = frame["capital_allocation_pattern"].mode().iloc[0] if not frame.empty else "N/A"
    metric_cols[4].metric("Largest Pattern", top_pattern)

    summary = table_source.groupby(["capital_allocation_pattern", "broad_sector"], dropna=False).size().reset_index(name="companies")
    fig = px.treemap(
        summary,
        path=["capital_allocation_pattern", "broad_sector"],
        values="companies",
        color="capital_allocation_pattern",
        title="Company Count by Capital Allocation Pattern and Sector",
        labels={"companies": "Companies", "capital_allocation_pattern": "Pattern", "broad_sector": "Sector"},
    )
    fig.update_traces(textinfo="label+value", hovertemplate="<b>%{label}</b><br>%{value} companies<extra></extra>")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=620,
        margin=dict(l=20, r=20, t=70, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    table = table_source[["company_id", "company_name", "capital_allocation_pattern", "broad_sector"]].rename(
        columns={
            "company_id": "Ticker",
            "company_name": "Company",
            "capital_allocation_pattern": "Pattern",
            "broad_sector": "Sector",
        }
    )
    st.subheader("Companies in Current View")
    table_height = min(560, max(120, 38 * (len(table) + 1)))
    st.dataframe(table, use_container_width=True, hide_index=True, height=table_height)
