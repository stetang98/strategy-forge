"""Market-regime detection via a Gaussian Hidden Markov Model.

A 2-state HMM on (returns, realized volatility) separates a *trend* regime from a
*chop* regime. The "trend" state is defined deterministically as the state with the
highest mean return, so labels are stable across fits given a fixed seed.

The ``RegimeModel`` fit/predict split exists so the backtest engine can fit on a
training window and predict on a *later* window — avoiding the look-ahead that
fitting on the whole series would introduce.
"""
from __future__ import annotations

import logging
import warnings

import numpy as np
import pandas as pd

from forge.strategy.signals import realized_vol

try:  # hmmlearn is the only heavy dep here; import error should be actionable
    from hmmlearn.hmm import GaussianHMM
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError("regime detection requires hmmlearn: pip install hmmlearn") from exc

try:
    from sklearn.exceptions import ConvergenceWarning
except ImportError:  # pragma: no cover - sklearn ships with hmmlearn
    ConvergenceWarning = RuntimeWarning  # type: ignore[assignment,misc]

# hmmlearn reports non-convergence via the logging system (NOT warnings.warn), so it
# must be quieted on its own logger.
_HMM_LOGGER = logging.getLogger("hmmlearn")


class LookaheadWarning(UserWarning):
    """Raised when a function fits on data that includes the period it labels."""


def build_regime_features(close: pd.Series, vol_lookback: int = 20) -> pd.DataFrame:
    """Build the HMM feature matrix: simple returns + annualized realized vol.

    Leading rows without enough history to compute both features are dropped, so
    column 0 (``returns``) is always the trend-defining feature.
    """
    features = pd.DataFrame(
        {
            "returns": close.pct_change(fill_method=None),
            "realized_vol": realized_vol(close, vol_lookback),
        }
    )
    return features.dropna()


class RegimeModel:
    """A fitted regime classifier with a stable trend-state label."""

    def __init__(self, n_states: int = 2, random_state: int = 42, n_iter: int = 200):
        self.n_states = n_states
        self.random_state = random_state
        self.n_iter = n_iter
        self._hmm: GaussianHMM | None = None
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None
        self._trend_state: int | None = None

    def _standardize(self, features: pd.DataFrame) -> np.ndarray:
        return (features.to_numpy() - self._mean) / self._std

    def fit(self, features: pd.DataFrame) -> "RegimeModel":
        raw = features.to_numpy()
        self._mean = raw.mean(axis=0)
        std = raw.std(axis=0)
        std[std == 0] = 1.0  # guard against a constant feature
        self._std = std

        self._hmm = GaussianHMM(
            n_components=self.n_states,
            covariance_type="full",
            n_iter=self.n_iter,
            random_state=self.random_state,
        )
        scaled = self._standardize(features)
        prev_level = _HMM_LOGGER.level
        with warnings.catch_warnings():
            # Quiet sklearn KMeans-init convergence warnings (warnings system) AND
            # hmmlearn's EM non-convergence reports (logging system) during fit.
            warnings.simplefilter("ignore", category=ConvergenceWarning)
            _HMM_LOGGER.setLevel(logging.CRITICAL)
            try:
                self._hmm.fit(scaled)
                states = self._hmm.predict(scaled)
            finally:
                _HMM_LOGGER.setLevel(prev_level)

        # Surface (not hide) genuine non-convergence — it means unreliable labels.
        if not getattr(self._hmm.monitor_, "converged", True):
            warnings.warn(
                "HMM regime model did not converge; labels may be unreliable "
                "(input is likely too short or degenerate).",
                RuntimeWarning,
                stacklevel=2,
            )

        # The trend regime is the hidden state with the highest mean return.
        returns = features.iloc[:, 0].to_numpy()
        mean_return = {s: float(returns[states == s].mean())
                       for s in range(self.n_states) if np.any(states == s)}
        if not mean_return:  # pragma: no cover - defensive; normal HMM always populates a state
            raise RuntimeError("HMM produced no populated states; input too short or degenerate")
        self._trend_state = max(mean_return, key=lambda s: mean_return[s])
        return self

    def predict_is_trend(self, features: pd.DataFrame) -> pd.Series:
        if self._hmm is None:
            raise RuntimeError("RegimeModel must be fit before predict_is_trend")
        scaled = self._standardize(features)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            states = self._hmm.predict(scaled)
        return pd.Series(states == self._trend_state, index=features.index, name="is_trend")


def detect_regime(close: pd.Series, vol_lookback: int = 20, n_states: int = 2,
                  random_state: int = 42) -> pd.Series:
    """Fit-and-predict regime labels over ``close``, aligned to its full index.

    Rows without enough history to form features are labeled ``False`` (not trend).
    This in-sample convenience is used for exploration; walk-forward backtests use
    ``RegimeModel.fit``/``predict_is_trend`` with separated windows instead.
    """
    warnings.warn(
        "detect_regime fits on the full series and is look-ahead biased; use "
        "RegimeModel.fit/predict_is_trend for walk-forward backtesting.",
        LookaheadWarning,
        stacklevel=2,
    )
    features = build_regime_features(close, vol_lookback)
    model = RegimeModel(n_states=n_states, random_state=random_state).fit(features)
    is_trend = model.predict_is_trend(features)
    return is_trend.reindex(close.index, fill_value=False).astype(bool)
