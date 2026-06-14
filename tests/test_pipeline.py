"""Tests for forge.backtest.pipeline — composing signals into executable weights."""
import numpy as np
import pandas as pd

from forge.backtest import pipeline
from forge.strategy.spec import StrategySpec


def _df(n=60, seed=1):
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    rng = np.random.default_rng(seed)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.002, 0.02, n))), index=idx, name="close")
    fng = pd.Series(rng.integers(5, 95, n), index=idx, name="fear_greed")
    return pd.DataFrame({"close": close, "fear_greed": fng})


def _spec(**overrides):
    base = {"name": "t", "signal": {"type": "ts_momentum", "lookback_days": 5,
                                    "fast_ma": 3, "slow_ma": 10}}
    base.update(overrides)
    return StrategySpec.model_validate(base)


class TestBasePosition:
    def test_dispatches_by_signal_type(self):
        df = _df()
        for stype, sig in [
            ("ts_momentum", {"type": "ts_momentum", "lookback_days": 5, "fast_ma": 3, "slow_ma": 10}),
            ("ema_crossover", {"type": "ema_crossover", "fast_ma": 3, "slow_ma": 10}),
            ("fng_contrarian", {"type": "fng_contrarian"}),
        ]:
            spec = StrategySpec.model_validate({"name": "t", "signal": sig})
            pos = pipeline.base_position(df, spec)
            assert pos.dtype == bool
            assert pos.index.equals(df.index)


class TestComputeDecisionWeights:
    def test_zero_weight_when_not_in_position(self):
        df = _df()
        spec = _spec(regime_gate={"enabled": False}, sentiment_overlay={"enabled": False})
        base = pipeline.base_position(df, spec)
        is_trend = pd.Series(True, index=df.index)
        w = pipeline.compute_decision_weights(df, spec, is_trend)
        assert (w[~base] == 0).all()

    def test_regime_gate_flattens_outside_trend(self):
        df = _df()
        spec = _spec(regime_gate={"enabled": True}, sentiment_overlay={"enabled": False},
                     sizing={"type": "full"})
        is_trend = pd.Series(True, index=df.index)
        is_trend.iloc[:30] = False
        w = pipeline.compute_decision_weights(df, spec, is_trend)
        assert (w.iloc[:30] == 0).all()  # not-trend region is flat regardless of signal

    def test_clipped_to_max_leverage(self):
        df = _df()
        spec = _spec(sizing={"type": "full", "max_leverage": 1.0},
                     sentiment_overlay={"enabled": True, "fear_boost": 2.0},
                     regime_gate={"enabled": False})
        is_trend = pd.Series(True, index=df.index)
        w = pipeline.compute_decision_weights(df, spec, is_trend)
        assert (w <= 1.0 + 1e-9).all()
        assert (w >= 0).all()

    def test_sentiment_trims_in_extreme_greed(self):
        idx = pd.date_range("2023-01-01", periods=4, freq="D")
        df = pd.DataFrame({"close": [100.0, 101, 102, 103],
                           "fear_greed": [50, 50, 90, 50]}, index=idx)
        spec = _spec(signal={"type": "ema_crossover", "fast_ma": 1, "slow_ma": 2},
                     sizing={"type": "full"}, regime_gate={"enabled": False},
                     sentiment_overlay={"enabled": True, "fng_extreme_greed": 75, "greed_trim": 0.5})
        is_trend = pd.Series(True, index=idx)
        w = pipeline.compute_decision_weights(df, spec, is_trend)
        # the extreme-greed bar (index 2) is trimmed relative to a neutral in-position bar
        in_pos = pipeline.base_position(df, spec)
        if bool(in_pos.iloc[2]) and bool(in_pos.iloc[3]):
            assert w.iloc[2] < w.iloc[3]


class TestExecutionShift:
    def test_shifts_decision_by_one_bar(self):
        idx = pd.date_range("2023-01-01", periods=4, freq="D")
        decision = pd.Series([0.0, 1.0, 0.5, 0.0], index=idx)
        execw = pipeline.to_execution_weights(decision)
        assert execw.iloc[0] == 0.0                  # nothing known before the first bar
        assert execw.iloc[1] == decision.iloc[0]
        assert execw.iloc[3] == decision.iloc[2]
