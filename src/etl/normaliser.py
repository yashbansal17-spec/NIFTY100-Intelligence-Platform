from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


SOURCE_FILES = {
    "companies": "companies.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "prosandcons": "prosandcons.xlsx",
    "financial_ratios": "financial_ratios.xlsx",
    "market_cap": "market_cap.xlsx",
    "peer_groups": "peer_groups.xlsx",
    "sectors": "sectors.xlsx",
    "stock_prices": "stock_prices.xlsx",
}

CORE_TABLES = {
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
}

LOAD_ORDER = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "stock_prices",
]

NUMERIC_COLUMNS = {
    "companies": ["face_value", "book_value", "roce_percentage", "roe_percentage"],
    "profitandloss": [
        "sales",
        "expenses",
        "operating_profit",
        "opm_percentage",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_percentage",
        "net_profit",
        "eps",
        "dividend_payout",
    ],
    "balancesheet": [
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
    ],
    "cashflow": ["operating_activity", "investing_activity", "financing_activity", "net_cash_flow"],
    "financial_ratios": [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
    ],
    "market_cap": [
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ],
    "sectors": ["index_weight_pct"],
    "stock_prices": ["open_price", "high_price", "low_price", "close_price", "volume", "adjusted_close"],
}


def snake_case(value: object) -> str:
    text = str(value).strip().replace("%", " percentage ")
    text = re.sub(r"[^0-9A-Za-z]+", "_", text).strip("_").lower()
    return text


def normalize_ticker(value: object) -> str | None:
    if pd.isna(value):
        return None
    ticker = str(value).strip().upper()
    ticker = re.sub(r"^(NSE|BSE)\s*[:\-]\s*", "", ticker)
    ticker = re.sub(r"\s+", "", ticker)
    return ticker or None


def normalize_year(value: object) -> int | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    match = re.search(r"(19|20)\d{2}", text)
    if match:
        return int(match.group(0))
    match = re.search(r"(?<!\d)(\d{2})(?!\d)", text)
    if match:
        year = int(match.group(1))
        return 2000 + year if year < 40 else 1900 + year
    return None


def read_source(data_dir: str | Path, table: str) -> pd.DataFrame:
    path = Path(data_dir) / SOURCE_FILES[table]
    df = pd.read_excel(path, header=1) if table in CORE_TABLES else pd.read_excel(path)
    if any(str(col).startswith("Unnamed") for col in df.columns):
        headers = [snake_case(value) for value in df.iloc[0].tolist()]
        df = df.iloc[1:].copy()
        df.columns = headers
    else:
        df.columns = [snake_case(col) for col in df.columns]
    df = df.dropna(how="all").copy()
    df = df.loc[:, [col for col in df.columns if col]]
    return normalize_frame(table, df)


def normalize_frame(table: str, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [snake_case(col) for col in df.columns]
    df = df.rename(columns={"year": "year", "annual_report": "annual_report"})

    if "id" in df.columns and table != "companies":
        df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")

    if table == "companies":
        df["id"] = df["id"].map(normalize_ticker)
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].map(normalize_ticker)

    if table == "peer_groups" and "is_benchmark" in df.columns:
        df["is_benchmark"] = df["is_benchmark"].map(lambda x: 1 if str(x).strip().lower() == "true" else 0)

    if table == "stock_prices" and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    if table in {"documents", "market_cap"} and "year" in df.columns:
        df["year"] = df["year"].map(normalize_year).astype("Int64")
    elif "year" in df.columns and table != "stock_prices":
        df["fiscal_year"] = df["year"].map(normalize_year).astype("Int64")

    for col in NUMERIC_COLUMNS.get(table, []):
        if col in df.columns:
            if col == "volume":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.astype(object).where(pd.notna(df), None)
