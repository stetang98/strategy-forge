"""Compose a StrategySpec + market data into executable target weights.

Three steps, kept separate and pure so each is unit-testable:

1. ``base_position``           — the raw long/flat mask for the chosen signal family.
2. ``compute_decision_weights`` — gate by regime, size, and tilt by sentiment, giving
   the target weight the strategy *decides* on at each bar's close.
3. ``to_execution_weights``     — shift decisions forward one bar so trades execute on
   the *next* bar. This is what makes the whole backtest look-ahead safe: no decision
   is ever acted on within the same bar that produced it.
"""
from __future__ import annotations

import pandas as pd

from forge.strategy import signals
from forge.strategy.spec import StrategySpec


def _require(df: pd.DataFrame, column: str, why: str) -> pd.Series:
    if column not in df.columns:
        raise ValueError(f"market data is missing '{column}' column required for {why}")
    return df[column]


def base_position(df: pd.DataFrame, spec: StrategySpec) -> pd.Series:
    """The raw long/flat boolean mask for the configured signal family."""
    sig = spec.signal
    close = _require(df, "close", "the price signal")
    if sig.type == "ts_momentum":
        return signals.ts_momentum_position(close, sig.lookback_days, sig.fast_ma, sig.slow_ma)
    if sig.type == "ema_crossover":
        return signals.ema_crossover_position(close, sig.fast_ma, sig.slow_ma)
    if sig.type == "fng_contrarian":
        fng = _require(df, "fear_greed", "the fng_contrarian signal")
        return signals.fng_contrarian_position(fng, sig.fng_buy_below, sig.fng_sell_above)
    raise ValueError(f"unknown signal type {sig.type!r}")  # pragma: no cover - spec validates


def _size_weights(df: pd.DataFrame, spec: StrategySpec) -> pd.Series:
    close = df["close"]
    sz = spec.sizing
    if sz.type == "vol_target":
        return signals.vol_target_weight(close, sz.target_vol, sz.vol_lookback_days, sz.max_leverage)
    if sz.type == "full":
        return pd.Series(sz.max_leverage, index=close.index, dtype="float64")
    if sz.type == "fixed_fraction":
        return pd.Series(sz.fraction, index=close.index, dtype="float64")
    raise ValueError(f"unknown sizing type {sz.type!r}")  # pragma: no cover - spec validates


def compute_decision_weights(df: pd.DataFrame, spec: StrategySpec,
                             is_trend: pd.Series) -> pd.Series:
    """Target weight the strategy decides on at each bar (pre-execution-shift)."""
    base = base_position(df, spec)
    tradeable = (base & is_trend) if spec.regime_gate.enabled else base

    weight = _size_weights(df, spec)
    if spec.sentiment_overlay.enabled:
        ov = spec.sentiment_overlay
        fng = _require(df, "fear_greed", "the sentiment overlay")
        weight = weight * signals.sentiment_scale(
            fng, ov.fng_extreme_fear, ov.fng_extreme_greed, ov.fear_boost, ov.greed_trim
        )

    weight = weight.where(tradeable, 0.0)
    return weight.clip(lower=0.0, upper=spec.sizing.max_leverage).fillna(0.0)


def to_execution_weights(weights: pd.Series) -> pd.Series:
    """Shift decisions one bar forward so trades execute on the next bar (no look-ahead)."""
    return weights.shift(1).fillna(0.0)
