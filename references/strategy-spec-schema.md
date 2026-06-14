# StrategySpec schema

The single intermediate representation Strategy Forge compiles intent into and the
backtest consumes. Validated strictly (unknown fields are rejected) by
`forge/strategy/spec.py`. All fields below are optional except `name` and `signal`.

## Top level

| Field | Type | Default | Notes |
|---|---|---|---|
| `name` | string (non-empty) | — | kebab-case; names the output files |
| `symbol` | string | `"BNBUSDT"` | a Binance spot pair (keyless OHLCV source) |
| `interval` | enum | `"1d"` | `1m,3m,5m,15m,30m,1h,2h,4h,6h,12h,1d,1w` |
| `start` / `end` | ISO date or null | null | `start` must be before `end` |
| `initial_cash` | float > 0 | `10000` | starting capital |
| `signal` | object | — | see below (required) |
| `regime_gate` | object | disabled | HMM trend/chop filter |
| `sentiment_overlay` | object | disabled | Fear & Greed exposure tilt |
| `sizing` | object | vol-target | position sizing |
| `costs` | object | 30/25 bps | simulated transaction costs |
| `validation` | object | walk-forward | out-of-sample scheme |

## `signal`

`type` is one of:

- `"ts_momentum"` — long when trailing return > 0 **and** fast SMA > slow SMA.
  Fields: `lookback_days` (default 30), `fast_ma` (10), `slow_ma` (100).
- `"ema_crossover"` — long while fast EMA > slow EMA. Fields: `fast_ma` (10), `slow_ma` (100).
- `"fng_contrarian"` — accumulate at/below `fng_buy_below` (default 20), exit at/above
  `fng_sell_above` (default 80). Requires Fear & Greed data.

Constraint: `slow_ma` > `fast_ma`; `fng_buy_below` < `fng_sell_above`.

## `regime_gate` (opt-in)

| Field | Default | Notes |
|---|---|---|
| `enabled` | `false` | when true, trade only in the detected trend regime |
| `n_states` | `2` | HMM hidden states (2–4) |
| `vol_lookback_days` | `20` | volatility feature window |
| `trade_in` | `"trend"` | regime to allow trading in |

The trend regime is the HMM state with the highest mean return. The gate reduces
drawdown but typically lowers total return on strongly trending assets — show the tradeoff.

## `sentiment_overlay` (opt-in)

| Field | Default | Notes |
|---|---|---|
| `enabled` | `false` | tilt exposure by Fear & Greed |
| `fng_extreme_fear` | `25` | at/below → multiply exposure by `fear_boost` |
| `fng_extreme_greed` | `75` | at/above → multiply exposure by `greed_trim` |
| `fear_boost` | `1.15` | ≥ 1.0 |
| `greed_trim` | `0.5` | in (0, 1] |

Constraint: `fng_extreme_fear` < `fng_extreme_greed`.

## `sizing`

- `"vol_target"` (default) — exposure = `target_vol / realized_vol`, clipped to
  `[0, max_leverage]`. Fields: `target_vol` (0.20), `vol_lookback_days` (20), `max_leverage` (1.0).
- `"full"` — always `max_leverage` when in position.
- `"fixed_fraction"` — constant `fraction` (in (0, 1]).

## `costs`

`slippage_bps` (default 30) and `fee_bps` (default 25), applied to every fill.

## `validation`

| Field | Default | Notes |
|---|---|---|
| `scheme` | `"walk_forward"` | `walk_forward`, `holdout`, or `none` |
| `train_days` | `365` | initial training window |
| `test_days` | `90` | walk-forward fold size |

- `walk_forward` — expanding refit; each test fold is predicted by a model fit only on
  prior data. The honest number.
- `holdout` — fit once on the first `train_days`, evaluate the rest out-of-sample.
- `none` — in-sample only; use for a quick sketch and say so. With a regime gate this
  is look-ahead biased (the engine warns).

Look-ahead safety: regardless of scheme, decisions on bar *t* execute on bar *t+1*.
