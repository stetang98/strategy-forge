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
	$(PY) scripts/backtest.py --spec assets/trend-rider.json --out examples

# The full demo: headline on BNB, the same strategy surviving CAKE's crash,
# the risk-managed variant, and the baseline they beat.
demo:
	$(PY) scripts/backtest.py --spec assets/trend-rider.json --out examples
	$(PY) scripts/backtest.py --spec assets/cake-trend-rider.json --out examples
	$(PY) scripts/backtest.py --spec assets/regime-guard.json --out examples
	$(PY) scripts/backtest.py --spec assets/fgi-contrarian.json --out examples

clean:
	rm -rf .forge_cache .pytest_cache .coverage htmlcov **/__pycache__
