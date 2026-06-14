---
name: strategy-forge
description: |
  Turn a plain-English crypto trading idea into a rigorous, reproducible backtest.
  Compiles intent into a structured strategy spec, then runs a walk-forward, cost-
  adjusted backtest on CoinMarketCap-grade data and returns equity curve, Sharpe/
  Sortino/Calmar/max-drawdown, and an out-of-sample verdict vs buy-and-hold.
  Use when the user wants to build, backtest, optimize, or compare a crypto trading
  strategy (momentum, trend-following, mean-reversion, regime-switching, or a
  Fear & Greed sentiment rule), or asks "would it have worked to buy when ...".
  Trigger: "build a strategy", "backtest", "/strategy-forge", "momentum strategy",
  "trend following", "fear and greed strategy", "should I buy when".
license: MIT
compatibility: ">=1.0.0"
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - mcp__cmc-mcp__search_cryptos
  - mcp__cmc-mcp__get_crypto_quotes_latest
  - mcp__cmc-mcp__get_crypto_technical_analysis
  - mcp__cmc-mcp__get_global_metrics_latest
  - mcp__cmc-mcp__get_global_crypto_derivatives_metrics
  - mcp__cmc-mcp__trending_crypto_narratives
---

# Strategy Forge

Generate, backtest, and compare crypto trading strategies from a natural-language
brief. You (the agent) translate intent into a **strategy spec**, run a black-box
backtest script, and report honest, out-of-sample results. *Quantopian for crypto,
authored as a Skill.*

> Not financial advice. Backtests are historical and do not guarantee future results.

## Prerequisites

The engine is a local Python package. Once per environment:

```bash
pip install -r requirements.txt   # vectorbt, hmmlearn, pydantic, pandas, matplotlib...
```

Backtests need **no API key** — they pull keyless, reproducible data
(`data-api.binance.vision` for OHLCV, `alternative.me` for the Fear & Greed index).
For *live* signal readings and richer data, connect the CoinMarketCap MCP (see
`references/cmc-endpoints.md`); it is optional and never required to reproduce a backtest.

## Core principle

One artifact drives everything: the **StrategySpec** (a JSON object). It is the
human-readable plan, the backtest input, and a reproducible record. Never hand-edit
the engine; compose a spec and run the script.

## Workflow

### Step 1 — Compile intent into a StrategySpec

Map the user's request to this template. Pick the signal family that matches their
words; leave everything else at its (sensible) default. Full field reference:
`references/strategy-spec-schema.md`. Signal-family guidance:
`references/strategy-families.md`.

```json
{
  "name": "kebab-case-name",
  "symbol": "BNBUSDT",
  "interval": "1d",
  "start": "2021-01-01",
  "end": "2026-06-13",
  "signal": { "type": "ema_crossover", "fast_ma": 10, "slow_ma": 50 },
  "regime_gate": { "enabled": false },
  "sentiment_overlay": { "enabled": false },
  "sizing": { "type": "vol_target", "target_vol": 1.0, "vol_lookback_days": 20, "max_leverage": 1.0 },
  "costs": { "slippage_bps": 30, "fee_bps": 25 },
  "validation": { "scheme": "walk_forward", "train_days": 365, "test_days": 90 }
}
```

Mapping cues:
- "trend following / momentum / ride the trend" → `signal.type: "ema_crossover"` or `"ts_momentum"`.
- "buy fear, sell greed / contrarian / sentiment" → `signal.type: "fng_contrarian"`.
- "protect capital / avoid crashes / risk-managed / switch in choppy markets" → add
  `"regime_gate": { "enabled": true }` (an HMM trend/chop filter — reduces drawdown,
  usually at the cost of upside; show the tradeoff honestly).
- "tilt with fear & greed" → `"sentiment_overlay": { "enabled": true }`.
- Always keep `validation.scheme` = `"walk_forward"` (or `"holdout"`) for an honest,
  out-of-sample number. Only use `"none"` for a quick in-sample sketch, and say so.

Always set both `fast_ma` and `slow_ma` explicitly (don't rely on defaults), and keep
`name` to letters/digits/hyphens (it becomes a filename). Write the spec to a file, e.g.
`assets/<name>.json`. Ready-made examples live in `assets/` (`trend-rider`,
`cake-trend-rider`, `regime-guard`, `fgi-contrarian`).

### Step 2 — (Optional) Show the live signal

If the CMC MCP is connected, read the current context so the user sees today's setup:
`get_global_metrics_latest` (Fear & Greed, altcoin-season), `get_crypto_quotes_latest`
and `get_crypto_technical_analysis` (price, trend) for the spec's symbol. This is
illustrative only; it does not change the backtest.

### Step 3 — Run the backtest (black box)

Run `python scripts/backtest.py --help` once if unsure of flags, then:

```bash
python scripts/backtest.py --spec assets/<name>.json --out examples
```

Do NOT read the engine source to "explain" the result — the script is the source of
truth. It writes `examples/<name>.metrics.json` and `examples/<name>.png` and prints
a results block.

### Step 4 — Report results (fixed template)

Present exactly this, filling from the script output / `metrics.json`:

```
Strategy: <name> on <symbol>  (<period>)
Full sample:    return <x>%  · Sharpe <s> · max drawdown <dd>% · <n> trades
Out-of-sample:  return <x>%  · Sharpe <s> · max drawdown <dd>%        ← trust this one
Buy & hold:     return <x>%
Tearsheet: examples/<name>.png
```

Then add a short, honest read:
- 🟢 Green flags: positive **out-of-sample** return; Sharpe ≳ 1; max drawdown well
  below buy-and-hold; trades not excessive.
- 🔴 Red flags: out-of-sample much worse than full-sample (overfit); drawdown near or
  above buy-and-hold; `n_trades` tiny (lucky) or huge (cost-bleed); `validation: none`.
- Always end with: *Not financial advice.*

### Step 5 — Compare / iterate

To make a point, run a second spec (e.g. the same idea with `regime_gate.enabled: true`,
or the `fgi-contrarian` baseline) and contrast the tearsheets. A great demo is one
chart where a disciplined strategy beats a naive baseline — or preserves capital on an
asset that buy-and-hold rode to zero.

## Tool-failure fallback

- `ModuleNotFoundError` / engine import error → run the Prerequisites `pip install`.
- Data fetch error (network / unknown symbol) → confirm the symbol is a real Binance
  pair (e.g. `BNBUSDT`, `ETHUSDT`, `CAKEUSDT`) and retry; the loader is keyless.
- "market frame has only N rows" → widen the date range or pick a longer-listed token.
- Spec validation error → the message names the offending field; fix it against
  `references/strategy-spec-schema.md`.

## What this is for

A self-custody trader or agent author who wants to go from a trading idea to *evidence*
without writing quant code — and the same StrategySpec can later drive a live execution
agent. See `README.md` for the architecture and `THIRD_PARTY.md` for attributions.
