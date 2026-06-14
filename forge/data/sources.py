"""Keyless market-data sources: historical OHLCV and the Fear & Greed index.

Both sources are public and require no API key, so backtests reproduce for anyone:

- OHLCV: ``data-api.binance.vision`` (Binance public mirror), daily candles.
- Fear & Greed: ``api.alternative.me/fng`` (full daily series since 2018-02-01).

Parsing is split from fetching so the parse logic is pure and unit-testable, and
fetch takes an injectable ``http_get`` so tests never touch the network.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

import pandas as pd

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]

BINANCE_VISION_KLINES_URL = "https://data-api.binance.vision/api/v3/klines"
ALTERNATIVE_ME_FNG_URL = "https://api.alternative.me/fng/"

# An http getter takes (url, params) and returns parsed JSON (list or dict).
HttpGet = Callable[[str, Optional[dict]], Any]


def _empty_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(dtype="float64") for c in OHLCV_COLUMNS},
        index=pd.DatetimeIndex([], name="date"),
    )


def parse_binance_klines(raw: list) -> pd.DataFrame:
    """Parse Binance klines (list of arrays) into a daily OHLCV DataFrame.

    Each row is ``[openTime_ms, open, high, low, close, volume, closeTime, ...]``.
    The index is a tz-naive, midnight-normalized, ascending ``DatetimeIndex``.

    Raises ``ValueError`` for a non-list payload (e.g. a Binance ``{"code", "msg"}``
    error object) or rows that don't match the expected kline shape.
    """
    if not isinstance(raw, list):
        raise ValueError(
            f"Binance klines response must be a list, got {type(raw).__name__}: {raw!r}"
        )
    if not raw:
        return _empty_ohlcv()

    try:
        index = pd.to_datetime([row[0] for row in raw], unit="ms").normalize()
        frame = pd.DataFrame(
            {
                "open": [float(r[1]) for r in raw],
                "high": [float(r[2]) for r in raw],
                "low": [float(r[3]) for r in raw],
                "close": [float(r[4]) for r in raw],
                "volume": [float(r[5]) for r in raw],
            },
            index=pd.DatetimeIndex(index, name="date"),
        )
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Malformed Binance klines payload: {exc}") from exc

    # Drop duplicate days (keep the latest), guarantee ascending order.
    return frame[~frame.index.duplicated(keep="last")].sort_index()


def parse_fear_greed(raw: dict) -> pd.Series:
    """Parse an alternative.me Fear & Greed payload into a daily int Series.

    The index is a tz-naive, midnight-normalized, ascending ``DatetimeIndex``;
    the series is named ``fear_greed`` with integer values in [0, 100].
    """
    if not isinstance(raw, dict):
        raise ValueError(
            f"Fear & Greed response must be a dict, got {type(raw).__name__}: {raw!r}"
        )
    data = raw.get("data", [])
    if not data:
        return pd.Series(
            dtype="int64",
            index=pd.DatetimeIndex([], name="date"),
            name="fear_greed",
        )

    try:
        index = pd.to_datetime([int(d["timestamp"]) for d in data], unit="s").normalize()
        series = pd.Series(
            [int(d["value"]) for d in data],
            index=pd.DatetimeIndex(index, name="date"),
            name="fear_greed",
        )
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Malformed Fear & Greed payload: {exc}") from exc

    return series[~series.index.duplicated(keep="last")].sort_index()


def _to_ms(when: Any) -> int:
    """Convert a date-like value to a UTC epoch in milliseconds (tz-safe)."""
    ts = pd.Timestamp(when)
    if ts.tz is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return int((ts - pd.Timestamp("1970-01-01")) // pd.Timedelta(milliseconds=1))


# A legitimate response (full Fear&Greed history, one OHLCV page) is well under this.
_MAX_RESPONSE_BYTES = 32 * 1024 * 1024


def _default_http_get(url: str, params: Optional[dict] = None, timeout: int = 30) -> Any:
    import json as _json

    import requests  # imported lazily so tests that inject http_get need no network stack

    resp = requests.get(url, params=params, timeout=timeout, stream=True)
    resp.raise_for_status()
    body = resp.raw.read(_MAX_RESPONSE_BYTES + 1, decode_content=True)
    if len(body) > _MAX_RESPONSE_BYTES:
        raise ValueError(f"response from {url!r} exceeds {_MAX_RESPONSE_BYTES} bytes")
    return _json.loads(body)


def fetch_ohlcv(
    symbol: str,
    interval: str = "1d",
    start: Any = None,
    end: Any = None,
    limit: int = 1000,
    http_get: Optional[HttpGet] = None,
) -> pd.DataFrame:
    """Fetch daily OHLCV for ``symbol`` (e.g. ``"BNBUSDT"``) from binance.vision."""
    getter = http_get or _default_http_get
    params: dict[str, Any] = {"symbol": symbol, "interval": interval, "limit": limit}
    if start is not None:
        params["startTime"] = _to_ms(start)
    if end is not None:
        params["endTime"] = _to_ms(end)
    return parse_binance_klines(getter(BINANCE_VISION_KLINES_URL, params))


_INTERVAL_TO_TIMEDELTA = {
    "1m": pd.Timedelta(minutes=1),
    "3m": pd.Timedelta(minutes=3),
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "30m": pd.Timedelta(minutes=30),
    "1h": pd.Timedelta(hours=1),
    "2h": pd.Timedelta(hours=2),
    "4h": pd.Timedelta(hours=4),
    "6h": pd.Timedelta(hours=6),
    "12h": pd.Timedelta(hours=12),
    "1d": pd.Timedelta(days=1),
    "1w": pd.Timedelta(weeks=1),
}


def fetch_ohlcv_history(
    symbol: str,
    interval: str = "1d",
    start: Any = None,
    end: Any = None,
    page_limit: int = 1000,
    http_get: Optional[HttpGet] = None,
    max_pages: int = 200,
) -> pd.DataFrame:
    """Fetch OHLCV across multiple pages (the API caps each call at ~1000 bars).

    Pages forward from ``start``, advancing one interval past the last bar of each
    full page, stopping on a short/empty page, on reaching ``end``, or ``max_pages``.

    With ``start=None`` there is no anchor to page from, so a single most-recent
    page (up to ``page_limit`` bars) is returned without forward paging.
    """
    getter = http_get or _default_http_get
    step = _INTERVAL_TO_TIMEDELTA.get(interval)
    if step is None:
        raise ValueError(
            f"Unsupported interval {interval!r}. Supported: {list(_INTERVAL_TO_TIMEDELTA)}"
        )

    if start is None:
        return fetch_ohlcv(symbol, interval=interval, end=end, limit=page_limit, http_get=getter)

    frames: list[pd.DataFrame] = []
    cursor: Any = start

    for _ in range(max_pages):
        page = fetch_ohlcv(
            symbol, interval=interval, start=cursor, end=end,
            limit=page_limit, http_get=getter,
        )
        if page.empty:
            break
        frames.append(page)
        if len(page) < page_limit:
            break
        cursor = page.index[-1] + step
        if end is not None and cursor > pd.Timestamp(end):
            break

    if not frames:
        return _empty_ohlcv()

    out = pd.concat(frames)
    out = out[~out.index.duplicated(keep="last")].sort_index()
    if start is not None:
        out = out[out.index >= pd.Timestamp(start)]
    if end is not None:
        out = out[out.index <= pd.Timestamp(end)]
    return out


def fetch_fear_greed(
    start: Any = None,
    end: Any = None,
    http_get: Optional[HttpGet] = None,
) -> pd.Series:
    """Fetch the full Fear & Greed history, optionally clipped to [start, end]."""
    getter = http_get or _default_http_get
    series = parse_fear_greed(getter(ALTERNATIVE_ME_FNG_URL, {"limit": 0, "format": "json"}))
    if start is not None:
        series = series[series.index >= pd.Timestamp(start)]
    if end is not None:
        series = series[series.index <= pd.Timestamp(end)]
    return series
