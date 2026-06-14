"""Tests for forge.data.sources — keyless OHLCV + Fear&Greed parsing and fetch.

Fixtures mirror the real shapes observed from the live APIs (2026-06-14):
- binance.vision klines: list of arrays [openTime_ms, o, h, l, c, v, closeTime, ...]
- alternative.me fng:    {"data": [{"value": "18", "timestamp": "1781395200"}, ...]}
"""
import pandas as pd
import pytest

from forge.data import sources

# --- sample fixtures (two daily bars: 2021-01-01, 2021-01-02) ---
BINANCE_KLINES = [
    [1609459200000, "37.50", "38.10", "36.90", "37.36", "1000.0",
     1609545599999, "37360.0", 100, "500.0", "18680.0", "0"],
    [1609545600000, "37.36", "40.00", "37.00", "39.50", "2000.0",
     1609631999999, "79000.0", 200, "1000.0", "39500.0", "0"],
]

FNG_JSON = {
    "name": "Fear and Greed Index",
    "data": [
        {"value": "30", "value_classification": "Fear", "timestamp": "1609545600"},
        {"value": "25", "value_classification": "Extreme Fear", "timestamp": "1609459200"},
    ],
    "metadata": {"error": None},
}


class TestParseBinanceKlines:
    def test_returns_ohlcv_columns_as_floats(self):
        df = sources.parse_binance_klines(BINANCE_KLINES)
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert all(str(df[c].dtype) == "float64" for c in df.columns)

    def test_index_is_sorted_naive_daily_datetime(self):
        df = sources.parse_binance_klines(BINANCE_KLINES)
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.tz is None
        assert df.index.is_monotonic_increasing
        assert df.index[0] == pd.Timestamp("2021-01-01")
        assert df.index[1] == pd.Timestamp("2021-01-02")

    def test_values_parsed_correctly(self):
        df = sources.parse_binance_klines(BINANCE_KLINES)
        assert df.loc["2021-01-01", "close"] == pytest.approx(37.36)
        assert df.loc["2021-01-02", "high"] == pytest.approx(40.00)

    def test_empty_input_returns_empty_frame_with_columns(self):
        df = sources.parse_binance_klines([])
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert len(df) == 0


class TestParseFearGreed:
    def test_returns_named_int_series_sorted_ascending(self):
        s = sources.parse_fear_greed(FNG_JSON)
        assert s.name == "fear_greed"
        assert s.index.is_monotonic_increasing
        assert s.index.tz is None
        assert s.loc["2021-01-01"] == 25
        assert s.loc["2021-01-02"] == 30

    def test_empty_data_returns_empty_named_series(self):
        s = sources.parse_fear_greed({"data": []})
        assert s.name == "fear_greed"
        assert len(s) == 0


class TestFetchOhlcv:
    def test_uses_injected_http_get_and_parses(self):
        captured = {}

        def fake_get(url, params=None):
            captured["url"] = url
            captured["params"] = params or {}
            return BINANCE_KLINES

        df = sources.fetch_ohlcv("BNBUSDT", interval="1d", http_get=fake_get)
        # symbol reached the request somehow (url or params)
        assert "BNBUSDT" in captured["url"] or captured["params"].get("symbol") == "BNBUSDT"
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert len(df) == 2


class TestFetchFearGreed:
    def test_uses_injected_http_get_and_parses(self):
        def fake_get(url, params=None):
            return FNG_JSON

        s = sources.fetch_fear_greed(http_get=fake_get)
        assert s.name == "fear_greed"
        assert len(s) == 2


def _make_klines(n_days, base_day="2021-01-01"):
    base_ms = int((pd.Timestamp(base_day) - pd.Timestamp("1970-01-01")) // pd.Timedelta(milliseconds=1))
    rows = []
    for i in range(n_days):
        ot = base_ms + i * 86_400_000
        rows.append([ot, "100", "101", "99", str(100 + i), "10",
                     ot + 86_399_999, "1000", 5, "5", "500", "0"])
    return rows


class TestFetchOhlcvHistoryPagination:
    def test_pages_until_short_page_and_dedups(self):
        master = _make_klines(4)  # daily bars 2021-01-01 .. 2021-01-04
        page_limit = 3
        calls = []

        def fake_get(url, params=None):
            calls.append(params)
            start_ms = params.get("startTime")
            rows = [r for r in master if start_ms is None or r[0] >= start_ms]
            return rows[:page_limit]

        df = sources.fetch_ohlcv_history(
            "BNBUSDT", interval="1d", start="2021-01-01",
            page_limit=page_limit, http_get=fake_get,
        )
        assert len(df) == 4
        assert df.index[0] == pd.Timestamp("2021-01-01")
        assert df.index[-1] == pd.Timestamp("2021-01-04")
        assert df.index.is_monotonic_increasing
        assert len(calls) == 2  # one full page (3), then one short page (1) -> stop

    def test_clips_to_end_date_and_passes_end_time(self):
        master = _make_klines(10)
        calls = []

        def fake_get(url, params=None):
            calls.append(params)
            start_ms = (params or {}).get("startTime", 0)
            end_ms = (params or {}).get("endTime", float("inf"))
            return [r for r in master if start_ms <= r[0] <= end_ms]

        df = sources.fetch_ohlcv_history(
            "BNBUSDT", interval="1d", start="2021-01-01", end="2021-01-05",
            page_limit=1000, http_get=fake_get,
        )
        assert df.index[-1] == pd.Timestamp("2021-01-05")
        assert len(df) == 5
        assert calls[0].get("endTime") == sources._to_ms("2021-01-05")

    def test_start_none_returns_single_recent_page_without_future_paging(self):
        master = _make_klines(5)
        calls = []

        def fake_get(url, params=None):
            calls.append(params)
            start_ms = (params or {}).get("startTime")
            limit = params["limit"]
            if start_ms is None:  # binance returns the most-recent `limit` bars
                return master[-limit:]
            return [r for r in master if r[0] >= start_ms][:limit]

        df = sources.fetch_ohlcv_history("BNBUSDT", start=None, page_limit=3, http_get=fake_get)
        assert len(calls) == 1  # no wasted future page
        assert len(df) == 3

    def test_stops_at_max_pages_when_every_page_full(self):
        master = _make_klines(10)

        def fake_get(url, params=None):
            start_ms = params.get("startTime")
            return [r for r in master if r[0] >= start_ms][:2]  # always a full page

        df = sources.fetch_ohlcv_history(
            "BNBUSDT", start="2021-01-01", page_limit=2, http_get=fake_get, max_pages=3,
        )
        assert len(df) == 6  # 3 pages * 2 bars, advancing one day per page
        assert df.index.is_monotonic_increasing

    def test_unknown_interval_raises(self):
        with pytest.raises(ValueError, match="interval"):
            sources.fetch_ohlcv_history("BNBUSDT", interval="2w", start="2021-01-01",
                                        http_get=lambda u, p=None: [])


class TestParseGuards:
    def test_klines_non_list_raises(self):
        with pytest.raises(ValueError, match="list"):
            sources.parse_binance_klines({"code": -1121, "msg": "Invalid symbol."})

    def test_klines_malformed_row_raises(self):
        with pytest.raises(ValueError, match="[Mm]alformed"):
            sources.parse_binance_klines([[1609459200000, "37.5"]])  # row too short

    def test_klines_non_numeric_raises(self):
        bad = [[1609459200000, "x", "y", "z", "bad", "10", 0, "0", 0, "0", "0", "0"]]
        with pytest.raises(ValueError, match="[Mm]alformed"):
            sources.parse_binance_klines(bad)

    def test_fng_non_dict_raises(self):
        with pytest.raises(ValueError, match="dict"):
            sources.parse_fear_greed([{"value": "10"}])

    def test_fng_missing_value_key_raises(self):
        with pytest.raises(ValueError, match="[Mm]alformed"):
            sources.parse_fear_greed({"data": [{"timestamp": "1609459200"}]})


class TestToMs:
    def test_tz_aware_converts_to_utc(self):
        naive = sources._to_ms("2021-01-01")
        aware = sources._to_ms(pd.Timestamp("2021-01-01", tz="America/New_York"))
        assert aware == naive + 5 * 3600 * 1000  # EST is UTC-5


class TestFetchFearGreedClipping:
    def test_clips_to_start_and_end(self):
        def _ts(d):
            return str(int((pd.Timestamp(d) - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)))

        raw = {"data": [{"value": str(v), "timestamp": _ts(d)}
                        for d, v in [("2021-01-01", 10), ("2021-01-02", 20), ("2021-01-03", 30)]]}
        s = sources.fetch_fear_greed(start="2021-01-02", end="2021-01-02",
                                     http_get=lambda u, p=None: raw)
        assert list(s.index) == [pd.Timestamp("2021-01-02")]
        assert s.iloc[0] == 20
