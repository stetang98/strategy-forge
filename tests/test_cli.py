"""End-to-end tests for the scripts/backtest.py CLI (the Skill's black-box entry point)."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _load_cli():
    path = Path(__file__).resolve().parents[1] / "scripts" / "backtest.py"
    spec = importlib.util.spec_from_file_location("backtest_cli", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_df(n=150):
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    rng = np.random.default_rng(0)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.002, 0.02, n))), index=idx, name="close")
    return pd.DataFrame({"close": close})


class TestCli:
    def test_missing_spec_returns_exit_code_2(self, tmp_path):
        cli = _load_cli()
        rc = cli.main(["--spec", str(tmp_path / "nope.json"), "--out", str(tmp_path)])
        assert rc == 2

    def test_runs_end_to_end_with_patched_loader(self, tmp_path, monkeypatch):
        import forge.run as run_mod
        monkeypatch.setattr(run_mod._loader, "load_market_data", lambda *a, **k: _fake_df())

        spec_file = tmp_path / "clitest.json"
        spec_file.write_text(json.dumps({
            "name": "clitest", "symbol": "BNBUSDT",
            "signal": {"type": "ema_crossover", "fast_ma": 5, "slow_ma": 20},
            "validation": {"scheme": "none"},
        }))
        cli = _load_cli()
        rc = cli.main(["--spec", str(spec_file), "--out", str(tmp_path)])
        assert rc == 0
        assert (tmp_path / "clitest.png").exists()
        assert (tmp_path / "clitest.metrics.json").exists()
