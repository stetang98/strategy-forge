"""Top-level orchestration: a strategy spec in, a backtest report out.

This is the testable core behind ``scripts/backtest.py`` (the Skill's black-box
script). The data loader is injectable so the orchestration is unit-tested without
network access; in production it defaults to the keyless reproducible loader.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from forge.backtest import engine, report
from forge.data import loader as _loader
from forge.strategy.spec import StrategySpec

DataLoader = Callable[..., pd.DataFrame]

# Fewer rows than this cannot produce a meaningful backtest (lookbacks + warmup).
MIN_ROWS = 30


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
    return {"result": result, "summary": report.result_to_dict(result), "paths": paths}
