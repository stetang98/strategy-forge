"""Tests for forge.data.cmc — the CoinMarketCap Agent Hub provider.

Network is never touched: a fake client mirrors the `coinmarketcapapi` response
shape (objects exposing `.data`). Real-key shapes are verified separately against
the live API; these tests pin the parsing/extraction logic.
"""
import pandas as pd

from forge.data import cmc


class _Resp:
    def __init__(self, data):
        self.data = data


class _FakeCMC:
    """Mimics coinmarketcapapi.CoinMarketCapAPI for the methods we call."""

    def __init__(self, *, fng_hist=None, fng_latest=None, quotes=None, global_metrics=None):
        self._fng_hist = fng_hist or []
        self._fng_latest = fng_latest
        self._quotes = quotes
        self._gm = global_metrics

    def fearandgreed_historical(self, **kw):
        return _Resp(self._fng_hist)

    def fearandgreed_latest(self, **kw):
        return _Resp(self._fng_latest)

    def cryptocurrency_quotes_latest(self, **kw):
        return _Resp(self._quotes)

    def globalmetrics_quotes_latest(self, **kw):
        return _Resp(self._gm)


CMC_FNG_HIST = [
    {"timestamp": "1609545600", "value": 30, "value_classification": "Fear"},
    {"timestamp": "1609459200", "value": 25, "value_classification": "Extreme Fear"},
]


class TestParseCmcFearGreed:
    def test_returns_sorted_named_int_series(self):
        s = cmc.parse_cmc_fear_greed(CMC_FNG_HIST)
        assert s.name == "fear_greed"
        assert s.index.is_monotonic_increasing
        assert s.loc["2021-01-01"] == 25
        assert s.loc["2021-01-02"] == 30

    def test_handles_int_or_str_values(self):
        data = [{"timestamp": 1609459200, "value": "40"}]
        s = cmc.parse_cmc_fear_greed(data)
        assert s.iloc[0] == 40

    def test_empty_is_empty_named_series(self):
        s = cmc.parse_cmc_fear_greed([])
        assert s.name == "fear_greed"
        assert len(s) == 0

    def test_skips_malformed_records(self):
        data = [{"timestamp": "1609459200", "value": 25},
                {"timestamp": "1609545600"},          # missing value -> skipped
                {"value": 50}]                         # missing timestamp -> skipped
        s = cmc.parse_cmc_fear_greed(data)
        assert len(s) == 1
        assert s.iloc[0] == 25


class TestFetchFearGreedCmc:
    def test_uses_client_and_clips_range(self):
        client = _FakeCMC(fng_hist=CMC_FNG_HIST)
        s = cmc.fetch_fear_greed_cmc(client, start="2021-01-02", end="2021-01-02")
        assert list(s.index) == [pd.Timestamp("2021-01-02")]
        assert s.iloc[0] == 30

    def test_make_fng_fetcher_matches_loader_signature(self):
        client = _FakeCMC(fng_hist=CMC_FNG_HIST)
        fetch = cmc.make_fng_fetcher(client)
        s = fetch(start=None, end=None)   # loader calls fetch(start=..., end=...)
        assert s.name == "fear_greed"
        assert len(s) == 2


class TestLiveMarketContext:
    def test_extracts_available_fields_defensively(self):
        client = _FakeCMC(
            fng_latest={"value": 18, "value_classification": "Extreme Fear"},
            quotes={"BTC": {"quote": {"USD": {"price": 64000.0, "percent_change_24h": -2.1}}}},
            global_metrics={"btc_dominance": 54.6, "eth_dominance": 9.1,
                            "quote": {"USD": {"total_market_cap": 2.3e12}}},
        )
        ctx = cmc.live_market_context(client, "BTC")
        assert ctx["fear_greed"] == 18
        assert ctx["price"] == 64000.0
        assert ctx["btc_dominance"] == 54.6
        assert ctx["symbol"] == "BTC"

    def test_missing_fields_become_none_not_crash(self):
        client = _FakeCMC()  # everything empty/None
        ctx = cmc.live_market_context(client, "BTC")
        assert ctx["symbol"] == "BTC"
        assert ctx["fear_greed"] is None
        assert ctx["price"] is None
