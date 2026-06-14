"""Tests for forge.strategy.spec — the StrategySpec intermediate representation."""
import pytest
from pydantic import ValidationError

from forge.strategy.spec import StrategySpec

MINIMAL = {
    "name": "test-strat",
    "signal": {"type": "ts_momentum", "lookback_days": 30},
}


class TestStrategySpecParsing:
    def test_parses_minimal_and_applies_defaults(self):
        spec = StrategySpec.model_validate(MINIMAL)
        assert spec.name == "test-strat"
        assert spec.symbol == "BNBUSDT"
        assert spec.interval == "1d"
        assert spec.signal.type == "ts_momentum"
        assert spec.signal.lookback_days == 30
        assert spec.sizing.type == "vol_target"
        assert spec.costs.fee_bps == 25
        assert spec.regime_gate.enabled is True
        assert spec.sentiment_overlay.enabled is True

    def test_json_round_trip_is_stable(self):
        spec = StrategySpec.model_validate(MINIMAL)
        again = StrategySpec.model_validate_json(spec.model_dump_json())
        assert again == spec


class TestStrategySpecValidation:
    def test_rejects_unknown_signal_type(self):
        with pytest.raises(ValidationError):
            StrategySpec.model_validate({"name": "x", "signal": {"type": "magic"}})

    def test_rejects_negative_lookback(self):
        with pytest.raises(ValidationError):
            StrategySpec.model_validate(
                {"name": "x", "signal": {"type": "ts_momentum", "lookback_days": -5}}
            )

    def test_rejects_fng_threshold_out_of_range(self):
        with pytest.raises(ValidationError):
            StrategySpec.model_validate(
                {"name": "x", "signal": {"type": "ts_momentum"},
                 "sentiment_overlay": {"fng_extreme_fear": 150}}
            )

    def test_rejects_slow_ma_not_greater_than_fast(self):
        with pytest.raises(ValidationError, match="slow_ma"):
            StrategySpec.model_validate(
                {"name": "x", "signal": {"type": "ema_crossover", "fast_ma": 50, "slow_ma": 20}}
            )

    def test_rejects_unknown_top_level_field(self):
        with pytest.raises(ValidationError):
            StrategySpec.model_validate(
                {"name": "x", "signal": {"type": "ts_momentum"}, "bogus": 1}
            )

    def test_rejects_nonpositive_target_vol(self):
        with pytest.raises(ValidationError):
            StrategySpec.model_validate(
                {"name": "x", "signal": {"type": "ts_momentum"}, "sizing": {"target_vol": 0}}
            )

    def test_rejects_fng_buy_not_below_sell(self):
        with pytest.raises(ValidationError, match="fng_buy_below"):
            StrategySpec.model_validate(
                {"name": "x", "signal": {"type": "fng_contrarian",
                                         "fng_buy_below": 80, "fng_sell_above": 20}}
            )

    def test_rejects_empty_name(self):
        with pytest.raises(ValidationError):
            StrategySpec.model_validate({"name": "", "signal": {"type": "ts_momentum"}})

    def test_rejects_unknown_interval(self):
        with pytest.raises(ValidationError):
            StrategySpec.model_validate(
                {"name": "x", "interval": "garbage", "signal": {"type": "ts_momentum"}}
            )

    def test_rejects_start_after_end(self):
        with pytest.raises(ValidationError, match="start"):
            StrategySpec.model_validate(
                {"name": "x", "signal": {"type": "ts_momentum"},
                 "start": "2025-01-01", "end": "2020-01-01"}
            )

    def test_parses_iso_dates(self):
        spec = StrategySpec.model_validate(
            {"name": "x", "signal": {"type": "ts_momentum"},
             "start": "2022-01-01", "end": "2025-12-31"}
        )
        assert str(spec.start) == "2022-01-01"
        assert str(spec.end) == "2025-12-31"


class TestSentimentOverlayDefaults:
    def test_has_two_sided_boost_and_trim(self):
        spec = StrategySpec.model_validate(MINIMAL)
        assert spec.sentiment_overlay.fear_boost > 1.0   # genuinely tilts up in fear
        assert 0 < spec.sentiment_overlay.greed_trim < 1.0
