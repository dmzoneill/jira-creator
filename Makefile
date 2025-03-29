# --- Variables ---
PYTHON ?= python
PIPENV ?= pipenv
SCRIPT := rh-jira.py

# --- Setup & Install ---
.PHONY: install
install:
	$(PIPENV) install --dev

.PHONY: setup
setup: install
	@echo "✅ Virtualenv and dependencies ready."

# --- Run Script ---
.PHONY: run
run:
	$(PIPENV) run $(PYTHON) $(SCRIPT)

.PHONY: dry-run
dry-run:
	$(PIPENV) run $(PYTHON) $(SCRIPT) bug "Dry run summary" --dry-run

# --- Tests ---
.PHONY: test
test:
	PYTHONPATH=. pipenv run pytest tests

.PHONY: test-watch
test-watch:
	$(PIPENV) run ptw --onfail "notify-send 'Tests failed!'"

# --- Lint ---
.PHONY: lint
lint:
	$(PIPENV) run black . --check
	$(PIPENV) run flake8 . --ignore=E501,F401,W503


.PHONY: format
format:
	pipenv run autopep8 . --recursive --in-place --aggressive --aggressive
	pipenv run black .

# Run tests with coverage, including subprocess tracking
.PHONY: coverage
coverage:
	pipenv run coverage erase
	PYTHONPATH=. COVERAGE_PROCESS_START=.coveragerc pipenv run coverage run -m pytest tests
	pipenv run coverage combine
	pipenv run coverage report -m --fail-under=99
	pipenv run coverage html
	@echo "📂 Coverage report: open htmlcov/index.html"


# Clean up coverage artifacts
clean-coverage:
	rm -rf .coverage htmlcov

# --- Clean ---
.PHONY: clean
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# --- Help ---
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make install     - Install dependencies"
	@echo "  make setup       - Setup the environment"
	@echo "  make run         - Run the script"
	@echo "  make dry-run     - Run script in dry-run mode"
	@echo "  make test        - Run all unit tests"
	@echo "  make lint        - Run format checks"
	@echo "  make format      - Auto-format code"
	@echo "  make clean       - Remove __pycache__ and *.pyc files"
