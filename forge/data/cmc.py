"""CoinMarketCap Agent Hub provider.

When a CMC API key is present, this lights up two things the keyless path can't:

1. A **live market-context readout** (current Fear & Greed, price, BTC/ETH dominance,
   total market cap) — the visible "Best Use of Agent Hub" moment in the demo.
2. An optional CMC-sourced Fear & Greed series for backtests, as a drop-in replacement
   for the keyless source (same shape, so it slots straight into the loader).

The client is `coinmarketcapapi` (the rsz44 wrapper), which supports a `sandbox=True`
mode (public test key) used to verify plumbing without a real key. All extraction is
defensive so a missing field degrades to ``None`` rather than crashing a demo.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

import pandas as pd

_log = logging.getLogger(__name__)


def make_client(api_key: Optional[str] = None, sandbox: bool = False) -> Any:
    """Construct a CoinMarketCap API client (lazy import keeps it an optional dep)."""
    import coinmarketcapapi

    return coinmarketcapapi.CoinMarketCapAPI(api_key, sandbox=sandbox)


def parse_cmc_fear_greed(data: list) -> pd.Series:
    """Parse CMC v3 fear-and-greed records into a daily int Series (same shape as the
    keyless source): tz-naive, midnight-normalized, ascending, named ``fear_greed``.
    """
    valid = [d for d in data if isinstance(d, dict) and "timestamp" in d and "value" in d]
    if not valid:
        return pd.Series(dtype="int64", index=pd.DatetimeIndex([], name="date"), name="fear_greed")
    index = pd.to_datetime([int(d["timestamp"]) for d in valid], unit="s").normalize()
    series = pd.Series(
        [int(d["value"]) for d in valid],
        index=pd.DatetimeIndex(index, name="date"),
        name="fear_greed",
    )
    # CMC historical returns newest-first; keep='first' retains the most recent revision.
    return series[~series.index.duplicated(keep="first")].sort_index()


def fetch_fear_greed_cmc(client: Any, start: Any = None, end: Any = None,
                         limit: int = 500) -> pd.Series:
    """Fetch the CMC Fear & Greed history via ``client``, clipped to [start, end].

    Note: ``limit`` caps the API response (~500 days of daily data from today). For
    longer backtests the keyless ``alternative.me`` source has full history since 2018;
    this CMC source is best for the live signal and recent windows.
    """
    resp = client.fearandgreed_historical(limit=limit)
    raw = getattr(resp, "data", []) or []
    if len(raw) >= limit:
        _log.warning("CMC Fear & Greed hit the limit=%d cap; older history truncated.", limit)
    series = parse_cmc_fear_greed(raw)
    if start is not None:
        series = series[series.index >= pd.Timestamp(start)]
    if end is not None:
        series = series[series.index <= pd.Timestamp(end)]
    return series


def make_fng_fetcher(client: Any) -> Callable[..., pd.Series]:
    """Adapt a CMC client into the loader's ``fng_fetcher(start, end)`` signature."""
    def _fetch(start: Any = None, end: Any = None) -> pd.Series:
        return fetch_fear_greed_cmc(client, start=start, end=end)
    return _fetch


def live_market_context(client: Any, symbol: str) -> dict[str, Any]:
    """Pull a current market snapshot from CMC for the demo (defensive: missing → None)."""
    ctx: dict[str, Any] = {
        "symbol": symbol, "price": None, "percent_change_24h": None,
        "fear_greed": None, "fear_greed_label": None,
        "btc_dominance": None, "eth_dominance": None, "total_market_cap": None,
    }

    try:
        d = client.fearandgreed_latest().data
        ctx["fear_greed"] = int(d["value"])
        ctx["fear_greed_label"] = d.get("value_classification")
    except Exception as exc:
        _log.debug("CMC fear&greed latest unavailable: %s", exc)

    try:
        entry = client.cryptocurrency_quotes_latest(symbol=symbol).data[symbol]
        if isinstance(entry, list):
            entry = entry[0]
        usd = entry["quote"]["USD"]
        ctx["price"] = float(usd["price"])
        ctx["percent_change_24h"] = usd.get("percent_change_24h")
    except Exception as exc:
        _log.debug("CMC quotes for %s unavailable: %s", symbol, exc)

    try:
        g = client.globalmetrics_quotes_latest().data
        ctx["btc_dominance"] = g.get("btc_dominance")
        ctx["eth_dominance"] = g.get("eth_dominance")
        ctx["total_market_cap"] = g.get("quote", {}).get("USD", {}).get("total_market_cap")
    except Exception as exc:
        _log.debug("CMC global metrics unavailable: %s", exc)

    return ctx
