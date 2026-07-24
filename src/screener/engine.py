from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


FILTERABLE_METRICS = [
    "roe_min",
    "de_max",
    "fcf_min",
    "revenue_cagr_5yr_min",
    "pat_cagr_5yr_min",
    "opm_min",
    "pe_max",
    "pb_max",
    "dividend_yield_min",
    "icr_min",
    "market_cap_min",
    "net_profit_min",
    "eps_cagr_min",
    "asset_turnover_min",
    "sales_min",
]


def load_screener_config(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_latest_universe(db_path: str | Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    query = """
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
    market_screen AS (
      SELECT company_id,
             MIN(pe_ratio) AS screen_pe_ratio,
             MIN(pb_ratio) AS screen_pb_ratio,
             MAX(dividend_yield_pct) AS screen_dividend_yield_pct
      FROM market_cap
      GROUP BY company_id
    ),
    latest_pl AS (
      SELECT p.*,
             ROW_NUMBER() OVER (PARTITION BY p.company_id ORDER BY p.fiscal_year DESC, p.id DESC) AS rn
      FROM profitandloss p
      WHERE p.fiscal_year IS NOT NULL
    ),
    prev_ratios AS (
      SELECT company_id, fiscal_year, debt_to_equity,
             ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY fiscal_year DESC, id DESC) AS rn
      FROM financial_ratios
      WHERE fiscal_year IS NOT NULL
    )
    SELECT c.id AS company_id, c.company_name, COALESCE(s.broad_sector, 'Unassigned') AS broad_sector,
           lr.fiscal_year, lr.net_profit_margin_pct, lr.operating_profit_margin_pct,
           lr.return_on_equity_pct, lr.return_on_capital_employed_pct, lr.return_on_assets_pct,
           lr.debt_to_equity, lr.high_leverage_flag, lr.interest_coverage, lr.icr_label,
           lr.asset_turnover, lr.free_cash_flow_cr, lr.revenue_cagr_3yr, lr.revenue_cagr_5yr,
           lr.pat_cagr_5yr, lr.eps_cagr_5yr, lr.composite_quality_score, lr.cfo_quality_score,
           lr.capex_intensity_pct, lr.fcf_conversion_rate_pct, lr.dividend_payout_ratio_pct,
           lm.market_cap_crore, lm.pe_ratio, lm.pb_ratio, lm.dividend_yield_pct,
           ms.screen_pe_ratio, ms.screen_pb_ratio, ms.screen_dividend_yield_pct,
           lp.sales, lp.net_profit, pr.debt_to_equity AS previous_debt_to_equity
    FROM latest_ratios lr
    JOIN companies c ON c.id = lr.company_id
    LEFT JOIN sectors s ON s.company_id = lr.company_id
    LEFT JOIN latest_market lm ON lm.company_id = lr.company_id AND lm.rn = 1
    LEFT JOIN market_screen ms ON ms.company_id = lr.company_id
    LEFT JOIN latest_pl lp ON lp.company_id = lr.company_id AND lp.rn = 1
    LEFT JOIN prev_ratios pr ON pr.company_id = lr.company_id AND pr.rn = 2
    WHERE lr.rn = 1
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["icr_for_filter"] = df.apply(
        lambda row: np.inf if row.get("icr_label") == "Debt Free" else row.get("interest_coverage"),
        axis=1,
    )
    df["de_declining_yoy"] = df.apply(
        lambda row: pd.notna(row.get("previous_debt_to_equity"))
        and pd.notna(row.get("debt_to_equity"))
        and row["debt_to_equity"] < row["previous_debt_to_equity"],
        axis=1,
    )
    return add_composite_quality_score(df)


def winsor_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return pd.Series([50.0] * len(series), index=series.index)
    p10 = numeric.quantile(0.10)
    p90 = numeric.quantile(0.90)
    if p10 == p90:
        score = pd.Series([50.0] * len(series), index=series.index)
    else:
        clipped = numeric.clip(lower=p10, upper=p90)
        score = (clipped - p10) / (p90 - p10) * 100
    if not higher_is_better:
        score = 100 - score
    return score.fillna(0)


def add_composite_quality_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        df["composite_quality_score"] = []
        return df
    score_frames = []
    for _, group in df.groupby("broad_sector", dropna=False):
        part = group.copy()
        part["_roe_score"] = winsor_score(part["return_on_equity_pct"])
        part["_roce_score"] = winsor_score(part["return_on_capital_employed_pct"])
        part["_npm_score"] = winsor_score(part["net_profit_margin_pct"])
        part["_fcf_score"] = winsor_score(part["free_cash_flow_cr"])
        part["_cfo_score"] = winsor_score(part["cfo_quality_score"])
        part["_fcf_positive_score"] = np.where(part["free_cash_flow_cr"] > 0, 100, 0)
        part["_rev_growth_score"] = winsor_score(part["revenue_cagr_5yr"])
        part["_pat_growth_score"] = winsor_score(part["pat_cagr_5yr"])
        part["_de_score"] = winsor_score(part["debt_to_equity"], higher_is_better=False)
        part["_icr_score"] = winsor_score(part["icr_for_filter"].replace(np.inf, np.nan).fillna(999))
        part["composite_quality_score"] = (
            part["_roe_score"] * 0.15
            + part["_roce_score"] * 0.10
            + part["_npm_score"] * 0.10
            + part["_fcf_score"] * 0.15
            + part["_cfo_score"] * 0.10
            + part["_fcf_positive_score"] * 0.05
            + part["_rev_growth_score"] * 0.10
            + part["_pat_growth_score"] * 0.10
            + part["_de_score"] * 0.10
            + part["_icr_score"] * 0.05
        )
        score_frames.append(part)
    return pd.concat(score_frames, ignore_index=True)


def apply_filters(df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    result = df.copy()
    for key, value in thresholds.items():
        if key == "roe_min":
            result = result[result["return_on_equity_pct"] > value]
        elif key == "de_max":
            result = result[(result["broad_sector"] == "Financials") | (result["debt_to_equity"] < value)]
        elif key == "de_eq":
            if value == 0:
                result = result[result["debt_to_equity"] <= 0.01]
            else:
                result = result[result["debt_to_equity"] == value]
        elif key == "fcf_min":
            result = result[result["free_cash_flow_cr"] > value]
        elif key == "revenue_cagr_5yr_min":
            result = result[result["revenue_cagr_5yr"] > value]
        elif key == "revenue_cagr_3yr_min":
            result = result[result["revenue_cagr_3yr"] > value]
        elif key == "pat_cagr_5yr_min":
            result = result[result["pat_cagr_5yr"] > value]
        elif key == "opm_min":
            result = result[result["operating_profit_margin_pct"] > value]
        elif key == "pe_max":
            column = "screen_pe_ratio" if "screen_pe_ratio" in result.columns else "pe_ratio"
            result = result[result[column] < value]
        elif key == "pb_max":
            column = "screen_pb_ratio" if "screen_pb_ratio" in result.columns else "pb_ratio"
            result = result[result[column] < value]
        elif key == "dividend_yield_min":
            use_screen_value = ("pe_max" in thresholds or "pb_max" in thresholds) and "screen_dividend_yield_pct" in result.columns
            column = "screen_dividend_yield_pct" if use_screen_value else "dividend_yield_pct"
            result = result[result[column] > value]
        elif key == "dividend_payout_max":
            result = result[result["dividend_payout_ratio_pct"] < value]
        elif key == "icr_min":
            result = result[result["icr_for_filter"] > value]
        elif key == "market_cap_min":
            result = result[result["market_cap_crore"] > value]
        elif key == "net_profit_min":
            result = result[result["net_profit"] > value]
        elif key == "eps_cagr_min":
            result = result[result["eps_cagr_5yr"] > value]
        elif key == "asset_turnover_min":
            result = result[result["asset_turnover"] > value]
        elif key == "sales_min":
            result = result[result["sales"] > value]
        elif key == "de_declining_yoy":
            if value:
                result = result[result["de_declining_yoy"]]
    return result.sort_values("composite_quality_score", ascending=False).reset_index(drop=True)


def run_presets(df: pd.DataFrame, config: dict) -> dict[str, pd.DataFrame]:
    return {name: apply_filters(df, thresholds) for name, thresholds in config["presets"].items()}
