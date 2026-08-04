from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "output" / "nifty100.db"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils import db
from dashboard.utils import theme as theme_mod


def load_companies() -> pd.DataFrame:
    companies = db.get_companies()
    if companies.empty:
        return pd.DataFrame(columns=["company_id", "company_name", "broad_sector"])
    return companies.sort_values(["company_id", "company_name"]).reset_index(drop=True)


def select_company(companies: pd.DataFrame) -> str | None:
    if companies.empty:
        st.info("Ticker not found - please try another")
        return None
    labels = [f"{row.company_id} - {row.company_name}" for row in companies.itertuples()]
    selected = st.selectbox(
        "Search company or ticker",
        labels,
        index=0,
        placeholder="Type ticker or company name",
        help="Start typing inside this dropdown to search by ticker or company name.",
    )
    return selected.split(" - ", 1)[0]


def get_company_name(companies: pd.DataFrame, ticker: str) -> str:
    row = companies[companies["company_id"] == ticker]
    if row.empty:
        return ticker
    return str(row.iloc[0]["company_name"])


def get_annual_reports(ticker: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(
            """
            SELECT year, annual_report
            FROM documents
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            conn,
            params=(ticker.upper(),),
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def report_status(url: str) -> str:
    if not url or not str(url).strip():
        return "unavailable"
    return "available"


def render_selected_report(year: int, url: str) -> None:
    st.markdown('<div class="clean-rule"></div>', unsafe_allow_html=True)
    detail_cols = st.columns([1, 1, 2], gap="large")
    detail_cols[0].metric("Selected Year", str(year))
    status = report_status(url)
    detail_cols[1].metric("Status", "Available" if status == "available" else "Unavailable")
    if url and str(url).strip():
        detail_cols[2].link_button("Open Annual Report PDF ↗", url, use_container_width=True)
        st.markdown("**BSE PDF URL**")
        st.code(url, language=None)
    else:
        detail_cols[2].button("No PDF URL in Database", disabled=True, use_container_width=True)
        st.info("No BSE annual report URL is stored for this selected year.")


def render() -> None:
    theme_mod.render_page_header(
        "Document Repository",
        "Annual Reports",
        "Select any NIFTY 100 company and open stored BSE annual report PDF links.",
    )
    if st.button("Refresh Report Links"):
        st.cache_data.clear()
        st.rerun()

    companies = load_companies()
    ticker = select_company(companies)
    if not ticker:
        return

    reports = get_annual_reports(ticker)
    company_name = get_company_name(companies, ticker)
    st.subheader(f"{ticker} Annual Reports")
    st.caption(company_name)

    if reports.empty:
        st.info("No annual report links available for this company.")
        return

    year_options = [int(year) for year in reports["year"].dropna().astype(int).tolist()]
    selected_year = st.selectbox("Select report year", year_options, index=0)
    selected_report = reports[reports["year"].astype(int) == int(selected_year)].iloc[0]
    render_selected_report(int(selected_report["year"]), str(selected_report["annual_report"] or ""))

    with st.expander("View all stored report years", expanded=False):
        display = reports.copy()
        display["status"] = display["annual_report"].apply(lambda value: "Available" if str(value or "").strip() else "Missing")
        display = display.rename(columns={"year": "Year", "annual_report": "BSE PDF URL", "status": "Status"})
        table_height = min(360, max(120, 35 * (len(display) + 1)))
        st.dataframe(display, use_container_width=True, hide_index=True, height=table_height)
