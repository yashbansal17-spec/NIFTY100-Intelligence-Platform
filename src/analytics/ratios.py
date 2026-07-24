from __future__ import annotations


def safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def pct(numerator: float | None, denominator: float | None) -> float | None:
    value = safe_divide(numerator, denominator)
    return None if value is None else value * 100


def net_profit_margin(net_profit: float | None, sales: float | None) -> float | None:
    return pct(net_profit, sales)


def operating_profit_margin(
    operating_profit: float | None,
    sales: float | None,
    source_opm: float | None = None,
    tolerance_pct: float = 1.0,
) -> tuple[float | None, bool]:
    computed = pct(operating_profit, sales)
    mismatch = computed is not None and source_opm is not None and abs(computed - source_opm) > tolerance_pct
    return computed, mismatch


def return_on_equity(net_profit: float | None, equity_capital: float | None, reserves: float | None) -> float | None:
    equity = (equity_capital or 0) + (reserves or 0)
    if equity <= 0:
        return None
    return pct(net_profit, equity)


def return_on_capital_employed(
    operating_profit: float | None,
    other_income: float | None,
    equity_capital: float | None,
    reserves: float | None,
    borrowings: float | None,
    broad_sector: str | None = None,
) -> tuple[float | None, str]:
    capital = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if capital <= 0:
        return None, "financials_sector_relative" if broad_sector == "Financials" else "absolute"
    ebit = (operating_profit or 0) + (other_income or 0)
    mode = "financials_sector_relative" if broad_sector == "Financials" else "absolute"
    return pct(ebit, capital), mode


def return_on_assets(net_profit: float | None, total_assets: float | None) -> float | None:
    return pct(net_profit, total_assets)


def debt_to_equity(borrowings: float | None, equity_capital: float | None, reserves: float | None) -> float | None:
    if borrowings == 0:
        return 0
    equity = (equity_capital or 0) + (reserves or 0)
    if equity <= 0:
        return None
    return safe_divide(borrowings, equity)


def high_leverage_flag(de_ratio: float | None, broad_sector: str | None) -> bool:
    return de_ratio is not None and de_ratio > 5 and broad_sector != "Financials"


def interest_coverage(
    operating_profit: float | None,
    other_income: float | None,
    interest: float | None,
) -> tuple[float | None, str | None, bool]:
    if interest in (None, 0):
        return None, "Debt Free", False
    value = safe_divide((operating_profit or 0) + (other_income or 0), interest)
    return value, None, value is not None and value < 1.5


def net_debt(borrowings: float | None, investments: float | None) -> float | None:
    if borrowings is None and investments is None:
        return None
    return (borrowings or 0) - (investments or 0)


def asset_turnover(sales: float | None, total_assets: float | None) -> float | None:
    return safe_divide(sales, total_assets)


def book_value_per_share(equity_capital: float | None, reserves: float | None) -> float | None:
    if equity_capital in (None, 0):
        return None
    return safe_divide((equity_capital or 0) + (reserves or 0), equity_capital)


def composite_quality_score(
    roe: float | None,
    npm: float | None,
    de_ratio: float | None,
    cfo_quality: float | None,
) -> float | None:
    parts: list[float] = []
    if roe is not None:
        parts.append(max(0, min(100, roe)))
    if npm is not None:
        parts.append(max(0, min(100, npm * 2)))
    if de_ratio is not None:
        parts.append(max(0, 100 - min(100, de_ratio * 20)))
    if cfo_quality is not None:
        parts.append(max(0, min(100, cfo_quality * 50)))
    if not parts:
        return None
    return sum(parts) / len(parts)
