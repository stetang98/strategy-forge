# Strategy families — when to use each

Pick the signal that matches the user's words; compose gates/overlays for nuance.

## Trend / momentum (the workhorse)

**Use when:** "ride the trend", "momentum", "trend following", "buy strength".
**Why:** time-series (trend) momentum is the best-documented systematic crypto edge —
positive across independent studies, and it *exits* downtrends, which is what protects
capital on assets that crash.

- `ema_crossover` with **fast 10 / slow 50** is the robust workhorse — captures most of
  a bull run and steps aside in bear markets. Always specify both `fast_ma` and `slow_ma`
  explicitly (the schema default for `slow_ma` is 100, a slower signal).
- `ts_momentum` adds a trailing-return confirmation; slightly more conservative.
- Pair with `sizing.vol_target` so position size shrinks when volatility spikes.

**Honest expectation:** on a token in a relentless bull, trend-following usually trails
buy-and-hold on *total* return but wins on *risk-adjusted* return and drawdown. On a
token that falls hard, it can be the difference between a profit and near-total loss.

## Fear & Greed contrarian (the baseline)

**Use when:** "buy fear, sell greed", "contrarian", "sentiment".
**Why:** intuitive and a useful benchmark, but it is a slow mean-reversion overlay, not
standalone alpha; the index is sample-thin (since 2018) and easy to curve-fit.
**Recommendation:** ship it as the baseline a real strategy must beat, not the headline.

## Regime switching (capital preservation)

**Use when:** "protect capital", "avoid crashes", "risk-managed", "switch in choppy
markets".
**How:** set `regime_gate.enabled: true`. A 2-state Gaussian HMM on (returns, realized
volatility) labels each bar trend vs chop; the strategy trades only in the trend regime.
**Tradeoff (state it plainly):** the gate meaningfully lowers drawdown but usually lowers
total return on trending assets — it shines on choppy or declining markets. Always show
the gated vs ungated comparison so the user chooses their point on the risk/return frontier.

## Sentiment overlay (a tilt, not a trigger)

**Use when:** the user wants to "lean in when everyone's fearful, trim when greedy"
*on top of* a primary signal. Set `sentiment_overlay.enabled: true`. It scales exposure
(boost in extreme fear, trim in extreme greed) but never opens a position on its own.

## Composing well

1. Start with a trend signal + vol-target sizing + walk-forward validation.
2. If the user prioritizes drawdown, add the regime gate and compare.
3. If they want a sentiment flavor, add the overlay.
4. Always report the **out-of-sample** number and benchmark against buy-and-hold.
