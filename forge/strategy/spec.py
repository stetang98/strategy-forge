"""StrategySpec — the strategy intermediate representation.

This is the keystone of Strategy Forge: a single declarative, validated object that
is (1) what ``SKILL.md`` compiles natural-language intent into, (2) the input the
backtest engine consumes, and (3) a human-readable, reproducible artifact. Every
field is strictly validated (``extra="forbid"``) so a malformed spec fails loudly
at the boundary rather than producing a silently wrong backtest.
"""
from __future__ import annotations

import datetime
import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Intervals supported by the data layer (forge.data.sources).
Interval = Literal["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "1w"]

# `name` becomes a filename; restrict it to prevent path traversal. `symbol` becomes
# an HTTP query value; restrict it to the exchange pair format.
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{0,63}$")
_SAFE_SYMBOL = re.compile(r"^[A-Z0-9]{2,20}$")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SignalSpec(_Strict):
    """The entry/exit signal family and its parameters."""

    type: Literal["ts_momentum", "fng_contrarian", "ema_crossover"]
    lookback_days: int = Field(default=30, gt=0, description="trailing return window for ts_momentum")
    fast_ma: int = Field(default=10, gt=0)
    slow_ma: int = Field(default=100, gt=0)
    fng_buy_below: int = Field(default=20, ge=0, le=100, description="fng_contrarian: accumulate below")
    fng_sell_above: int = Field(default=80, ge=0, le=100, description="fng_contrarian: exit above")

    @model_validator(mode="after")
    def _check_ma_order(self) -> "SignalSpec":
        # fast_ma/slow_ma are unused for fng_contrarian but kept consistent for all types.
        if self.slow_ma <= self.fast_ma:
            raise ValueError("slow_ma must be greater than fast_ma")
        return self

    @model_validator(mode="after")
    def _check_fng_order(self) -> "SignalSpec":
        if self.fng_buy_below >= self.fng_sell_above:
            raise ValueError("fng_buy_below must be strictly less than fng_sell_above")
        return self


class RegimeGateSpec(_Strict):
    """HMM market-regime gate: trade momentum only in the trending regime."""

    enabled: bool = False
    type: Literal["hmm"] = "hmm"
    n_states: int = Field(default=2, ge=2, le=4)
    vol_lookback_days: int = Field(default=20, gt=0)
    trade_in: Literal["trend", "all"] = "trend"


class SentimentOverlaySpec(_Strict):
    """Fear & Greed overlay: tilt up in extreme fear, trim in extreme greed."""

    enabled: bool = False
    fng_extreme_fear: int = Field(default=25, ge=0, le=100)
    fng_extreme_greed: int = Field(default=75, ge=0, le=100)
    fear_boost: float = Field(default=1.15, ge=1.0, description="exposure multiplier in extreme fear")
    greed_trim: float = Field(default=0.5, gt=0, le=1.0, description="exposure multiplier in extreme greed")

    @model_validator(mode="after")
    def _check_band(self) -> "SentimentOverlaySpec":
        if self.fng_extreme_fear >= self.fng_extreme_greed:
            raise ValueError("fng_extreme_fear must be < fng_extreme_greed")
        return self


class SizingSpec(_Strict):
    """Position sizing. ``vol_target`` scales exposure inversely with realized vol."""

    type: Literal["vol_target", "full", "fixed_fraction"] = "vol_target"
    target_vol: float = Field(default=0.20, gt=0, description="annualized vol target")
    vol_lookback_days: int = Field(default=20, gt=0)
    max_leverage: float = Field(default=1.0, gt=0)
    fraction: float = Field(default=1.0, gt=0, le=1.0, description="fixed_fraction exposure")


class CostsSpec(_Strict):
    """Simulated transaction costs applied to every fill."""

    slippage_bps: float = Field(default=30.0, ge=0)
    fee_bps: float = Field(default=25.0, ge=0)


class ValidationSpec(_Strict):
    """Out-of-sample validation scheme for honest, non-overfit metrics."""

    scheme: Literal["holdout", "walk_forward", "none"] = "walk_forward"
    train_days: int = Field(default=365, gt=0)
    test_days: int = Field(default=90, gt=0)


class StrategySpec(_Strict):
    """A complete, backtestable strategy definition."""

    name: str = Field(min_length=1)
    symbol: str = Field(default="BNBUSDT", min_length=1)
    interval: Interval = "1d"
    start: Optional[datetime.date] = None
    end: Optional[datetime.date] = None
    initial_cash: float = Field(default=10_000.0, gt=0)

    signal: SignalSpec
    regime_gate: RegimeGateSpec = Field(default_factory=RegimeGateSpec)
    sentiment_overlay: SentimentOverlaySpec = Field(default_factory=SentimentOverlaySpec)
    sizing: SizingSpec = Field(default_factory=SizingSpec)
    costs: CostsSpec = Field(default_factory=CostsSpec)
    validation: ValidationSpec = Field(default_factory=ValidationSpec)

    @field_validator("name")
    @classmethod
    def _safe_name(cls, v: str) -> str:
        if not _SAFE_NAME.fullmatch(v):
            raise ValueError(
                "name must be 1-64 chars, start alphanumeric, then only letters/digits/-/_ "
                "(it becomes a filename; no path separators)"
            )
        return v

    @field_validator("symbol")
    @classmethod
    def _safe_symbol(cls, v: str) -> str:
        if not _SAFE_SYMBOL.fullmatch(v):
            raise ValueError("symbol must be 2-20 uppercase letters/digits, e.g. BNBUSDT")
        return v

    @model_validator(mode="after")
    def _check_date_order(self) -> "StrategySpec":
        if self.start and self.end and self.start >= self.end:
            raise ValueError("start must be before end")
        return self
