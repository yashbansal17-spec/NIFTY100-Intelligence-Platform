-- 01. Company count
SELECT COUNT(*) AS companies FROM companies;

-- 02. Source row counts by loaded table
SELECT 'companies' AS table_name, COUNT(*) AS rows FROM companies UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow UNION ALL
SELECT 'analysis', COUNT(*) FROM analysis UNION ALL
SELECT 'documents', COUNT(*) FROM documents UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons UNION ALL
SELECT 'sectors', COUNT(*) FROM sectors UNION ALL
SELECT 'financial_ratios', COUNT(*) FROM financial_ratios UNION ALL
SELECT 'market_cap', COUNT(*) FROM market_cap UNION ALL
SELECT 'peer_groups', COUNT(*) FROM peer_groups UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices;

-- 03. Top 10 companies by latest annual sales
WITH latest AS (
  SELECT company_id, MAX(fiscal_year) AS fiscal_year FROM profitandloss GROUP BY company_id
)
SELECT p.company_id, c.company_name, p.fiscal_year, p.sales
FROM profitandloss p
JOIN latest l USING (company_id, fiscal_year)
JOIN companies c ON c.id = p.company_id
ORDER BY p.sales DESC
LIMIT 10;

-- 04. Balance-sheet mismatches above 1%
SELECT company_id, year, total_assets, total_liabilities,
       ROUND(ABS(total_assets-total_liabilities), 2) AS difference
FROM balancesheet
WHERE ABS(total_assets-total_liabilities) > MAX(1, ABS(total_assets)*0.01)
ORDER BY difference DESC;

-- 05. Sector coverage
SELECT broad_sector, COUNT(*) AS companies, ROUND(SUM(index_weight_pct), 2) AS index_weight_pct
FROM sectors
GROUP BY broad_sector
ORDER BY companies DESC;

-- 06. Five random companies for manual review
SELECT c.id, c.company_name, s.broad_sector,
       (SELECT COUNT(DISTINCT fiscal_year) FROM profitandloss p WHERE p.company_id = c.id) AS pl_years,
       (SELECT COUNT(DISTINCT fiscal_year) FROM balancesheet b WHERE b.company_id = c.id) AS bs_years,
       (SELECT COUNT(DISTINCT fiscal_year) FROM cashflow cf WHERE cf.company_id = c.id) AS cf_years
FROM companies c
LEFT JOIN sectors s ON s.company_id = c.id
ORDER BY RANDOM()
LIMIT 5;

-- 07. Latest ROE and ROCE from company master
SELECT id, company_name, roe_percentage, roce_percentage
FROM companies
ORDER BY roe_percentage DESC
LIMIT 10;

-- 08. Stock price monthly coverage
SELECT company_id, COUNT(*) AS months, MIN(date) AS first_month, MAX(date) AS last_month
FROM stock_prices
GROUP BY company_id
ORDER BY months DESC, company_id;

-- 09. Latest stock close by company
WITH latest AS (
  SELECT company_id, MAX(date) AS date FROM stock_prices GROUP BY company_id
)
SELECT s.company_id, c.company_name, s.date, s.close_price, s.volume
FROM stock_prices s
JOIN latest l USING (company_id, date)
JOIN companies c ON c.id = s.company_id
ORDER BY s.close_price DESC
LIMIT 10;

-- 10. Companies with fewer than five P&L years
SELECT c.id, c.company_name, COUNT(DISTINCT p.fiscal_year) AS pl_years
FROM companies c
LEFT JOIN profitandloss p ON p.company_id = c.id
GROUP BY c.id, c.company_name
HAVING COUNT(DISTINCT p.fiscal_year) < 5
ORDER BY pl_years, c.id;
