.PHONY: install init seed run test eval demo-burst clean

install:
	py -3.11 -m pip install -r requirements.txt

init:
	py -3.11 scripts/init_db.py

seed:
	py -3.11 scripts/seed.py

run:
	py -3.11 app/main.py

test:
	py -3.11 -m pytest tests/ -v

unit:
	py -3.11 -m pytest tests/test_classifier.py tests/test_geo.py -v

eval:
	py -3.11 scripts/evaluate.py

demo-burst:
	py -3.11 scripts/demo_burst.py

clean:
	rm -f grievance_router.db grievance_router.db-journal
	rm -rf __pycache__ .pytest_cache
	rm -rf app/__pycache__ app/*/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

help:
	@echo "Grievance Router - Available commands:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make init         - Initialize database"
	@echo "  make seed         - Seed test data"
	@echo "  make run          - Start the application"
	@echo "  make test         - Run all tests"
	@echo "  make unit         - Run unit tests only"
	@echo "  make eval         - Run model evaluation"
	@echo "  make demo-burst   - Run demo spike scenario"
	@echo "  make clean        - Clean generated files"
