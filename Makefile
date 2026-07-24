PYTHON ?= python
DATA_DIR ?= data/excel

.PHONY: load validate ratios sprint3 valuation sprint5 sprint6 test report dashboard api clean

load:
	$(PYTHON) src/etl/loader.py --data-dir "$(DATA_DIR)" --db output/nifty100.db --audit output/load_audit.csv

validate:
	$(PYTHON) src/etl/validator.py --db output/nifty100.db --failures output/validation_failures.csv

ratios:
	$(PYTHON) src/analytics/populate_ratios.py --db output/nifty100.db --output-dir output

sprint3:
	$(PYTHON) src/screener/run_sprint3.py --db output/nifty100.db --config config/screener_config.yaml --output-dir output --reports-dir reports

valuation:
	$(PYTHON) src/analytics/valuation.py --db output/nifty100.db --output-dir output

sprint5:
	$(PYTHON) src/nlp/parser.py --db output/nifty100.db --output-dir output
	$(PYTHON) src/nlp/pros_cons_generator.py --db output/nifty100.db --output-dir output
	$(PYTHON) src/analytics/cashflow_kpis.py --db output/nifty100.db --output-dir output
	$(PYTHON) src/reports/tearsheet.py --db output/nifty100.db --output-dir output --reports-dir reports
	$(PYTHON) src/reports/sector_report.py --db output/nifty100.db --reports-dir reports

sprint6:
	$(PYTHON) src/analytics/clustering.py --db output/nifty100.db --output-dir output --reports-dir reports
	$(PYTHON) src/api/export_docs.py
	$(PYTHON) src/finalize_sprint6.py --root .

test:
	$(PYTHON) -m unittest discover -s tests/etl -p "test_*.py"
	$(PYTHON) -m unittest discover -s tests/kpi -p "test_*.py"
	$(PYTHON) -m unittest discover -s tests/screener -p "test_*.py"

report:
	$(PYTHON) src/etl/loader.py --data-dir "$(DATA_DIR)" --db output/nifty100.db --audit output/load_audit.csv
	$(PYTHON) src/etl/validator.py --db output/nifty100.db --failures output/validation_failures.csv
	$(PYTHON) src/analytics/populate_ratios.py --db output/nifty100.db --output-dir output
	$(PYTHON) src/screener/run_sprint3.py --db output/nifty100.db --config config/screener_config.yaml --output-dir output --reports-dir reports
	$(PYTHON) src/analytics/valuation.py --db output/nifty100.db --output-dir output
	$(PYTHON) src/nlp/parser.py --db output/nifty100.db --output-dir output
	$(PYTHON) src/nlp/pros_cons_generator.py --db output/nifty100.db --output-dir output
	$(PYTHON) src/analytics/cashflow_kpis.py --db output/nifty100.db --output-dir output

dashboard:
	streamlit run src/dashboard/app.py

api:
	uvicorn src.api.main:app --port 8000

clean:
	$(PYTHON) -c "import pathlib; [p.unlink() for p in pathlib.Path('output').glob('*') if p.is_file()]"
