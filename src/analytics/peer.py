from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


PEER_METRICS = {
    "ROE": ("return_on_equity_pct", True),
    "ROCE": ("return_on_capital_employed_pct", True),
    "Net Profit Margin": ("net_profit_margin_pct", True),
    "D/E": ("debt_to_equity", False),
    "FCF": ("free_cash_flow_cr", True),
    "PAT CAGR 5yr": ("pat_cagr_5yr", True),
    "Revenue CAGR 5yr": ("revenue_cagr_5yr", True),
    "EPS CAGR 5yr": ("eps_cagr_5yr", True),
    "Interest Coverage": ("interest_coverage", True),
    "Asset Turnover": ("asset_turnover", True),
}


def latest_ratio_frame(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
    WITH ranked AS (
      SELECT fr.*,
             ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
      FROM financial_ratios fr
      WHERE fr.fiscal_year IS NOT NULL
    )
    SELECT r.*, c.company_name
    FROM ranked r
    JOIN companies c ON c.id = r.company_id
    WHERE r.rn = 1
    """
    return pd.read_sql_query(query, conn)


def percent_rank(values: pd.Series, higher_is_better: bool) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().sum() <= 1:
        ranks = pd.Series([1.0] * len(values), index=values.index)
    else:
        ranks = numeric.rank(method="min", pct=True)
    if not higher_is_better:
        ranks = 1 - ranks + (1 / max(len(values), 1))
    return ranks.clip(0, 1).fillna(0)


def compute_peer_percentiles(db_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = sqlite3.connect(db_path)
    ratios = latest_ratio_frame(conn)
    peers = pd.read_sql_query("SELECT peer_group_name, company_id, is_benchmark FROM peer_groups", conn)
    merged = peers.merge(ratios, on="company_id", how="left")
    rows = []
    for group_name, group in merged.groupby("peer_group_name"):
        for metric_name, (column, higher_is_better) in PEER_METRICS.items():
            ranks = percent_rank(group[column], higher_is_better)
            for idx, rank in ranks.items():
                rows.append(
                    {
                        "company_id": group.loc[idx, "company_id"],
                        "peer_group_name": group_name,
                        "metric": metric_name,
                        "value": group.loc[idx, column],
                        "percentile_rank": float(rank),
                        "year": int(group.loc[idx, "fiscal_year"]) if pd.notna(group.loc[idx, "fiscal_year"]) else None,
                    }
                )
    percentiles = pd.DataFrame(rows)
    conn.execute("DROP TABLE IF EXISTS peer_percentiles")
    conn.execute(
        """
        CREATE TABLE peer_percentiles (
          company_id TEXT NOT NULL REFERENCES companies(id),
          peer_group_name TEXT NOT NULL,
          metric TEXT NOT NULL,
          value REAL,
          percentile_rank REAL,
          year INTEGER
        )
        """
    )
    percentiles.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()
    assigned = set(peers["company_id"])
    unassigned = ratios.loc[~ratios["company_id"].isin(assigned), ["company_id", "company_name"]].copy()
    unassigned["message"] = "No peer group assigned"
    conn.close()
    return percentiles, unassigned
