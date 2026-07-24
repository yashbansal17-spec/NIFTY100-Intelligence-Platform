PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS market_cap;
DROP TABLE IF EXISTS peer_groups;
DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS sectors;
DROP TABLE IF EXISTS prosandcons;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS analysis;
DROP TABLE IF EXISTS cashflow;
DROP TABLE IF EXISTS balancesheet;
DROP TABLE IF EXISTS profitandloss;
DROP TABLE IF EXISTS companies;

PRAGMA foreign_keys = ON;

CREATE TABLE companies (
  id TEXT PRIMARY KEY,
  company_logo TEXT,
  company_name TEXT NOT NULL,
  chart_link TEXT,
  about_company TEXT,
  website TEXT,
  nse_profile TEXT,
  bse_profile TEXT,
  face_value REAL,
  book_value REAL,
  roce_percentage REAL,
  roe_percentage REAL
);

CREATE TABLE profitandloss (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  year TEXT NOT NULL,
  fiscal_year INTEGER,
  sales REAL,
  expenses REAL,
  operating_profit REAL,
  opm_percentage REAL,
  other_income REAL,
  interest REAL,
  depreciation REAL,
  profit_before_tax REAL,
  tax_percentage REAL,
  net_profit REAL,
  eps REAL,
  dividend_payout REAL
);

CREATE TABLE balancesheet (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  year TEXT NOT NULL,
  fiscal_year INTEGER,
  equity_capital REAL,
  reserves REAL,
  borrowings REAL,
  other_liabilities REAL,
  total_liabilities REAL,
  fixed_assets REAL,
  cwip REAL,
  investments REAL,
  other_asset REAL,
  total_assets REAL
);

CREATE TABLE cashflow (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  year TEXT NOT NULL,
  fiscal_year INTEGER,
  operating_activity REAL,
  investing_activity REAL,
  financing_activity REAL,
  net_cash_flow REAL
);

CREATE TABLE analysis (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  compounded_sales_growth TEXT,
  compounded_profit_growth TEXT,
  stock_price_cagr TEXT,
  roe TEXT
);

CREATE TABLE documents (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  year INTEGER NOT NULL,
  annual_report TEXT
);

CREATE TABLE prosandcons (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  pros TEXT,
  cons TEXT
);

CREATE TABLE sectors (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL UNIQUE REFERENCES companies(id),
  broad_sector TEXT NOT NULL,
  sub_sector TEXT,
  index_weight_pct REAL,
  market_cap_category TEXT
);

CREATE TABLE financial_ratios (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  year TEXT NOT NULL,
  fiscal_year INTEGER,
  net_profit_margin_pct REAL,
  operating_profit_margin_pct REAL,
  return_on_equity_pct REAL,
  debt_to_equity REAL,
  interest_coverage REAL,
  asset_turnover REAL,
  free_cash_flow_cr REAL,
  capex_cr REAL,
  earnings_per_share REAL,
  book_value_per_share REAL,
  dividend_payout_ratio_pct REAL,
  total_debt_cr REAL,
  cash_from_operations_cr REAL,
  return_on_capital_employed_pct REAL,
  return_on_assets_pct REAL,
  high_leverage_flag INTEGER DEFAULT 0,
  icr_label TEXT,
  icr_warning_flag INTEGER DEFAULT 0,
  net_debt_cr REAL,
  revenue_cagr_3yr REAL,
  revenue_cagr_3yr_flag TEXT,
  revenue_cagr_5yr REAL,
  revenue_cagr_5yr_flag TEXT,
  revenue_cagr_10yr REAL,
  revenue_cagr_10yr_flag TEXT,
  pat_cagr_3yr REAL,
  pat_cagr_3yr_flag TEXT,
  pat_cagr_5yr REAL,
  pat_cagr_5yr_flag TEXT,
  pat_cagr_10yr REAL,
  pat_cagr_10yr_flag TEXT,
  eps_cagr_3yr REAL,
  eps_cagr_3yr_flag TEXT,
  eps_cagr_5yr REAL,
  eps_cagr_5yr_flag TEXT,
  eps_cagr_10yr REAL,
  eps_cagr_10yr_flag TEXT,
  cfo_quality_score REAL,
  cfo_quality_label TEXT,
  capex_intensity_pct REAL,
  capex_intensity_label TEXT,
  fcf_conversion_rate_pct REAL,
  capital_allocation_pattern TEXT,
  roce_benchmark_mode TEXT,
  composite_quality_score REAL
);

CREATE TABLE market_cap (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  year INTEGER NOT NULL,
  market_cap_crore REAL,
  enterprise_value_crore REAL,
  pe_ratio REAL,
  pb_ratio REAL,
  ev_ebitda REAL,
  dividend_yield_pct REAL,
  UNIQUE(company_id, year)
);

CREATE TABLE peer_groups (
  id INTEGER PRIMARY KEY,
  peer_group_name TEXT NOT NULL,
  company_id TEXT NOT NULL REFERENCES companies(id),
  is_benchmark INTEGER NOT NULL CHECK(is_benchmark IN (0, 1))
);

CREATE TABLE stock_prices (
  id INTEGER PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(id),
  date TEXT NOT NULL,
  open_price REAL,
  high_price REAL,
  low_price REAL,
  close_price REAL,
  volume INTEGER,
  adjusted_close REAL,
  UNIQUE(company_id, date)
);

CREATE INDEX idx_pl_company_year ON profitandloss(company_id, fiscal_year);
CREATE INDEX idx_bs_company_year ON balancesheet(company_id, fiscal_year);
CREATE INDEX idx_cf_company_year ON cashflow(company_id, fiscal_year);
CREATE INDEX idx_ratios_company_year ON financial_ratios(company_id, fiscal_year);
CREATE INDEX idx_market_cap_company_year ON market_cap(company_id, year);
CREATE INDEX idx_peer_groups_company ON peer_groups(company_id);
CREATE INDEX idx_prices_company_date ON stock_prices(company_id, date);
