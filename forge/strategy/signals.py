"""Pure, composable signal and sizing functions.

Every function here is a pure transformation of price/sentiment Series into a
signal or weight Series — no I/O, no global state — so they are trivially
unit-testable and free of look-ahead by construction (each value at bar *t* uses
only data at or before *t*; decision/execution offset is applied by the engine).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Crypto trades 24/7, so a "year" is 365 daily bars (not 252).
TRADING_DAYS_PER_YEAR = 365


def trailing_return(close: pd.Series, lookback: int) -> pd.Series:
    """Simple return over ``lookback`` bars: ``close_t / close_{t-lookback} - 1``."""
    return close / close.shift(lookback) - 1.0


def realized_vol(close: pd.Series, lookback: int,
                 periods_per_year: int = TRADING_DAYS_PER_YEAR) -> pd.Series:
    """Annualized realized volatility from rolling std of simple returns."""
    returns = close.pct_change(fill_method=None)  # do not silently forward-fill NaN gaps
    return returns.rolling(lookback).std() * np.sqrt(periods_per_year)


def ts_momentum_position(close: pd.Series, lookback_days: int,
                         fast_ma: int, slow_ma: int) -> pd.Series:
    """Time-series momentum: long when trailing return > 0 AND fast SMA > slow SMA."""
    positive_momentum = trailing_return(close, lookback_days) > 0
    fast = close.rolling(fast_ma).mean()
    slow = close.rolling(slow_ma).mean()
    uptrend = fast > slow
    return (positive_momentum & uptrend).fillna(False).astype(bool)


def ema_crossover_position(close: pd.Series, fast_ma: int, slow_ma: int) -> pd.Series:
    """Long while the fast EMA is above the slow EMA."""
    fast = close.ewm(span=fast_ma, adjust=False).mean()
    slow = close.ewm(span=slow_ma, adjust=False).mean()
    return (fast > slow).fillna(False).astype(bool)


def fng_contrarian_position(fng: pd.Series, buy_below: int, sell_above: int) -> pd.Series:
    """Contrarian state machine: accumulate at/below ``buy_below``, exit at/above
    ``sell_above``, and hold the last state in between (no look-ahead — pure ffill).
    """
    raw = pd.Series(np.nan, index=fng.index, dtype="float64")
    raw[fng <= buy_below] = 1.0
    raw[fng >= sell_above] = 0.0
    held = raw.ffill().fillna(0.0)
    return (held > 0).astype(bool)


def sentiment_scale(fng: pd.Series, extreme_fear: int, extreme_greed: int,
                    fear_boost: float = 1.0, greed_trim: float = 0.5) -> pd.Series:
    """Exposure multiplier from sentiment: boost in extreme fear, trim in extreme greed.

    Note the function default ``fear_boost=1.0`` is reduce-only (greed trim only); the
    pipeline passes ``StrategySpec.sentiment_overlay.fear_boost`` (default 1.15) for a
    genuinely two-sided overlay.
    """
    scale = pd.Series(1.0, index=fng.index, dtype="float64")
    scale[fng <= extreme_fear] = fear_boost
    scale[fng >= extreme_greed] = greed_trim
    return scale


def vol_target_weight(close: pd.Series, target_vol: float, vol_lookback: int,
                      max_leverage: float = 1.0) -> pd.Series:
    """Volatility-targeted exposure: ``target_vol / realized_vol``, clipped to
    ``[0, max_leverage]``. Zero-vol bars clip to ``max_leverage`` (no blow-up);
    bars without enough history to estimate vol get weight 0.
    """
    vol = realized_vol(close, vol_lookback)
    with np.errstate(divide="ignore", invalid="ignore"):
        weight = target_vol / vol
    # Constant-price (zero vol) -> fully confident, capped at max_leverage.
    weight = weight.where(vol != 0, max_leverage)
    weight = weight.clip(lower=0.0, upper=max_leverage)
    return weight.fillna(0.0)
