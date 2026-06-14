"""Tests for forge.data.loader — joining OHLCV + Fear&Greed and boundary validation."""
import pandas as pd
import pytest

from forge.data import loader


def _ohlcv(dates, close):
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="date")
    return pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close,
         "volume": [1.0] * len(close)},
        index=idx,
    )


def _fng(dates, vals):
    return pd.Series(vals, index=pd.DatetimeIndex(pd.to_datetime(dates), name="date"),
                     name="fear_greed")


class TestValidateMarketFrame:
    def _good(self):
        df = _ohlcv(["2021-01-01", "2021-01-02"], [10.0, 11.0])
        df["fear_greed"] = [20, 30]
        return df

    def test_accepts_valid_frame(self):
        loader.validate_market_frame(self._good())  # should not raise

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="empty"):
            loader.validate_market_frame(self._good().iloc[0:0])

    def test_rejects_missing_column(self):
        with pytest.raises(ValueError, match="close"):
            loader.validate_market_frame(self._good().drop(columns=["close"]))

    def test_rejects_non_monotonic_index(self):
        df = self._good().iloc[::-1]
        with pytest.raises(ValueError, match="monotonic"):
            loader.validate_market_frame(df)

    def test_rejects_duplicate_index(self):
        df = self._good()
        df = pd.concat([df, df.iloc[[0]]])
        with pytest.raises(ValueError, match="duplicate"):
            loader.validate_market_frame(df)

    def test_rejects_nan_in_close(self):
        df = self._good()
        df.loc["2021-01-02", "close"] = float("nan")
        with pytest.raises(ValueError, match="NaN"):
            loader.validate_market_frame(df)


class TestLoadMarketData:
    def _fetchers(self, ohlcv, fng):
        return (
            lambda symbol, interval="1d", start=None, end=None: ohlcv,
            lambda start=None, end=None: fng,
        )

    def test_joins_ohlcv_and_fear_greed(self):
        ohlcv = _ohlcv(["2021-01-01", "2021-01-02", "2021-01-03"], [10.0, 11.0, 12.0])
        fng = _fng(["2021-01-01", "2021-01-02", "2021-01-03"], [20, 30, 40])
        of, ff = self._fetchers(ohlcv, fng)
        df = loader.load_market_data("X", ohlcv_fetcher=of, fng_fetcher=ff)
        assert "fear_greed" in df.columns
        assert df.loc["2021-01-03", "fear_greed"] == 40
        assert df.loc["2021-01-02", "close"] == 11.0

    def test_forward_fills_missing_fear_greed(self):
        ohlcv = _ohlcv(["2021-01-01", "2021-01-02", "2021-01-03"], [10.0, 11.0, 12.0])
        fng = _fng(["2021-01-01", "2021-01-03"], [20, 40])  # 01-02 missing
        of, ff = self._fetchers(ohlcv, fng)
        df = loader.load_market_data("X", ohlcv_fetcher=of, fng_fetcher=ff)
        assert df.loc["2021-01-02", "fear_greed"] == 20  # carried forward, no lookahead

    def test_without_fear_greed_has_no_fng_column(self):
        ohlcv = _ohlcv(["2021-01-01", "2021-01-02"], [10.0, 11.0])
        of, ff = self._fetchers(ohlcv, _fng([], []))
        df = loader.load_market_data("X", with_fear_greed=False, ohlcv_fetcher=of, fng_fetcher=ff)
        assert "fear_greed" not in df.columns
        assert list(df["close"]) == [10.0, 11.0]

    def test_drops_rows_before_first_fear_greed_reading(self):
        ohlcv = _ohlcv(["2021-01-01", "2021-01-02", "2021-01-03"], [10.0, 11.0, 12.0])
        fng = _fng(["2021-01-02", "2021-01-03"], [20, 30])  # nothing for 01-01
        of, ff = self._fetchers(ohlcv, fng)
        df = loader.load_market_data("X", ohlcv_fetcher=of, fng_fetcher=ff)
        assert pd.Timestamp("2021-01-01") not in df.index
        assert len(df) == 2

    def test_forward_fills_trailing_fear_greed(self):
        ohlcv = _ohlcv(["2021-01-01", "2021-01-02", "2021-01-03"], [10.0, 11.0, 12.0])
        fng = _fng(["2021-01-01"], [20])  # only first day has a reading
        of, ff = self._fetchers(ohlcv, fng)
        df = loader.load_market_data("X", ohlcv_fetcher=of, fng_fetcher=ff)
        assert df.loc["2021-01-03", "fear_greed"] == 20  # carried forward, not NaN
        assert len(df) == 3

    def test_passes_interval_to_ohlcv_fetcher(self):
        captured = {}

        def of(symbol, interval="1d", start=None, end=None):
            captured["interval"] = interval
            return _ohlcv(["2021-01-01", "2021-01-02"], [10.0, 11.0])

        loader.load_market_data("X", interval="1h", with_fear_greed=False,
                                ohlcv_fetcher=of, fng_fetcher=lambda start=None, end=None: _fng([], []))
        assert captured["interval"] == "1h"

    def test_rejects_none(self):
        with pytest.raises(ValueError, match="empty"):
            loader.validate_market_frame(None)
