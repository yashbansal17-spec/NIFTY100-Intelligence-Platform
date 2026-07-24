# NIFTY100 Intelligence Platform

This project contains the Sprint 1-5 implementation for the NIFTY100 Intelligence Platform:

- Sprint 1: data foundation, SQLite ETL, schema, audit files, DQ validation.
- Sprint 2: financial ratio engine and cash-flow KPI calculations.
- Sprint 3: screener presets, peer percentiles, Excel exports, radar charts.
- Sprint 4: Streamlit dashboard and valuation module.
- Sprint 5: NLP pros/cons, cash-flow intelligence, company tearsheets, sector reports, portfolio PDF.
- Sprint 6: KMeans clustering, FastAPI endpoints, OpenAPI/Postman export, final QA, acceptance gates, and final deliverables archive.

## Run The Full Data Pipeline

```powershell
python src/etl/loader.py --data-dir data\excel --db output\nifty100.db --audit output\load_audit.csv
python src/etl/validator.py --db output\nifty100.db --failures output\validation_failures.csv
python src/analytics/populate_ratios.py --db output\nifty100.db --output-dir output
python src/screener/run_sprint3.py --db output\nifty100.db --config config\screener_config.yaml --output-dir output --reports-dir reports
python src/analytics/valuation.py --db output\nifty100.db --output-dir output
python src/nlp/parser.py --db output\nifty100.db --output-dir output
python src/nlp/pros_cons_generator.py --db output\nifty100.db --output-dir output
python src/analytics/cashflow_kpis.py --db output\nifty100.db --output-dir output
python src/reports/tearsheet.py --db output\nifty100.db --output-dir output --reports-dir reports
python src/reports/sector_report.py --db output\nifty100.db --reports-dir reports
python src/analytics/clustering.py --db output\nifty100.db --output-dir output --reports-dir reports
python src/api/export_docs.py
python src/finalize_sprint6.py --root .
```

## Run Tests

```powershell
python -m unittest discover -s tests\etl -p "test_*.py"
python -m unittest discover -s tests\kpi -p "test_*.py"
python -m unittest discover -s tests\screener -p "test_*.py"
```

## Run Dashboard

```powershell
streamlit run src/dashboard/app.py
```

The dashboard runs on `localhost:8501` with wide layout and sidebar navigation.

## Run API

```powershell
uvicorn src.api.main:app --port 8000
```

Health check:

```powershell
curl http://localhost:8000/api/v1/health
```

OpenAPI docs are available at `http://localhost:8000/docs` when the API is running.

## Dashboard Screens

1. Home: six KPI tiles, sector breakdown donut chart, top 5 companies by composite score, year selector from 2019 to 2024.
2. Company Profile: company/ticker search, profile card, six KPI tiles, revenue/net profit bars, ROE/ROCE line chart, pros and cons badges.
3. Screener: ten metric sliders, six preset buttons, live results table, result count, CSV download.
4. Peers: peer group selector, selected company radar chart versus peer average, benchmark-highlighted KPI table.
5. Trends: company search, up to three overlay metrics, 10-year line chart with YoY annotations.
6. Sectors: sector dropdown, revenue versus ROE bubble chart, sector median KPI bar chart.
7. Capital Allocation: treemap of all companies by allocation pattern and sector, plus pattern company list.
8. Reports: company search and clickable BSE annual report PDF links with unavailable badges for failed links.

## Key Outputs

- `output/nifty100.db`
- `output/load_audit.csv`
- `output/validation_failures.csv`
- `output/screener_output.xlsx`
- `output/peer_comparison.xlsx`
- `output/valuation_summary.xlsx`
- `output/valuation_flags.csv`
- `output/analysis_parsed.csv`
- `output/parse_failures.csv`
- `output/pros_cons_generated.csv`
- `output/cashflow_intelligence.xlsx`
- `output/distress_alerts.csv`
- `output/pattern_changes.csv`
- `reports/radar_charts/`
- `reports/tearsheets/`
- `reports/sector/`
- `reports/portfolio/portfolio_summary.pdf`
- `output/cluster_labels.csv`
- `reports/elbow_plot.png`
- `reports/correlation_heatmap.png`
- `output/outlier_report.csv`
- `output/portfolio_stats.csv`
- `docs/openapi.json`
- `docs/postman_collection.json`
- `docs/analyst_guide.pdf`
- `docs/acceptance_checklist.pdf`
- `output/final_deliverables/`

## Notes

The project uses `data/excel` as the source-data folder and `output` plus `reports` for generated deliverables. The supplied company master contains 92 companies, and all downstream sprint outputs are generated from that company universe.
