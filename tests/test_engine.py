"""Tests for forge.backtest.engine — orchestration, validation split, metrics."""
import numpy as np
import pandas as pd
import pytest

from forge.backtest import engine
from forge.strategy.spec import StrategySpec


def _two_regime_df(seed=0):
    rng = np.random.default_rng(seed)
    up = 100 * np.cumprod(1 + rng.normal(0.006, 0.004, 130))
    chop = up[-1] * np.cumprod(1 + rng.normal(0.0, 0.05, 130))
    close = np.concatenate([up, chop])
    idx = pd.date_range("2022-01-01", periods=len(close), freq="D")
    fng = pd.Series(rng.integers(5, 95, len(close)), index=idx, name="fear_greed")
    return pd.DataFrame({"close": pd.Series(close, index=idx, name="close"), "fear_greed": fng})


def _spec(**v):
    base = {"name": "t", "signal": {"type": "ts_momentum", "lookback_days": 10,
                                    "fast_ma": 5, "slow_ma": 20}}
    base.update(v)
    return StrategySpec.model_validate(base)


class TestMetrics:
    def test_keys_and_types(self):
        idx = pd.date_range("2023-01-01", periods=60, freq="D")
        equity = pd.Series(10000 * np.exp(np.cumsum(np.full(60, 0.002))), index=idx)
        weights = pd.Series(1.0, index=idx)
        m = engine._metrics(equity, weights)
        for k in ["total_return", "sharpe", "sortino", "calmar", "max_drawdown",
                  "win_rate", "n_trades"]:
            assert k in m
        assert isinstance(m["total_return"], float)
        assert isinstance(m["n_trades"], int)
        assert m["total_return"] > 0

    def test_flat_equity_gives_nan_sharpe_not_inf(self):
        idx = pd.date_range("2023-01-01", periods=30, freq="D")
        equity = pd.Series(10000.0, index=idx)        # never moves
        weights = pd.Series(0.0, index=idx)           # never trades
        m = engine._metrics(equity, weights)
        assert not np.isinf(m["sharpe"])              # must be NaN, never +/-inf
        assert np.isnan(m["sharpe"])
        assert m["n_trades"] == 0

    def test_total_return_matches_equity_endpoints(self):
        idx = pd.date_range("2023-01-01", periods=10, freq="D")
        equity = pd.Series(np.linspace(10000, 12000, 10), index=idx)
        m = engine._metrics(equity, pd.Series(1.0, index=idx))
        assert m["total_return"] == pytest.approx(12000 / 10000 - 1)


class TestRunBacktest:
    def test_holdout_is_lookahead_safe_and_has_oos(self):
        df = _two_regime_df()
        spec = _spec(validation={"scheme": "holdout", "train_days": 120, "test_days": 60})
        res = engine.run_backtest(df, spec)
        assert res.equity.index.equals(df.index)
        assert res.weights.iloc[0] == 0.0          # execution shift => first bar flat
        assert {"total_return", "sharpe", "max_drawdown"}.issubset(res.stats_full)
        assert res.oos_start is not None
        assert res.stats_oos is not None
        assert res.benchmark_equity.index.equals(df.index)

    def test_oos_total_return_matches_equity_slice(self):
        df = _two_regime_df()
        spec = _spec(validation={"scheme": "holdout", "train_days": 120, "test_days": 60})
        res = engine.run_backtest(df, spec)
        oos = res.equity[res.equity.index >= res.oos_start]
        expected = oos.iloc[-1] / oos.iloc[0] - 1
        assert res.stats_oos["total_return"] == pytest.approx(expected, rel=1e-9)

    def test_holdout_regime_labels_have_no_oos_contamination(self):
        df = _two_regime_df()
        spec = _spec(regime_gate={"enabled": True},
                     validation={"scheme": "holdout", "train_days": 120, "test_days": 60})
        is_trend_a, oos_start = engine.regime_labels(df, spec)
        # perturb ONLY the out-of-sample region, well past the cutoff
        df2 = df.copy()
        df2.iloc[150:, df2.columns.get_loc("close")] *= 1.5
        is_trend_b, _ = engine.regime_labels(df2, spec)
        train_mask = df.index < oos_start
        # training-region labels must not change when only OOS data changes
        assert is_trend_a[train_mask].equals(is_trend_b[train_mask])

    def test_walk_forward_runs_and_reports_oos(self):
        df = _two_regime_df()
        spec = _spec(validation={"scheme": "walk_forward", "train_days": 120, "test_days": 60})
        res = engine.run_backtest(df, spec)
        assert res.oos_start is not None
        assert res.stats_oos is not None
        assert res.weights.index.equals(df.index)

    def test_walk_forward_regime_gate_runs_and_has_oos(self):
        df = _two_regime_df()
        spec = _spec(regime_gate={"enabled": True, "n_states": 2, "vol_lookback_days": 10},
                     validation={"scheme": "walk_forward", "train_days": 120, "test_days": 60})
        res = engine.run_backtest(df, spec)
        assert res.oos_start is not None
        assert res.stats_oos is not None
        assert res.weights.index.equals(df.index)

    def test_scheme_none_has_no_oos_split(self):
        df = _two_regime_df()
        spec = _spec(regime_gate={"enabled": False},
                     validation={"scheme": "none", "train_days": 120, "test_days": 60})
        res = engine.run_backtest(df, spec)
        assert res.oos_start is None
        assert res.stats_oos is None

    def test_train_window_exceeding_data_yields_no_oos(self):
        df = _two_regime_df().iloc[:40]
        spec = _spec(regime_gate={"enabled": False},
                     validation={"scheme": "holdout", "train_days": 500, "test_days": 60})
        res = engine.run_backtest(df, spec)
        assert res.stats_oos is None

