from __future__ import annotations

import argparse
import csv
import math
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]
CORE_KPIS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "asset_turnover",
]
CLUSTER_NAMES = {
    0: "High-Quality Compounders",
    1: "Defensive Dividend Payers",
    2: "Value Cyclicals",
    3: "Distressed or Turnaround",
    4: "Emerging Growth",
}


def load_latest_frame(db_path: str | Path, output_dir: str | Path) -> pd.DataFrame:
    """Load latest company KPIs and cash-flow intelligence for clustering."""
    conn = sqlite3.connect(db_path)
    query = """
    WITH latest_ratios AS (
      SELECT fr.*,
             ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.fiscal_year DESC, fr.id DESC) AS rn
      FROM financial_ratios fr
      WHERE fr.fiscal_year IS NOT NULL
    )
    SELECT c.id AS company_id, c.company_name, COALESCE(s.broad_sector, 'Unassigned') AS broad_sector,
           lr.return_on_equity_pct, lr.return_on_capital_employed_pct,
           lr.net_profit_margin_pct, lr.operating_profit_margin_pct,
           lr.debt_to_equity, lr.free_cash_flow_cr, lr.revenue_cagr_5yr,
           lr.pat_cagr_5yr, lr.eps_cagr_5yr, lr.asset_turnover,
           lr.composite_quality_score
    FROM companies c
    LEFT JOIN sectors s ON s.company_id = c.id
    LEFT JOIN latest_ratios lr ON lr.company_id = c.id AND lr.rn = 1
    ORDER BY c.id
    """
    frame = pd.read_sql_query(query, conn)
    conn.close()
    cf_path = Path(output_dir) / "cashflow_intelligence.xlsx"
    if cf_path.exists():
        cf = pd.read_excel(cf_path, usecols=["company_id", "fcf_cagr_5yr"])
        frame = frame.merge(cf, on="company_id", how="left")
    else:
        frame["fcf_cagr_5yr"] = np.nan
    return frame


def impute_sector_medians(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Impute missing feature values with sector median, then portfolio median."""
    out = frame.copy()
    for feature in features:
        out[feature] = pd.to_numeric(out[feature], errors="coerce")
        sector_values = out.groupby("broad_sector")[feature].transform("median")
        out[feature] = out[feature].fillna(sector_values)
        out[feature] = out[feature].fillna(out[feature].median())
        out[feature] = out[feature].fillna(0)
    return out


def standard_scale(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Scale features to zero mean and unit variance."""
    mean = values.mean(axis=0)
    std = values.std(axis=0)
    std[std == 0] = 1
    return (values - mean) / std, mean, std


def kmeans(values: np.ndarray, k: int, random_state: int = 42, max_iter: int = 200) -> tuple[np.ndarray, np.ndarray, float]:
    """Run deterministic KMeans with Euclidean distance."""
    rng = np.random.default_rng(random_state)
    if len(values) < k:
        raise ValueError("Not enough rows for requested cluster count")
    centroid_idx = rng.choice(len(values), size=k, replace=False)
    centroids = values[centroid_idx].copy()
    labels = np.zeros(len(values), dtype=int)
    for _ in range(max_iter):
        distances = np.linalg.norm(values[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = distances.argmin(axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for cluster_id in range(k):
            members = values[labels == cluster_id]
            if len(members):
                centroids[cluster_id] = members.mean(axis=0)
    distances = np.linalg.norm(values[:, None, :] - centroids[None, :, :], axis=2)
    labels = distances.argmin(axis=1)
    inertia = float(np.sum((values - centroids[labels]) ** 2))
    return labels, centroids, inertia


def elbow_plot(values: np.ndarray, reports_dir: Path) -> None:
    """Generate elbow plot for k from 2 to 10."""
    inertias = []
    ks = list(range(2, 11))
    for k in ks:
        _, _, inertia = kmeans(values, k, random_state=42)
        inertias.append(inertia)
    reports_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.plot(ks, inertias, marker="o")
    plt.axvline(5, color="red", linestyle="--", label="k=5")
    plt.title("KMeans Elbow Plot")
    plt.xlabel("Number of clusters")
    plt.ylabel("Inertia")
    plt.legend()
    plt.tight_layout()
    plt.savefig(reports_dir / "elbow_plot.png", dpi=150)
    plt.close()


def correlation_heatmap(frame: pd.DataFrame, reports_dir: Path) -> None:
    """Generate annotated Pearson correlation heatmap for core KPIs."""
    data = frame[CORE_KPIS].apply(pd.to_numeric, errors="coerce")
    corr = data.corr(method="pearson")
    plt.figure(figsize=(11, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("NIFTY100 Latest-Year KPI Correlation")
    plt.tight_layout()
    reports_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(reports_dir / "correlation_heatmap.png", dpi=150)
    plt.close()


def outlier_report(frame: pd.DataFrame, output_dir: Path) -> int:
    """Write sector-relative Z-score outliers with absolute Z-score above 3."""
    rows = []
    for sector, group in frame.groupby("broad_sector", dropna=False):
        for metric in CORE_KPIS:
            values = pd.to_numeric(group[metric], errors="coerce")
            mean = values.mean()
            std = values.std()
            if pd.isna(std) or std == 0:
                continue
            zscores = (values - mean) / std
            for idx, zscore in zscores.items():
                if pd.notna(zscore) and abs(zscore) > 3:
                    rows.append(
                        {
                            "company_id": frame.loc[idx, "company_id"],
                            "company_name": frame.loc[idx, "company_name"],
                            "broad_sector": sector,
                            "metric": metric,
                            "value": values.loc[idx],
                            "z_score": zscore,
                        }
                    )
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_dir / "outlier_report.csv", index=False)
    return len(rows)


def portfolio_stats(frame: pd.DataFrame, output_dir: Path) -> int:
    """Write percentile and distribution statistics for core KPIs."""
    rows = []
    for metric in CORE_KPIS:
        values = pd.to_numeric(frame[metric], errors="coerce").dropna()
        rows.append(
            {
                "metric": metric,
                "p10": values.quantile(0.10),
                "p25": values.quantile(0.25),
                "p50": values.quantile(0.50),
                "p75": values.quantile(0.75),
                "p90": values.quantile(0.90),
                "mean": values.mean(),
                "std": values.std(),
            }
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).round(4).to_csv(output_dir / "portfolio_stats.csv", index=False)
    return len(rows)


def write_cluster_profile(frame: pd.DataFrame, output_dir: Path) -> None:
    """Write mean and median of input features by cluster."""
    rows = []
    for cluster_id, group in frame.groupby("cluster_id"):
        row = {"cluster_id": cluster_id, "cluster_name": CLUSTER_NAMES.get(int(cluster_id), f"Cluster {cluster_id}")}
        for feature in FEATURES:
            row[f"{feature}_mean"] = group[feature].mean()
            row[f"{feature}_median"] = group[feature].median()
        row["company_count"] = len(group)
        rows.append(row)
    pd.DataFrame(rows).round(4).to_csv(output_dir / "cluster_profile.csv", index=False)


def generate_clustering_outputs(db_path: str | Path, output_dir: str | Path, reports_dir: str | Path) -> dict[str, int]:
    """Generate Sprint 6 clustering, correlation, outlier, and portfolio-stat outputs."""
    output_path = Path(output_dir)
    reports_path = Path(reports_dir)
    frame = load_latest_frame(db_path, output_path)
    frame = impute_sector_medians(frame, FEATURES)
    scaled, _, _ = standard_scale(frame[FEATURES].to_numpy(dtype=float))
    elbow_plot(scaled, reports_path)
    labels, centroids, _ = kmeans(scaled, 5, random_state=42)
    distances = np.linalg.norm(scaled - centroids[labels], axis=1)
    frame["cluster_id"] = labels
    frame["cluster_name"] = frame["cluster_id"].map(CLUSTER_NAMES)
    frame["distance_from_centroid"] = distances
    labels_out = frame[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]].copy()
    output_path.mkdir(parents=True, exist_ok=True)
    labels_out.round(6).to_csv(output_path / "cluster_labels.csv", index=False)
    write_cluster_profile(frame, output_path)
    correlation_heatmap(frame, reports_path)
    outliers = outlier_report(frame, output_path)
    stat_rows = portfolio_stats(frame, output_path)
    return {
        "clustered_companies": len(labels_out),
        "outlier_rows": outliers,
        "portfolio_stat_rows": stat_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Sprint 6 KMeans clustering outputs.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "output"))
    parser.add_argument("--reports-dir", default=str(PROJECT_ROOT / "reports"))
    args = parser.parse_args()
    counts = generate_clustering_outputs(args.db, args.output_dir, args.reports_dir)
    for key, value in counts.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
