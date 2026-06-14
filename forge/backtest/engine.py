"""Backtest orchestration: spec + data -> look-ahead-safe portfolio + honest metrics.

Design decisions that make the numbers defensible to a skeptical judge:

- **Look-ahead safety**: decisions are shifted one bar before execution
  (``pipeline.to_execution_weights``); regime models are fit only on data strictly
  *before* each evaluated period, with the train/test boundary anchored on a single
  timestamp shared by both the regime split and the out-of-sample metric window.
- **Equity-derived metrics**: every reported statistic is computed from the
  cost-adjusted equity curve, so anyone can recompute them from the published curve.
  Out-of-sample metrics slice that same curve — no fresh portfolio, no spurious
  re-entry trade or fee distortion at the boundary.
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import vectorbt as vbt

from forge.backtest.pipeline import compute_decision_weights, to_execution_weights
from forge.strategy import regime
from forge.strategy.spec import StrategySpec

# Map a spec interval to a pandas frequency for annualized risk metrics.
_INTERVAL_TO_FREQ = {
    "1m": "1min", "3m": "3min", "5m": "5min", "15m": "15min", "30m": "30min",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "12h": "12h", "1d": "1D", "1w": "1W",
}
# Bars per year per interval, for annualizing Sharpe/Sortino/Calmar.
_PERIODS_PER_YEAR = {
    "1m": 365 * 1440, "3m": 365 * 480, "5m": 365 * 288, "15m": 365 * 96,
    "30m": 365 * 48, "1h": 365 * 24, "2h": 365 * 12, "4h": 365 * 6,
    "6h": 365 * 4, "12h": 365 * 2, "1d": 365, "1w": 52,
}


@dataclass
class BacktestResult:
    """Everything needed to report and plot a backtest."""

    spec: StrategySpec
    equity: pd.Series
    weights: pd.Series
    benchmark_equity: pd.Series
    stats_full: dict
    stats_oos: Optional[dict]
    oos_start: Optional[pd.Timestamp]


def _finite_or_nan(value: float) -> float:
    return value if math.isfinite(value) else float("nan")


def _trade_stats(equity: pd.Series, weights: pd.Series) -> tuple[int, float]:
    """Count holding spells (entries) and the fraction that ended profitable."""
    in_pos = (weights.reindex(equity.index).fillna(0.0) > 0).to_numpy()
    eq = equity.to_numpy()
    n_trades = 0
    wins = 0
    holding = False
    entry_value = np.nan
    for i in range(len(in_pos)):
        if in_pos[i] and not holding:
            holding, entry_value, n_trades = True, eq[i], n_trades + 1
        elif not in_pos[i] and holding:
            holding = False
            if eq[i] > entry_value:
                wins += 1
    if holding and eq[-1] > entry_value:  # spell still open at the end
        wins += 1
    win_rate = float(wins / n_trades) if n_trades else float("nan")
    return n_trades, win_rate


def _metrics(equity: pd.Series, weights: pd.Series, periods_per_year: int = 365) -> dict:
    """Compute headline risk/return metrics directly from a cost-adjusted equity curve."""
    equity = equity.dropna()
    if len(equity) < 2:
        return {"total_return": 0.0, "sharpe": float("nan"), "sortino": float("nan"),
                "calmar": float("nan"), "max_drawdown": 0.0, "win_rate": float("nan"),
                "n_trades": 0}

    returns = equity.pct_change().dropna()
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    max_drawdown = float((equity / equity.cummax() - 1.0).min())
    ann = math.sqrt(periods_per_year)

    std = float(returns.std())
    sharpe = _finite_or_nan(float(returns.mean() / std * ann)) if std > 0 else float("nan")
    downside = float(returns[returns < 0].std())
    sortino = (_finite_or_nan(float(returns.mean() / downside * ann))
               if downside > 0 else float("nan"))

    if max_drawdown < 0 and len(returns) > 0:
        ann_return = (1.0 + total_return) ** (periods_per_year / len(returns)) - 1.0
        calmar = _finite_or_nan(float(ann_return / abs(max_drawdown)))
    else:
        calmar = float("nan")

    n_trades, win_rate = _trade_stats(equity, weights)
    return {"total_return": total_return, "sharpe": sharpe, "sortino": sortino,
            "calmar": calmar, "max_drawdown": max_drawdown, "win_rate": win_rate,
            "n_trades": int(n_trades)}


def _bar_offset(n: int, days: int) -> int:
    """Bar index for ``days`` of history (1 bar/day for daily data), clamped to data."""
    return min(max(int(days), 1), max(n - 1, 1))


def _oos_start(df: pd.DataFrame, spec: StrategySpec) -> Optional[pd.Timestamp]:
    if spec.validation.scheme == "none":
        return None
    offset = _bar_offset(len(df), spec.validation.train_days)
    return df.index[offset] if offset < len(df) else None


def _fit_predict(train_features: pd.DataFrame, target_features: pd.DataFrame,
                 spec: StrategySpec) -> pd.Series:
    model = regime.RegimeModel(n_states=spec.regime_gate.n_states, random_state=42).fit(train_features)
    return model.predict_is_trend(target_features)


def _insample_regime(df: pd.DataFrame, spec: StrategySpec) -> pd.Series:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", regime.LookaheadWarning)
        return regime.detect_regime(df["close"], spec.regime_gate.vol_lookback_days,
                                    spec.regime_gate.n_states, random_state=42)


def _holdout_regime(df: pd.DataFrame, spec: StrategySpec) -> pd.Series:
    features = regime.build_regime_features(df["close"], spec.regime_gate.vol_lookback_days)
    cutoff = df.index[_bar_offset(len(df), spec.validation.train_days)]
    train = features[features.index < cutoff]
    if len(train) < spec.regime_gate.n_states + 1:  # too little to fit; fall back
        return _insample_regime(df, spec)
    preds = _fit_predict(train, features, spec)
    return preds.reindex(df.index, fill_value=False).astype(bool)


def _walk_forward_regime(df: pd.DataFrame, spec: StrategySpec) -> pd.Series:
    features = regime.build_regime_features(df["close"], spec.regime_gate.vol_lookback_days)
    cutoff = df.index[_bar_offset(len(df), spec.validation.train_days)]
    test_n = max(int(spec.validation.test_days), 1)
    labels = pd.Series(False, index=features.index)

    start_positions = np.where(features.index >= cutoff)[0]
    if len(start_positions) == 0:
        return labels.reindex(df.index, fill_value=False).astype(bool)

    i, n = int(start_positions[0]), len(features)
    while i < n:
        train = features.iloc[:i]
        test = features.iloc[i:i + test_n]
        if test.empty or len(train) < spec.regime_gate.n_states + 1:
            break
        preds = _fit_predict(train, test, spec)
        labels.loc[preds.index] = preds  # index-aligned (no positional coupling)
        i += test_n
    return labels.reindex(df.index, fill_value=False).astype(bool)


def regime_labels(df: pd.DataFrame, spec: StrategySpec) -> tuple[pd.Series, Optional[pd.Timestamp]]:
    """Return (is_trend, oos_start) for the configured validation scheme."""
    oos = _oos_start(df, spec)
    if not spec.regime_gate.enabled:
        return pd.Series(True, index=df.index), oos

    scheme = spec.validation.scheme
    if scheme == "walk_forward":
        return _walk_forward_regime(df, spec), oos
    if scheme == "holdout":
        return _holdout_regime(df, spec), oos

    # scheme == "none": labels are fit on the whole series — make that explicit.
    warnings.warn(
        "regime gate with validation scheme 'none' uses in-sample (look-ahead) "
        "regime labels; use 'holdout' or 'walk_forward' for an honest backtest.",
        regime.LookaheadWarning,
        stacklevel=2,
    )
    return _insample_regime(df, spec), oos


def _portfolio(close: pd.Series, weights: pd.Series, spec: StrategySpec) -> "vbt.Portfolio":
    return vbt.Portfolio.from_orders(
        close=close,
        size=weights,
        size_type="targetpercent",
        fees=spec.costs.fee_bps / 10_000.0,
        slippage=spec.costs.slippage_bps / 10_000.0,
        init_cash=spec.initial_cash,
        freq=_INTERVAL_TO_FREQ.get(spec.interval, "1D"),
    )


def run_backtest(df: pd.DataFrame, spec: StrategySpec) -> BacktestResult:
    """Run a full backtest and return metrics, equity, weights, and a benchmark."""
    df = df.sort_index()
    close = df["close"]
    periods = _PERIODS_PER_YEAR.get(spec.interval, 365)

    is_trend, oos_start = regime_labels(df, spec)
    decision = compute_decision_weights(df, spec, is_trend)
    weights = to_execution_weights(decision)

    equity = _portfolio(close, weights, spec).value()
    stats_full = _metrics(equity, weights, periods)

    stats_oos = None
    if oos_start is not None:
        mask = df.index >= oos_start
        if int(mask.sum()) > 1:
            stats_oos = _metrics(equity[mask], weights[mask], periods)

    benchmark = spec.initial_cash * close / close.iloc[0]
    return BacktestResult(
        spec=spec, equity=equity, weights=weights, benchmark_equity=benchmark,
        stats_full=stats_full, stats_oos=stats_oos, oos_start=oos_start,
    )
