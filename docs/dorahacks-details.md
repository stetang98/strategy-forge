# ⚒️ Strategy Forge — Quantopian for crypto, authored as a Skill

**Describe a crypto trading strategy in plain English → get a rigorous, reproducible backtest.**

A CoinMarketCap Agent-Hub Skill. *BNB Hack: AI Trading Agent Edition — Track 2 · zero-cost · 100% reproducible · 122 tests.*

---

## The story in one chart

On **CAKE**, which collapsed **−93%**, the same trend-following strategy *made +39%* by exiting the downtrend. Buy-and-hold would have wiped you out.

![Strategy Forge on CAKE: +39% while buy-and-hold fell 93%](https://raw.githubusercontent.com/stetang98/strategy-forge/main/examples/cake-trend-rider.png)

## The problem

Crypto traders and AI-agent builders have great strategy ideas but no fast, trustworthy way to validate them. A real backtest means writing quant code, sourcing data, and avoiding subtle look-ahead bias — so most "backtests" are cherry-picked and impossible to reproduce.

## What it is

Strategy Forge is an installable **CoinMarketCap Agent-Hub Skill**. You describe a trading idea; the Skill compiles it into a structured, validated **strategy spec**, then runs a real `vectorbt` backtest with **walk-forward validation, simulated transaction costs, and look-ahead-safe execution** — returning an equity curve, Sharpe / Sortino / Calmar / max-drawdown, and an honest out-of-sample verdict vs buy-and-hold. It's a strategy **generator**, not one hard-coded rule.

## Results (walk-forward, cost-adjusted, reproducible with no API key)

| Strategy | Asset | Return | Sharpe | Max DD | Out-of-sample | Buy & Hold |
|---|---|---:|---:|---:|---:|---:|
| **trend-rider** | BNB | **+840%** | 1.03 | −58% | +52% | +1514% |
| **trend-rider** | CAKE | **+39%** | 0.39 | −71% | +16% | **−93%** |
| regime-guard | CAKE | +13% | 0.22 | −54% | +13% | −93% |
| fgi-contrarian *(baseline)* | BNB | −83% | — | −84% | — | +1514% |

The point is **risk discipline, not headline return**: the same strategy captured most of BNB's bull at far lower drawdown, sitting in cash through the 2022 bear. The naive Fear & Greed baseline loses — that's the bar a real strategy must clear.

![Strategy Forge on BNB: +840%, Sharpe 1.03, much lower drawdown](https://raw.githubusercontent.com/stetang98/strategy-forge/main/examples/trend-rider.png)

## CoinMarketCap Agent Hub — verified live

Backtests are keyless and reproducible; **CoinMarketCap is layered for live signals**. With a free CMC key, `scripts/market_context.py` and *every* backtest run pull a real-time reading from the CMC Agent Hub — verified live against the CMC API:

```text
=== CoinMarketCap Agent Hub :: BNB market context [LIVE · CMC Pro] ===
  price: 611.12 · Fear & Greed: 21 (Fear) · BTC dominance: 58.8% · total mcap: $2.19T
```

Two access paths (live CMC + a keyless reproducible path), keyed on CMC's **differentiated data** — Fear & Greed, dominance, market structure — not just price. Shipped as an official `SKILL.md` Agent Skill.

## Built with AI, test-first

Built end-to-end with Claude Code, **test-driven (122 tests, ~94% coverage)**, with an independent adversarial code-review pass after every module — which caught and fixed real **look-ahead-bias and out-of-sample-integrity bugs** before shipping. When the original "regime-momentum" idea *lost money* in backtest, it was dropped: trend-following + vol-targeting is the honest winner, and the numbers above are exactly what the engine produced. Security: bandit clean, pip-audit clean, no secrets, validated inputs.

## Reproduce in 30 seconds (no API key)

```bash
make install && make demo      # regenerates every tearsheet above
make test                      # 122 tests
```

## How it maps to the hackathon

- **Track 2 placement** — a backtestable CMC Skill that *generates and validates* strategies, not one fixed rule.
- **Best Use of Agent Hub** — live CMC signals + the strategy keys on CMC's differentiated data.
- **Reproducibility** — keyless sources, so any judge re-runs every number with zero setup.

**Tech:** Python · vectorbt · hmmlearn · pydantic.

## Links

- **Repo:** https://github.com/stetang98/strategy-forge
- **Skill:** `SKILL.md` · **Reproduce:** `make demo`

*Not financial advice. Backtests are historical and do not guarantee future results.*
