# Sprint 2 Retrospective

## Formula Decisions

- Profitability ratios return `None` for unsafe denominators such as zero sales, zero assets, or non-positive equity.
- Debt-free companies receive `interest_coverage = None` and `icr_label = Debt Free`.
- Financials use a sector-relative ROCE mode, and high D/E warning flags are suppressed for Financials because leverage is structurally normal.
- CAGR metrics use explicit flags for turnaround, decline-to-loss, both-negative, zero-base, and insufficient-history cases.
- Source `roe_percentage` and `roce_percentage` are treated as display/reference values; computed values are used for analytics.

## Edge Cases Resolved

- OPM cross-check differences greater than 1 percentage point are logged.
- ROE and ROCE differences versus company master values are logged with category and explanation.
- Financial-sector leverage suppressions are logged as formula decisions.

## Sprint 2 Review Notes

- `financial_ratios` has 1,160 rows after the ratio engine runs.
- `capital_allocation.csv` has one pattern row per loaded cash-flow company-year.
- Screener preview count is within the requested 15-50 range.
