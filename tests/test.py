"""
test_dashboard.py

Standalone validation script for the NIFTY100 Intelligence Platform.
Runs OUTSIDE Streamlit - directly imports the same db.py / live_data.py
modules your dashboard pages use, so it verifies the exact data your
UI is built on.

USAGE
-----
Place this file in your project root (same folder as README/pyproject),
i.e. C:\\Users\\hp\\Desktop\\NIFTY100\\test_dashboard.py, then run:

    python test_dashboard.py

Or from anywhere, pointing at the project root:

    python test_dashboard.py --project-root "C:\\Users\\hp\\Desktop\\NIFTY100"

OUTPUT
------
- Console log of every check (PASS/FAIL/WARN)
- dashboard_test_report.txt  - full text report
- roe_vs_roce.png            - scatter of ROE vs ROCE across the universe
- revenue_trends.png         - 5yr+ revenue trend for selected companies

Exit code is non-zero if any hard FAIL occurred, so you can wire this
into a CI check later if you want.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Windows consoles often default to cp1252, which cannot encode the Rupee
# sign (\u20b9) or other non-ASCII characters used in this script's output.
# Force stdout/stderr to UTF-8 so console printing never crashes.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Path setup - mirrors the sys.path.insert pattern used in your pages/*.py
# ---------------------------------------------------------------------------

def setup_paths(project_root: Path) -> None:
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


# ---------------------------------------------------------------------------
# Companies you want the revenue-trend chart drawn for.
# Edit this list to whichever tickers you want to eyeball.
# Use the company_id / ticker exactly as stored in your `companies` table.
# ---------------------------------------------------------------------------
REVENUE_TREND_TICKERS = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ITC"]


class Report:
    """Collects check results and writes a text report + prints to console."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.fail_count = 0
        self.warn_count = 0
        self.pass_count = 0

    def _log(self, level: str, msg: str) -> None:
        line = f"[{level}] {msg}"
        print(line)
        self.lines.append(line)

    def ok(self, msg: str) -> None:
        self.pass_count += 1
        self._log("PASS", msg)

    def warn(self, msg: str) -> None:
        self.warn_count += 1
        self._log("WARN", msg)

    def fail(self, msg: str) -> None:
        self.fail_count += 1
        self._log("FAIL", msg)

    def section(self, title: str) -> None:
        bar = "=" * 70
        self._log("INFO", "")
        self._log("INFO", bar)
        self._log("INFO", title)
        self._log("INFO", bar)

    def write(self, path: Path) -> None:
        path.write_text("\n".join(self.lines), encoding="utf-8")


def check_universe(db, report: Report) -> pd.DataFrame:
    report.section("1. COMPANY UNIVERSE")
    companies = db.get_companies()

    if companies.empty:
        report.fail("get_companies() returned an EMPTY DataFrame. No companies loaded at all.")
        return companies

    n = len(companies)
    if n == 0:
        report.fail("Company count is 0.")
    elif n < 100:
        report.warn(f"Only {n} companies found - expected ~100 for a NIFTY 100 universe.")
    elif n > 100:
        report.warn(f"{n} companies found - more than 100, check for duplicate rows.")
    else:
        report.ok(f"Company count = {n} (matches NIFTY 100 expectation).")

    dupes = companies["company_id"].duplicated().sum()
    if dupes:
        report.fail(f"{dupes} duplicate company_id values found in companies table.")
    else:
        report.ok("No duplicate company_id values.")

    missing_sector = companies["broad_sector"].isna().sum() + (companies["broad_sector"] == "Unassigned").sum()
    if missing_sector:
        report.warn(f"{missing_sector} companies have no sector assigned ('Unassigned' / NaN).")
    else:
        report.ok("All companies have a sector assigned.")

    return companies


def check_live_market(live_data, companies: pd.DataFrame, report: Report) -> pd.DataFrame:
    report.section("2. LIVE MARKET DATA (Daily Open / Close / Current Price)")
    live_df = live_data.get_cached_live_market(force_refresh=False)

    if live_df.empty:
        report.fail("get_cached_live_market() returned EMPTY. Live price feed is broken or yfinance unreachable "
                    "and the dynamic fallback also failed.")
        return live_df

    report.ok(f"Live market data returned for {len(live_df)} companies.")

    expected_ids = set(companies["company_id"]) if not companies.empty else set()
    live_ids = set(live_df["company_id"])
    missing = expected_ids - live_ids
    if missing:
        report.warn(f"{len(missing)} companies have NO live price row: {sorted(missing)[:15]}"
                    f"{' ...' if len(missing) > 15 else ''}")
    else:
        report.ok("Every company in the universe has a live price row.")

    required_cols = ["current_price", "open_price", "high_52w", "low_52w", "return_1m_pct",
                      "pct_from_52w_high", "as_of_date", "is_live"]
    for col in required_cols:
        if col not in live_df.columns:
            report.fail(f"Column '{col}' missing entirely from live market data.")

    zero_or_null_price = live_df[live_df["current_price"].isna() | (live_df["current_price"] <= 0)]
    if not zero_or_null_price.empty:
        report.fail(f"{len(zero_or_null_price)} companies have null/zero current_price: "
                    f"{zero_or_null_price['company_id'].tolist()[:15]}")
    else:
        report.ok("No null/zero current_price values.")

    bad_52w = live_df[live_df["high_52w"] < live_df["low_52w"]]
    if not bad_52w.empty:
        report.fail(f"{len(bad_52w)} companies have 52W High < 52W Low (data integrity issue): "
                    f"{bad_52w['company_id'].tolist()}")
    else:
        report.ok("52W High >= 52W Low for all companies.")

    out_of_range = live_df[
        (live_df["current_price"] > live_df["high_52w"] * 1.01)
        | (live_df["current_price"] < live_df["low_52w"] * 0.99)
    ]
    if not out_of_range.empty:
        report.warn(f"{len(out_of_range)} companies have current_price outside their own 52W range "
                    f"(possible stale 52W data): {out_of_range['company_id'].tolist()[:15]}")
    else:
        report.ok("current_price falls within each company's own 52W High/Low range.")

    live_count = int(live_df["is_live"].sum()) if "is_live" in live_df.columns else 0
    fallback_count = len(live_df) - live_count
    report.ok(f"Live yfinance data: {live_count} companies | Simulated fallback data: {fallback_count} companies.")
    if fallback_count > 0:
        report.warn(f"{fallback_count} companies are using SIMULATED price data, not real yfinance data. "
                    "This usually means yfinance failed for those tickers (bad NSE symbol mapping, "
                    "rate limit, or no internet).")

    as_of_values = live_df["as_of_date"].unique()
    report.ok(f"Data as-of timestamp(s) present: {list(as_of_values)[:3]}")

    return live_df


def check_monthly_summary(live_data, live_df: pd.DataFrame, report: Report) -> dict:
    report.section("3. MONTHLY SUMMARY (Top Gainers / Losers / 52W Breakouts)")
    if live_df.empty:
        report.fail("Skipping monthly summary checks - live_df is empty.")
        return {}

    summary = live_data.get_cached_monthly_summary()
    if not summary:
        report.fail("get_cached_monthly_summary() returned an empty dict.")
        return {}

    top_gainers = summary.get("top_gainers")
    top_losers = summary.get("top_losers")

    if top_gainers is None or top_gainers.empty:
        report.fail("Top Gainers list is empty.")
    else:
        sorted_check = top_gainers["return_1m_pct"].is_monotonic_decreasing
        if sorted_check:
            report.ok(f"Top Gainers correctly sorted descending. #1 = "
                      f"{top_gainers.iloc[0]['company_id']} ({top_gainers.iloc[0]['return_1m_pct']:+.2f}%).")
        else:
            report.fail("Top Gainers list is NOT sorted correctly by return_1m_pct descending.")

    if top_losers is None or top_losers.empty:
        report.fail("Top Losers list is empty.")
    else:
        sorted_check = top_losers["return_1m_pct"].is_monotonic_increasing
        if sorted_check:
            report.ok(f"Top Losers correctly sorted ascending. #1 worst = "
                      f"{top_losers.iloc[0]['company_id']} ({top_losers.iloc[0]['return_1m_pct']:+.2f}%).")
        else:
            report.fail("Top Losers list is NOT sorted correctly by return_1m_pct ascending.")

    if top_gainers is not None and top_losers is not None and not top_gainers.empty and not top_losers.empty:
        overlap = set(top_gainers["company_id"]) & set(top_losers["company_id"])
        if overlap:
            report.fail(f"Same company appears in BOTH Top Gainers and Top Losers: {overlap}")
        else:
            report.ok("No overlap between Top Gainers and Top Losers.")

    near_high = summary.get("near_52w_high")
    near_low = summary.get("near_52w_low")
    if near_high is not None:
        bad = near_high[near_high["pct_from_52w_high"] < -5.0]
        if not bad.empty:
            report.fail(f"{len(bad)} companies in 'Near 52W High' list are actually more than 5% below high.")
        else:
            report.ok(f"'Near 52W High' list ({len(near_high)} companies) all within 5% of their high.")
    if near_low is not None:
        bad = near_low[near_low["pct_from_52w_low"] > 5.0]
        if not bad.empty:
            report.fail(f"{len(bad)} companies in 'Near 52W Low' list are actually more than 5% above low.")
        else:
            report.ok(f"'Near 52W Low' list ({len(near_low)} companies) all within 5% of their low.")

    avg_ret = summary.get("avg_1m_return")
    pct_adv = summary.get("pct_advancing")
    report.ok(f"Average 1M market return: {avg_ret:+.2f}% | Advancing: {pct_adv}%")
    if avg_ret is not None and abs(avg_ret) > 25:
        report.warn(f"Average 1M return of {avg_ret:+.2f}% looks unusually large for a monthly market move - "
                    "double check this isn't actually an annual return being mislabeled as 1M.")

    return summary


def check_fundamentals_history(db, companies: pd.DataFrame, report: Report) -> pd.DataFrame:
    report.section("4. 5-YEAR FUNDAMENTALS HISTORY (per-company fiscal year coverage)")
    if companies.empty:
        report.fail("Skipping - no companies to check.")
        return pd.DataFrame()

    current_year = datetime.now().year
    rows = []
    latest_years_seen = []

    for row in companies.itertuples():
        ticker = row.company_id
        ratios = db.get_ratios(ticker)
        if ratios.empty:
            rows.append({"company_id": ticker, "years_available": 0, "latest_year": None, "earliest_year": None})
            continue
        years = sorted(ratios["fiscal_year"].dropna().unique().tolist())
        rows.append({
            "company_id": ticker,
            "years_available": len(years),
            "latest_year": max(years) if years else None,
            "earliest_year": min(years) if years else None,
        })
        if years:
            latest_years_seen.append(max(years))

    coverage = pd.DataFrame(rows)
    no_data = coverage[coverage["years_available"] == 0]
    if not no_data.empty:
        report.fail(f"{len(no_data)} companies have ZERO fundamentals history: "
                    f"{no_data['company_id'].tolist()[:15]}")
    else:
        report.ok("Every company has at least some fundamentals history.")

    thin = coverage[(coverage["years_available"] > 0) & (coverage["years_available"] < 5)]
    if not thin.empty:
        report.warn(f"{len(thin)} companies have FEWER than 5 years of history "
                    f"(partial history, charts will note this): {thin['company_id'].tolist()[:15]}")
    else:
        report.ok("All companies with data have 5+ years of fundamentals history.")

    if latest_years_seen:
        overall_latest = max(latest_years_seen)
        overall_mode = pd.Series(latest_years_seen).mode().iloc[0]
        report.ok(f"Most recent fiscal year found across the universe: {overall_latest} "
                  f"(most common latest year: {overall_mode}).")
        if overall_latest < current_year - 1:
            report.warn(
                f"Latest fundamentals data is FY{overall_latest}, but the current year is {current_year}. "
                f"This confirms your ETL/ingestion pipeline has not loaded FY{overall_latest + 1} onward yet. "
                "This is a data-population issue (source pipeline), not a dashboard bug - the charts will "
                "show newer years automatically the moment those rows exist in financial_ratios/profitandloss."
            )
    else:
        report.fail("Could not determine latest fiscal year - no fundamentals data found anywhere.")

    return coverage


def build_roe_vs_roce_chart(db, companies: pd.DataFrame, report: Report, out_path: Path) -> None:
    report.section("5. ROE vs ROCE CHART")
    universe = db.get_latest_universe()
    if universe.empty:
        report.fail("get_latest_universe() is empty - cannot build ROE vs ROCE chart.")
        return

    plot_df = universe.dropna(subset=["return_on_equity_pct", "return_on_capital_employed_pct"])
    if plot_df.empty:
        report.fail("No companies have both ROE and ROCE populated - cannot plot.")
        return

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        report.fail("matplotlib is not installed. Run: pip install matplotlib")
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    sectors = plot_df["broad_sector"].fillna("Unassigned")
    unique_sectors = sorted(sectors.unique())
    cmap = plt.get_cmap("tab20")
    color_map = {s: cmap(i % 20) for i, s in enumerate(unique_sectors)}

    for sector in unique_sectors:
        subset = plot_df[sectors == sector]
        ax.scatter(
            subset["return_on_equity_pct"],
            subset["return_on_capital_employed_pct"],
            label=sector,
            alpha=0.75,
            s=60,
            color=color_map[sector],
        )

    lims = [
        min(plot_df["return_on_equity_pct"].min(), plot_df["return_on_capital_employed_pct"].min()) - 2,
        max(plot_df["return_on_equity_pct"].max(), plot_df["return_on_capital_employed_pct"].max()) + 2,
    ]
    ax.plot(lims, lims, linestyle="--", color="gray", linewidth=1, label="ROE = ROCE")

    ax.set_xlabel("ROE %")
    ax.set_ylabel("ROCE %")
    ax.set_title(f"ROE vs ROCE - NIFTY 100 Universe (n={len(plot_df)})")
    ax.legend(loc="upper left", fontsize=7, ncol=2, framealpha=0.85)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    report.ok(f"ROE vs ROCE scatter chart saved to: {out_path} ({len(plot_df)} companies plotted).")

    outliers = plot_df[(plot_df["return_on_equity_pct"] - plot_df["return_on_capital_employed_pct"]).abs() > 40]
    if not outliers.empty:
        report.warn(
            f"{len(outliers)} companies show a >40 point gap between ROE and ROCE "
            f"(could indicate high leverage or a data issue - worth a manual look): "
            f"{outliers['company_id'].tolist()[:10]}"
        )


def build_revenue_trend_chart(db, tickers: list[str], report: Report, out_path: Path) -> None:
    report.section("6. REVENUE TREND CHART (selected companies)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        report.fail("matplotlib is not installed. Run: pip install matplotlib")
        return

    fig, ax = plt.subplots(figsize=(11, 6))
    plotted_any = False

    for ticker in tickers:
        pl = db.get_pl(ticker)
        if pl.empty:
            report.warn(f"No P&L data found for ticker '{ticker}' - skipping in revenue chart. "
                        "Check the ticker spelling matches your companies.id exactly.")
            continue
        pl = pl.sort_values("fiscal_year")
        ax.plot(pl["fiscal_year"], pl["sales"], marker="o", label=ticker)
        plotted_any = True
        latest_year = pl["fiscal_year"].max()
        report.ok(f"{ticker}: {len(pl)} years of revenue data, latest FY{latest_year}, "
                  f"latest revenue ₹{pl['sales'].iloc[-1]:,.0f} Cr.")

    if not plotted_any:
        report.fail("None of the requested tickers had P&L data - chart not saved.")
        plt.close(fig)
        return

    ax.set_xlabel("Fiscal Year")
    ax.set_ylabel("Revenue (INR Crore)")
    ax.set_title("Revenue Trend - Selected Companies")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    report.ok(f"Revenue trend chart saved to: {out_path}")


def check_peer_groups(db, report: Report) -> None:
    report.section("7. PEER GROUPS")
    names = db.get_peer_group_names()
    if names.empty:
        report.warn("No peer groups found - Peer Benchmarking page will show 'No peer groups available.'")
        return
    report.ok(f"{len(names)} peer groups found: {names['peer_group_name'].tolist()[:10]}"
              f"{' ...' if len(names) > 10 else ''}")

    for name in names["peer_group_name"].tolist()[:5]:
        peers = db.get_peers(name)
        if peers.empty:
            report.warn(f"Peer group '{name}' has zero companies assigned.")
        else:
            bench_count = int(peers["is_benchmark"].fillna(0).sum())
            report.ok(f"Peer group '{name}': {len(peers)} companies, {bench_count} marked as benchmark.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the NIFTY100 dashboard's data and charts.")
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Path to the NIFTY100 project root (folder containing 'src' and 'pages'). "
             "Defaults to current directory.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    setup_paths(project_root)

    report = Report()
    report.section("NIFTY100 DASHBOARD VALIDATION - STARTED " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    report.ok(f"Project root: {project_root}")

    db_path = project_root / "output" / "nifty100.db"
    if not db_path.exists():
        report.fail(f"Database not found at expected path: {db_path}. "
                    "Pass --project-root pointing at your NIFTY100 folder, or check the DB was built.")
        report.write(project_root / "dashboard_test_report.txt")
        return 1

    try:
        from dashboard.utils import db
        from dashboard.utils import live_data
    except Exception as exc:
        report.fail(f"Could not import dashboard.utils.db / live_data: {exc}")
        report.write(project_root / "dashboard_test_report.txt")
        return 1

    companies = check_universe(db, report)
    live_df = check_live_market(live_data, companies, report)
    check_monthly_summary(live_data, live_df, report)
    check_fundamentals_history(db, companies, report)
    build_roe_vs_roce_chart(db, companies, report, project_root / "roe_vs_roce.png")
    build_revenue_trend_chart(db, REVENUE_TREND_TICKERS, report, project_root / "revenue_trends.png")
    check_peer_groups(db, report)

    report.section("SUMMARY")
    report.ok(f"PASS: {report.pass_count}  |  WARN: {report.warn_count}  |  FAIL: {report.fail_count}")

    report_path = project_root / "dashboard_test_report.txt"
    report.write(report_path)
    print(f"\nFull report written to: {report_path}")
    print(f"Charts written to: {project_root / 'roe_vs_roce.png'} and {project_root / 'revenue_trends.png'}")

    return 1 if report.fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())