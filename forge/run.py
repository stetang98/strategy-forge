"""Top-level orchestration: a strategy spec in, a backtest report out.

This is the testable core behind ``scripts/backtest.py`` (the Skill's black-box
script). The data loader is injectable so the orchestration is unit-tested without
network access; in production it defaults to the keyless reproducible loader.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from forge import env as _env
from forge.backtest import engine, report
from forge.data import loader as _loader
from forge.strategy.spec import StrategySpec

_log = logging.getLogger(__name__)

DataLoader = Callable[..., pd.DataFrame]

# Fewer rows than this cannot produce a meaningful backtest (lookbacks + warmup).
MIN_ROWS = 30

# Quote suffixes to strip so a Binance pair maps to a CMC base symbol (BNBUSDT -> BNB).
_QUOTE_SUFFIXES = ("FDUSD", "USDT", "USDC", "BUSD", "TUSD", "USD")
_STABLECOINS = {"USDT", "USDC", "BUSD", "TUSD", "FDUSD", "USD", "DAI", "FRAX"}


def _base_symbol(pair: str) -> str:
    """Map a Binance pair to its CMC base symbol (BNBUSDT -> BNB), checking longer
    quote suffixes first and leaving a bare stablecoin untouched (FDUSD stays FDUSD)."""
    if pair in _STABLECOINS:
        return pair
    for suffix in sorted(_QUOTE_SUFFIXES, key=len, reverse=True):
        if pair.endswith(suffix) and len(pair) - len(suffix) >= 2:
            return pair[: -len(suffix)]
    return pair


def live_cmc_context(symbol: str) -> dict[str, Any] | None:
    """Live CMC market snapshot for ``symbol`` when CMC_API_KEY is set, else None.

    This is what makes every backtest run *use* the CoinMarketCap Agent Hub: the
    reproducible backtest stays keyless, but each run is annotated with a real,
    live CMC reading (Fear & Greed, dominance, price). Never raises.
    """
    _env.load_dotenv()
    key = os.environ.get("CMC_API_KEY")
    if not key:
        return None
    try:
        from forge.data import cmc
    except ImportError:
        _log.warning("coinmarketcapapi not installed; run `pip install -e .[cmc]` for CMC context")
        return None
    try:
        return cmc.live_market_context(cmc.make_client(key), _base_symbol(symbol))
    except Exception as exc:  # never let an optional live readout break a backtest
        _log.debug("CMC live context unavailable: %s", exc)
        return None


def load_spec(path: Path | str) -> StrategySpec:
    """Read and validate a StrategySpec from a JSON file."""
    return StrategySpec.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))


def _needs_fear_greed(spec: StrategySpec) -> bool:
    # Keep in sync with every _require(df, "fear_greed", ...) call in backtest/pipeline.py.
    return spec.sentiment_overlay.enabled or spec.signal.type == "fng_contrarian"


def run_spec(spec: StrategySpec, out_dir: Path | str,
             data_loader: DataLoader | None = None) -> dict[str, Any]:
    """Load data for ``spec``, backtest it, write the report, return a summary bundle."""
    fetch = data_loader or _loader.load_market_data
    df = fetch(
        spec.symbol,
        start=spec.start,
        end=spec.end,
        interval=spec.interval,
        with_fear_greed=_needs_fear_greed(spec),
    )
    if len(df) < MIN_ROWS:
        raise ValueError(
            f"market frame for {spec.symbol} has only {len(df)} rows; "
            f"need at least {MIN_ROWS} for a meaningful backtest"
        )
    result = engine.run_backtest(df, spec)
    paths = report.write_report(result, out_dir, basename=spec.name)
    summary = report.result_to_dict(result)
    summary["cmc_context"] = live_cmc_context(spec.symbol)  # live CMC reading, or None
    return {"result": result, "summary": summary, "paths": paths}
