.PHONY: install test cov backtest demo clean

VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

test:
	$(PY) -m pytest

cov:
	$(PY) -m pytest --cov=forge --cov-report=term-missing

# Run the headline strategy backtest from its spec
backtest:
	$(PY) scripts/backtest.py --spec assets/regime-momentum.json --out examples

# Backtest the baseline the headline beats
demo:
	$(PY) scripts/backtest.py --spec assets/regime-momentum.json --out examples
	$(PY) scripts/backtest.py --spec assets/fgi-contrarian.json --out examples

clean:
	rm -rf .forge_cache .pytest_cache .coverage htmlcov **/__pycache__
