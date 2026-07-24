from __future__ import annotations


OK = "OK"
TURNAROUND = "TURNAROUND"
DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
BOTH_NEGATIVE = "BOTH_NEGATIVE"
ZERO_BASE = "ZERO_BASE"
INSUFFICIENT = "INSUFFICIENT"


def cagr(start: float | None, end: float | None, years: int | None) -> tuple[float | None, str]:
    if years is None or years <= 0 or start is None or end is None:
        return None, INSUFFICIENT
    if start == 0:
        return None, ZERO_BASE
    if start > 0 and end > 0:
        return (((end / start) ** (1 / years)) - 1) * 100, OK
    if start > 0 and end < 0:
        return None, DECLINE_TO_LOSS
    if start < 0 and end > 0:
        return None, TURNAROUND
    if start < 0 and end < 0:
        return None, BOTH_NEGATIVE
    return None, ZERO_BASE


def cagr_for_window(series_by_year: dict[int, float | None], end_year: int | None, years: int) -> tuple[float | None, str]:
    if end_year is None:
        return None, INSUFFICIENT
    start_year = end_year - years
    if end_year not in series_by_year or start_year not in series_by_year:
        return None, INSUFFICIENT
    return cagr(series_by_year[start_year], series_by_year[end_year], years)
