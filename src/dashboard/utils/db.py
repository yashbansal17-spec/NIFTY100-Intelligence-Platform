from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "output" / "nifty100.db"


def _query(sql: str, params: tuple = (), db_path: str | Path = DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    return _query(
        """
        SELECT c.id AS company_id, c.company_name, c.about_company, c.website,
               c.nse_profile, c.bse_profile, c.roce_percentage, c.roe_percentage,
               COALESCE(s.broad_sector, 'Unassigned') AS broad_sector,
               s.sub_sector, s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        ORDER BY c.company_name
        """
    )


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year: int | None = None) -> pd.DataFrame:
    params: tuple = (ticker.upper(),)
    year_filter = ""
    if year is not None:
        year_filter = "AND fr.fiscal_year = ?"
        params = (ticker.upper(), int(year))
    return _query(
        f"""
        SELECT fr.*, c.company_name, COALESCE(s.broad_sector, 'Unassigned') AS broad_sector,
               s.sub_sector
        FROM financial_ratios fr
        JOIN companies c ON c.id = fr.company_id
        LEFT JOIN sectors s ON s.company_id = fr.company_id
        WHERE fr.company_id = ? {year_filter}
        ORDER BY fr.fiscal_year
        """,
        params,
    )


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    return _query(
        """
        SELECT * FROM profitandloss
        WHERE company_id = ?
        ORDER BY fiscal_year
        """,
        (ticker.upper(),),
    )


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    return _query(
        """
        SELECT * FROM balancesheet
        WHERE company_id = ?
        ORDER BY fiscal_year
        """,
        (ticker.upper(),),
    )


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    return _query(
        """
        SELECT * FROM cashflow
        WHERE company_id = ?
        ORDER BY fiscal_year
        """,
        (ticker.upper(),),
    )


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    return _query(
        """
        SELECT s.*, c.company_name
        FROM sectors s
        JOIN companies c ON c.id = s.company_id
        ORDER BY s.broad_sector, c.company_name
        """
    )


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    return _query(
        """
        WITH latest_ratios AS (
          SELECT fr.*,
                 ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
          FROM financial_ratios fr
          WHERE fr.fiscal_year IS NOT NULL
        )
        SELECT pg.peer_group_name, pg.company_id, pg.is_benchmark, c.company_name,
               lr.return_on_equity_pct, lr.return_on_capital_employed_pct,
               lr.net_profit_margin_pct, lr.debt_to_equity, lr.free_cash_flow_cr,
               lr.pat_cagr_5yr, lr.revenue_cagr_5yr, lr.eps_cagr_5yr,
               lr.interest_coverage, lr.asset_turnover, lr.composite_quality_score
        FROM peer_groups pg
        JOIN companies c ON c.id = pg.company_id
        LEFT JOIN latest_ratios lr ON lr.company_id = pg.company_id AND lr.rn = 1
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, c.company_name
        """,
        (group_name,),
    )


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    path = PROJECT_ROOT / "output" / "valuation_summary.xlsx"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_excel(path)
    return frame[frame["company_id"].str.upper() == ticker.upper()].copy()


@st.cache_data(ttl=600)
def get_latest_universe() -> pd.DataFrame:
    return _query(
        """
        WITH latest_ratios AS (
          SELECT fr.*,
                 ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
          FROM financial_ratios fr
          WHERE fr.fiscal_year IS NOT NULL
        ),
        latest_market AS (
          SELECT mc.*,
                 ROW_NUMBER() OVER (PARTITION BY mc.company_id ORDER BY mc.year DESC, mc.id DESC) AS rn
          FROM market_cap mc
        ),
        latest_pl AS (
          SELECT p.*,
                 ROW_NUMBER() OVER (PARTITION BY p.company_id ORDER BY p.fiscal_year DESC, p.id DESC) AS rn
          FROM profitandloss p
          WHERE p.fiscal_year IS NOT NULL
        )
        SELECT c.id AS company_id, c.company_name, COALESCE(s.broad_sector, 'Unassigned') AS broad_sector,
               s.sub_sector, lr.fiscal_year, lr.return_on_equity_pct,
               lr.return_on_capital_employed_pct, lr.net_profit_margin_pct,
               lr.operating_profit_margin_pct, lr.debt_to_equity, lr.interest_coverage,
               lr.icr_label, lr.free_cash_flow_cr, lr.revenue_cagr_3yr, lr.revenue_cagr_5yr,
               lr.pat_cagr_5yr, lr.eps_cagr_5yr, lr.asset_turnover,
               lr.dividend_payout_ratio_pct, lr.capital_allocation_pattern,
               lr.composite_quality_score, lm.market_cap_crore, lm.pe_ratio, lm.pb_ratio,
               lm.ev_ebitda, lm.dividend_yield_pct, lp.sales, lp.net_profit
        FROM companies c
        LEFT JOIN latest_ratios lr ON lr.company_id = c.id AND lr.rn = 1
        LEFT JOIN sectors s ON s.company_id = c.id
        LEFT JOIN latest_market lm ON lm.company_id = c.id AND lm.rn = 1
        LEFT JOIN latest_pl lp ON lp.company_id = c.id AND lp.rn = 1
        ORDER BY c.company_name
        """
    )


@st.cache_data(ttl=600)
def get_year_universe(year: int) -> pd.DataFrame:
    return _query(
        """
        SELECT c.id AS company_id, c.company_name, COALESCE(s.broad_sector, 'Unassigned') AS broad_sector,
               fr.fiscal_year, fr.return_on_equity_pct, fr.return_on_capital_employed_pct,
               fr.net_profit_margin_pct, fr.operating_profit_margin_pct, fr.debt_to_equity,
               fr.free_cash_flow_cr, fr.revenue_cagr_5yr, fr.pat_cagr_5yr,
               fr.composite_quality_score, mc.pe_ratio, mc.market_cap_crore
        FROM companies c
        LEFT JOIN financial_ratios fr ON fr.company_id = c.id AND fr.fiscal_year = ?
        LEFT JOIN sectors s ON s.company_id = c.id
        LEFT JOIN market_cap mc ON mc.company_id = c.id AND mc.year = ?
        ORDER BY c.company_name
        """,
        (int(year), int(year)),
    )


@st.cache_data(ttl=600)
def get_peer_group_names() -> pd.DataFrame:
    return _query("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name")


@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    return _query(
        """
        SELECT year, annual_report
        FROM documents
        WHERE company_id = ?
        ORDER BY year DESC
        """,
        (ticker.upper(),),
    )


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str) -> pd.DataFrame:
    return _query(
        """
        SELECT pros, cons
        FROM prosandcons
        WHERE company_id = ?
        """,
        (ticker.upper(),),
    )


@st.cache_data(ttl=600)
def get_capital_allocation() -> pd.DataFrame:
    return _query(
        """
        WITH latest_ratios AS (
          SELECT company_id, capital_allocation_pattern,
                 ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY fiscal_year DESC, id DESC) AS rn
          FROM financial_ratios
          WHERE fiscal_year IS NOT NULL
        )
        SELECT c.id AS company_id, c.company_name,
               COALESCE(lr.capital_allocation_pattern, 'Unclassified') AS capital_allocation_pattern,
               COALESCE(s.broad_sector, 'Unassigned') AS broad_sector
        FROM companies c
        LEFT JOIN latest_ratios lr ON lr.company_id = c.id AND lr.rn = 1
        LEFT JOIN sectors s ON s.company_id = c.id
        ORDER BY c.company_name
        """
    )
