"""Tests for forge.strategy.regime — HMM trend/chop regime detection."""
import warnings

import numpy as np
import pandas as pd
import pytest

from forge.strategy import regime


def _detect_quiet(close, **kwargs):
    """detect_regime, suppressing its (intentional) look-ahead warning for clean output."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", regime.LookaheadWarning)
        return regime.detect_regime(close, **kwargs)


def _two_regime_close():
    """A clean uptrend (high return, low vol) followed by choppy sideways (≈0 return, high vol)."""
    rng = np.random.default_rng(0)
    up = 100 * np.cumprod(1 + rng.normal(0.006, 0.004, 120))   # trend
    chop = up[-1] * np.cumprod(1 + rng.normal(0.0, 0.05, 120))  # chop
    vals = np.concatenate([up, chop])
    idx = pd.date_range("2021-01-01", periods=len(vals), freq="D")
    return pd.Series(vals, index=idx, name="close")


class TestDetectRegime:
    def test_separates_trend_from_chop(self):
        close = _two_regime_close()
        is_trend = _detect_quiet(close, vol_lookback=10, n_states=2, random_state=42)
        assert is_trend.dtype == bool
        uptrend_part = is_trend.iloc[20:120].mean()
        chop_part = is_trend.iloc[140:240].mean()
        assert uptrend_part > 0.6   # mostly "trend" during the clean uptrend
        assert chop_part < 0.4      # mostly "not trend" during the chop

    def test_aligns_to_input_index_with_leading_false(self):
        close = _two_regime_close()
        is_trend = _detect_quiet(close, vol_lookback=10, random_state=42)
        assert is_trend.index.equals(close.index)
        assert bool(is_trend.iloc[0]) is False  # insufficient history -> not trend

    def test_is_deterministic_with_fixed_seed(self):
        close = _two_regime_close()
        a = _detect_quiet(close, vol_lookback=10, random_state=7)
        b = _detect_quiet(close, vol_lookback=10, random_state=7)
        assert a.equals(b)

    def test_warns_about_lookahead(self):
        close = _two_regime_close()
        with pytest.warns(regime.LookaheadWarning):
            regime.detect_regime(close, vol_lookback=10, random_state=42)


class TestRegimeModelFitPredict:
    def test_fit_on_train_predict_on_later_window(self):
        close = _two_regime_close()
        feats = regime.build_regime_features(close, vol_lookback=10)
        train = feats.iloc[:150]
        model = regime.RegimeModel(random_state=42).fit(train)
        # predict on the chop tail (rows ~140..240 are chop; features start ~bar 11)
        chop_tail = feats.iloc[160:]
        preds = model.predict_is_trend(chop_tail)
        assert preds.index.equals(chop_tail.index)
        assert preds.dtype == bool
        assert preds.mean() < 0.5  # the chop tail is predominantly "not trend"

    def test_trend_state_has_highest_mean_return(self):
        close = _two_regime_close()
        feats = regime.build_regime_features(close, vol_lookback=10)
        model = regime.RegimeModel(random_state=42).fit(feats)
        is_trend = model.predict_is_trend(feats)
        # mean return when labeled trend should exceed mean return when not
        assert feats.loc[is_trend, "returns"].mean() > feats.loc[~is_trend, "returns"].mean()
