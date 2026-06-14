"""Tests for forge.strategy.signals — pure, composable signal/sizing functions."""
import numpy as np
import pandas as pd
import pytest

from forge.strategy import signals


def _series(values, start="2021-01-01"):
    idx = pd.date_range(start, periods=len(values), freq="D")
    return pd.Series(values, index=idx, dtype="float64")


class TestTrailingReturn:
    def test_computes_lookback_return(self):
        s = _series([10, 11, 12, 13])
        r = signals.trailing_return(s, lookback=2)
        assert r.iloc[2] == pytest.approx(12 / 10 - 1)
        assert pd.isna(r.iloc[0])  # not enough history


class TestTsMomentumPosition:
    def test_long_in_uptrend_flat_in_downtrend(self):
        close = _series([10, 10, 10, 10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 10])
        pos = signals.ts_momentum_position(close, lookback_days=3, fast_ma=2, slow_ma=4)
        assert pos.dtype == bool
        assert pos.iloc[8] is np.True_ or bool(pos.iloc[8]) is True   # strong uptrend -> long
        assert bool(pos.iloc[13]) is False                            # downtrend -> flat
        assert bool(pos.iloc[0]) is False                             # leading NaN -> flat


class TestFngContrarianPosition:
    def test_state_machine_enter_fear_exit_greed(self):
        fng = pd.Series([10, 50, 90, 50, 15],
                        index=pd.date_range("2021-01-01", periods=5, freq="D"))
        pos = signals.fng_contrarian_position(fng, buy_below=20, sell_above=80)
        assert [bool(x) for x in pos] == [True, True, False, False, True]


class TestEmaCrossoverPosition:
    def test_long_when_fast_above_slow(self):
        close = _series(list(range(1, 21)))  # monotonic up -> fast EMA > slow EMA
        pos = signals.ema_crossover_position(close, fast_ma=3, slow_ma=8)
        assert bool(pos.iloc[-1]) is True


class TestSentimentScale:
    def test_piecewise_boost_trim_neutral(self):
        fng = pd.Series([10, 50, 90],
                        index=pd.date_range("2021-01-01", periods=3, freq="D"))
        scale = signals.sentiment_scale(fng, extreme_fear=25, extreme_greed=75,
                                        fear_boost=1.2, greed_trim=0.5)
        assert list(scale) == pytest.approx([1.2, 1.0, 0.5])


class TestVolTargetWeight:
    def test_zero_vol_clips_to_max_leverage(self):
        close = _series([100.0] * 10)  # constant -> zero realized vol
        w = signals.vol_target_weight(close, target_vol=0.2, vol_lookback=3, max_leverage=1.0)
        assert w.iloc[-1] == pytest.approx(1.0)  # no division-by-zero blowup

    def test_higher_vol_gives_lower_weight(self):
        calm = _series([100 + 0.1 * i for i in range(40)])
        wild = _series([100 * (1.1 if i % 2 else 0.9) for i in range(40)])
        wc = signals.vol_target_weight(calm, target_vol=0.2, vol_lookback=10, max_leverage=5.0)
        ww = signals.vol_target_weight(wild, target_vol=0.2, vol_lookback=10, max_leverage=5.0)
        assert ww.iloc[-1] < wc.iloc[-1]

    def test_weight_never_negative_or_nan(self):
        close = _series([100 + np.sin(i) for i in range(30)])
        w = signals.vol_target_weight(close, target_vol=0.2, vol_lookback=5, max_leverage=1.0)
        assert (w >= 0).all()
        assert not w.isna().any()

    def test_mid_series_nan_does_not_blow_up(self):
        vals = [100 + 0.5 * i for i in range(20)]
        vals[10] = np.nan
        close = _series(vals)
        w = signals.vol_target_weight(close, target_vol=0.2, vol_lookback=5, max_leverage=1.0)
        assert not w.isna().any()
        assert (w >= 0).all()


class TestSignalEdgeCases:
    def test_trailing_return_lookback_exceeds_length_is_all_nan(self):
        s = _series([10, 11, 12])
        r = signals.trailing_return(s, lookback=10)
        assert r.isna().all()

    def test_fng_contrarian_all_nan_is_all_flat(self):
        fng = pd.Series([np.nan] * 4, index=pd.date_range("2021-01-01", periods=4, freq="D"))
        pos = signals.fng_contrarian_position(fng, buy_below=20, sell_above=80)
        assert not pos.any()
