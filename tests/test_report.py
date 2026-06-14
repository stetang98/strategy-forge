"""Tests for forge.backtest.report — result serialization and tearsheet rendering."""
import json

import numpy as np
import pandas as pd

from forge.backtest import report
from forge.backtest.engine import BacktestResult
from forge.strategy.spec import StrategySpec


def _result():
    idx = pd.date_range("2022-01-01", periods=120, freq="D")
    equity = pd.Series(10000 * np.exp(np.cumsum(np.full(120, 0.003))), index=idx)
    bench = pd.Series(10000 * np.exp(np.cumsum(np.full(120, 0.001))), index=idx)
    weights = pd.Series(np.where(np.arange(120) % 20 < 12, 1.0, 0.0), index=idx)
    spec = StrategySpec.model_validate(
        {"name": "demo", "symbol": "BNBUSDT", "signal": {"type": "ema_crossover", "fast_ma": 10, "slow_ma": 50}}
    )
    return BacktestResult(
        spec=spec, equity=equity, weights=weights, benchmark_equity=bench,
        stats_full={"total_return": 0.42, "sharpe": 1.1, "sortino": 1.6, "calmar": 0.9,
                    "max_drawdown": -0.18, "win_rate": 0.55, "n_trades": 6},
        stats_oos={"total_return": 0.12, "sharpe": 0.7, "sortino": 1.0, "calmar": 0.5,
                   "max_drawdown": -0.15, "win_rate": 0.5, "n_trades": 3},
        oos_start=idx[60],
    )


class TestResultToDict:
    def test_is_json_serializable_with_expected_keys(self):
        d = report.result_to_dict(_result())
        json.dumps(d)  # must not raise
        assert d["name"] == "demo"
        assert d["symbol"] == "BNBUSDT"
        assert d["stats_full"]["total_return"] == 0.42
        assert d["stats_oos"]["sharpe"] == 0.7
        assert "benchmark_total_return" in d

    def test_handles_missing_oos(self):
        res = _result()
        res = report.BacktestResult(**{**res.__dict__, "stats_oos": None, "oos_start": None})
        d = report.result_to_dict(res)
        assert d["stats_oos"] is None
        json.dumps(d)

    def test_nan_stats_produce_valid_json(self):
        res = _result()
        nan_stats = {k: (float("nan") if isinstance(v, float) else v)
                     for k, v in res.stats_full.items()}
        res = report.BacktestResult(**{**res.__dict__, "stats_full": nan_stats})
        d = report.result_to_dict(res)
        raw = json.dumps(d)                 # must not emit bare NaN/Infinity tokens
        assert "NaN" not in raw and "Infinity" not in raw
        assert d["stats_full"]["sharpe"] is None


class TestRenderTearsheet:
    def test_writes_a_nonempty_png(self, tmp_path):
        path = report.render_tearsheet(_result(), tmp_path, basename="demo")
        assert path.exists()
        assert path.suffix == ".png"
        assert path.stat().st_size > 1000  # a real image, not an empty file

    def test_write_report_emits_metrics_and_tearsheet(self, tmp_path):
        paths = report.write_report(_result(), tmp_path)
        assert paths["metrics"].exists()
        assert paths["tearsheet"].exists()
        loaded = json.loads(paths["metrics"].read_text())
        assert loaded["name"] == "demo"

    def test_render_tearsheet_closes_figure(self, tmp_path):
        import matplotlib.pyplot as plt
        before = len(plt.get_fignums())
        report.render_tearsheet(_result(), tmp_path, basename="cleanup")
        assert len(plt.get_fignums()) == before  # no leaked figures
