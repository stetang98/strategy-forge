"""Strategy Forge — crypto strategy generation + backtesting engine.

The ``forge`` package is the tested, importable engine behind the Strategy Forge
Skill. Layers:

- ``forge.data``      — keyless market data (OHLCV, Fear & Greed) behind one interface
- ``forge.strategy``  — the StrategySpec IR, pure signal functions, regime detection
- ``forge.backtest``  — the vectorbt-backed engine and walk-forward validation
"""

__version__ = "0.1.0"
