"""Assemble a validated market frame from keyless sources.

``load_market_data`` left-joins the Fear & Greed series onto an OHLCV frame and
forward-fills it (carrying the last known reading forward — never backward, to
avoid look-ahead), then runs boundary validation. Fetchers are injectable so the
join/validation logic is unit-tested without network access.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

import pandas as pd

from forge.data import sources

OhlcvFetcher = Callable[..., pd.DataFrame]
FngFetcher = Callable[..., pd.Series]


def validate_market_frame(df: Optional[pd.DataFrame], require_fear_greed: bool = True) -> None:
    """Validate a market frame at the boundary; raise ``ValueError`` on any problem.

    Checks: non-empty, required columns present, a unique monotonic-increasing
    ``DatetimeIndex``, and no NaN in price (or Fear & Greed when required).
    """
    if df is None or df.empty:
        raise ValueError("market frame is empty")

    required = list(sources.OHLCV_COLUMNS)
    if require_fear_greed:
        required.append("fear_greed")
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"market frame missing required column(s): {missing}")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("market frame index must be a DatetimeIndex")
    if df.index.has_duplicates:
        raise ValueError("market frame index has duplicate timestamps")
    if not df.index.is_monotonic_increasing:
        raise ValueError("market frame index must be monotonic increasing")

    nan_cols = [c for c in required if df[c].isna().any()]
    if nan_cols:
        raise ValueError(f"market frame has NaN values in column(s): {nan_cols}")


def load_market_data(
    symbol: str,
    start: Any = None,
    end: Any = None,
    interval: str = "1d",
    with_fear_greed: bool = True,
    ohlcv_fetcher: Optional[OhlcvFetcher] = None,
    fng_fetcher: Optional[FngFetcher] = None,
) -> pd.DataFrame:
    """Load a validated OHLCV(+Fear&Greed) frame for ``symbol``.

    Returns a DataFrame indexed by date with columns
    ``open, high, low, close, volume[, fear_greed]``.

    Note on look-ahead: the Fear & Greed reading for date D is dated to D (the day
    it reflects) and only forward-filled, never back-filled. Decision/execution
    timing (decide on bar D, act on bar D+1) is enforced in the backtest engine so
    *every* signal — not just sentiment — is look-ahead safe.
    """
    fetch_ohlcv = ohlcv_fetcher or sources.fetch_ohlcv_history
    fetch_fng = fng_fetcher or sources.fetch_fear_greed

    df = fetch_ohlcv(symbol, interval=interval, start=start, end=end).copy()

    if with_fear_greed:
        fng = fetch_fng(start=start, end=end)
        df = df.join(fng, how="left")
        df["fear_greed"] = df["fear_greed"].ffill()
        # Drop any leading rows before the first available Fear & Greed reading
        # (cannot trade the signal there, and back-filling would leak the future).
        df = df.dropna(subset=["fear_greed"])
        df["fear_greed"] = df["fear_greed"].astype("int64")

    validate_market_frame(df, require_fear_greed=with_fear_greed)
    return df
