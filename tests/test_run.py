"""Tests for forge.run — load a spec, fetch data, backtest, write report."""
import json

import numpy as np
import pandas as pd
import pytest

from forge import run
from forge.strategy.spec import StrategySpec


def _fake_df(n=400, seed=3):
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    rng = np.random.default_rng(seed)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.002, 0.02, n))), index=idx, name="close")
    fng = pd.Series(rng.integers(5, 95, n), index=idx, name="fear_greed")
    return pd.DataFrame({"close": close, "fear_greed": fng})


def _trend_spec(**v):
    base = {"name": "t", "symbol": "BNBUSDT",
            "signal": {"type": "ema_crossover", "fast_ma": 10, "slow_ma": 50},
            "regime_gate": {"enabled": False}, "sentiment_overlay": {"enabled": False},
            "sizing": {"type": "vol_target", "target_vol": 1.0, "vol_lookback_days": 20, "max_leverage": 1.0},
            "validation": {"scheme": "walk_forward", "train_days": 200, "test_days": 60}}
    base.update(v)
    return StrategySpec.model_validate(base)


def _loader_factory(captured):
    """A fake loader that mirrors production: omit fear_greed when not requested."""
    def fake_loader(symbol, start=None, end=None, interval="1d", with_fear_greed=False):
        captured.update(symbol=symbol, with_fear_greed=with_fear_greed, interval=interval)
        df = _fake_df()
        return df if with_fear_greed else df.drop(columns=["fear_greed"])
    return fake_loader


class TestLoadSpec:
    def test_reads_and_validates_json(self, tmp_path):
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"name": "x", "signal": {"type": "ts_momentum"}}))
        spec = run.load_spec(p)
        assert spec.name == "x"
        assert spec.signal.type == "ts_momentum"

    def test_rejects_malformed_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not valid json")
        with pytest.raises(Exception):
            run.load_spec(p)


class TestRunSpec:
    def test_writes_outputs_and_returns_summary(self, tmp_path):
        captured = {}
        out = run.run_spec(_trend_spec(), tmp_path, data_loader=_loader_factory(captured))
        assert out["paths"]["metrics"].exists()
        assert out["paths"]["tearsheet"].exists()
        assert "stats_full" in out["summary"]
        assert captured["symbol"] == "BNBUSDT"
        assert captured["with_fear_greed"] is False  # trend strategy needs no sentiment

    def test_fng_strategy_requests_fear_greed(self, tmp_path):
        captured = {}
        spec = StrategySpec.model_validate(
            {"name": "b", "signal": {"type": "fng_contrarian"},
             "sizing": {"type": "full"}, "validation": {"scheme": "none"}}
        )
        run.run_spec(spec, tmp_path, data_loader=_loader_factory(captured))
        assert captured["with_fear_greed"] is True

    def test_sentiment_overlay_requests_fear_greed(self, tmp_path):
        captured = {}
        run.run_spec(_trend_spec(sentiment_overlay={"enabled": True}), tmp_path,
                     data_loader=_loader_factory(captured))
        assert captured["with_fear_greed"] is True

    def test_rejects_too_short_frame(self, tmp_path):
        def short_loader(symbol, start=None, end=None, interval="1d", with_fear_greed=False):
            idx = pd.date_range("2022-01-01", periods=5, freq="D")
            return pd.DataFrame({"close": [1.0, 2, 3, 4, 5]}, index=idx)

        with pytest.raises(ValueError, match="rows"):
            run.run_spec(_trend_spec(), tmp_path, data_loader=short_loader)
