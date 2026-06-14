<!-- markdownlint-disable MD033 MD041 -->
<h1 align="center">⚒️ Strategy Forge</h1>

<p align="center">
  <b>Describe a crypto strategy in plain English → get a rigorous, reproducible backtest.</b><br>
  A CoinMarketCap-powered strategy-generation Skill. <i>Quantopian for crypto, authored as an LLM Skill.</i>
</p>

<p align="center">
  <i>BNB Hack: AI Trading Agent Edition — Track 2 (Strategy Skills) · zero-cost · 100% reproducible</i>
</p>

---

## What it is

Strategy Forge is a **CoinMarketCap Agent-Hub Skill** that turns a natural-language
trading idea into a **structured, backtestable strategy spec**, then runs a real
[vectorbt](https://github.com/polakowo/vectorbt) backtest on historical market data
— with walk-forward validation, transaction costs, and an honest equity/drawdown
tearsheet. You don't write quant code; you describe intent and get evidence.

> "Build me a drawdown-safe BNB momentum strategy that backs off in extreme greed."
> → compiled spec → backtest → equity curve + Sharpe / max-drawdown, benchmarked
> against a naive baseline it beats.

## Why it's different

- **A strategy *generator*, not one hard-coded strategy.** Intent → spec → backtest.
  The **StrategySpec** is the keystone: human-readable, machine-runnable, and (future)
  a live-agent config.
- **Rigor over cherry-picking.** Walk-forward / out-of-sample splits, realistic costs,
  and overfit checks — so the numbers survive a skeptical judge re-running them.
- **100% keyless & reproducible.** Backtests pull from public, keyless sources
  (`data-api.binance.vision` for OHLCV, `alternative.me` for Fear & Greed since 2018).
  No API key, no cost, no paywall to reproduce results.
- **CoinMarketCap where it's the differentiator.** Live signals and the demo run on the
  CMC Agent Hub (MCP + REST) — Fear & Greed, altcoin-season, sentiment, derivatives —
  the data most entrants won't fully exploit.

## Headline strategy

**Regime-switched time-series momentum + Fear & Greed overlay, volatility-targeted.**
An HMM separates *trend* vs *chop* regimes; momentum trades only in trend; position
size scales inversely with volatility; sentiment tilts exposure up in extreme fear and
trims in extreme greed. Demoed **beating a naive Fear & Greed contrarian baseline** on
one chart.

> Backtest metrics will be published here once the engine run lands (in progress).

## Quickstart

```bash
make install                     # venv + deps + editable engine
make backtest                    # run the headline strategy from its spec
make demo                        # headline vs baseline, side by side
```

Or directly:

```bash
python scripts/backtest.py --spec assets/regime-momentum.json --out examples
```

No API key required. To enable CMC-branded live signals + the MCP demo, copy
`.env.example` → `.env` and add a free [CMC Basic key](https://pro.coinmarketcap.com/signup).

## How it maps to the hackathon

| Target | How |
|---|---|
| **Track 2 placement** | A backtestable CMC Skill that generates + validates strategies. |
| **Best Use of Agent Hub** | Live signals + demo on CMC MCP/REST; strategy keys on CMC's differentiated data. |
| **Reproducibility requirement** | Keyless data sources → anyone re-runs with zero setup. |

## Architecture

```
SKILL.md ──▶ StrategySpec (JSON, the IR) ──▶ scripts/backtest.py ──▶ forge engine
                                                                       ├─ data/     keyless OHLCV + Fear&Greed (CMC optional)
                                                                       ├─ strategy/ spec schema · pure signals · HMM regime
                                                                       └─ backtest/ vectorbt + walk-forward → metrics.json + tearsheet.png
```

See [`docs/superpowers/specs/2026-06-14-strategy-forge-design.md`](docs/superpowers/specs/2026-06-14-strategy-forge-design.md) for the full design.

## License

MIT © 2026 Ste Tang. Third-party attributions in [`THIRD_PARTY.md`](THIRD_PARTY.md).
Not financial advice.
