# Strategy Forge — DoraHacks submission

> Paste-ready copy for the BNB Hack: AI Trading Agent Edition submission form.
> **Track 2 — Strategy Skills** · also contesting **Best Use of CoinMarketCap Agent Hub**.

## One-liner

Describe a crypto trading idea in plain English → get a rigorous, reproducible,
out-of-sample backtest. A CoinMarketCap Agent-Hub Skill — *Quantopian for crypto.*

## What it does

Strategy Forge is an installable **CMC Skill** (`SKILL.md`). The agent compiles a
natural-language brief into a structured **StrategySpec**, then runs a real
`vectorbt` backtest with **walk-forward validation, simulated transaction costs, and
look-ahead-safe execution**, and returns an equity curve, Sharpe/Sortino/Calmar/
max-drawdown, and an honest out-of-sample verdict versus buy-and-hold. It is a
strategy *generator*, not one hard-coded rule — exactly the "Quantopian-style strategy
generation, adapted to crypto and authored as an LLM Skill" the track asks for.

## The strategy (how the results were achieved)

The headline family is **trend-following (EMA 10/50) with volatility targeting**:
- **Signal:** long while the fast EMA is above the slow EMA — time-series momentum,
  the best-documented systematic crypto edge. It *exits* downtrends, which is what
  preserves capital when an asset collapses.
- **Sizing:** exposure = `target_vol / realized_vol`, so position size shrinks when
  volatility spikes (and is capped at 1× — spot, no leverage).
- **Optional risk dial:** an HMM (Hidden Markov Model) regime gate on
  (returns, volatility) that trades only in the detected *trend* regime — it lowers
  drawdown further, at the cost of some upside. We show this tradeoff honestly rather
  than hiding it.
- **Validation:** walk-forward — each test fold is scored by a model fit only on prior
  data; decisions on bar *t* execute on bar *t+1*. The reported out-of-sample number is
  the one to trust.

## Results (walk-forward, cost-adjusted, keyless-reproducible)

| Strategy | Asset | Return | Sharpe | Max DD | Out-of-sample | Buy & Hold |
|---|---|---:|---:|---:|---:|---:|
| trend-rider | BNB | +840% | 1.03 | −58% | +52% | +1514% |
| trend-rider | CAKE | +39% | 0.39 | −71% | +16% | **−93%** |
| regime-guard | CAKE | +13% | 0.22 | −54% | +13% | −93% |
| fgi-contrarian *(baseline)* | BNB | −83% | — | −84% | — | +1514% |

The story is **risk discipline, not headline return**: the same strategy captured most
of BNB's bull at far lower drawdown, and on CAKE — which fell 93% — it *made +39%* by
exiting the downtrend. The naive Fear & Greed baseline loses; that's the bar a real
strategy must clear.

## How it uses the CoinMarketCap Agent Hub (Best Use of Agent Hub)

- **Two access paths:** a live CoinMarketCap path (`scripts/market_context.py` + every
  backtest run pulls live Fear & Greed, BTC/ETH dominance, price, market cap — **verified
  live against the CMC API**); and a **keyless, reproducible** path for backtests so any
  judge re-runs every number with no API key.
- **Keys on CMC's differentiated data** (Fear & Greed, dominance, market structure), not
  just price. The same CMC client can source the Fear & Greed series for sentiment strategies.
- Ships in the official CMC **`SKILL.md`** Agent-Skill format.

## Reproduce in 30 seconds (no API key)

```bash
make install && make demo      # regenerates every tearsheet in examples/
make test                      # 97 tests, 94% coverage
```

## Tech & engineering

Python · vectorbt · hmmlearn · pydantic. Built test-first (TDD, 97 tests, 94% coverage)
with an independent adversarial code-review pass after every module — which caught and
fixed real look-ahead-bias and out-of-sample-integrity bugs before shipping. Security:
bandit clean, pip-audit clean, no secrets, validated inputs. See the **AI Build Log** in
`README.md`.

## Links

- **Repository:** <https://github.com/stetang98/strategy-forge>  *(update if the name differs)*
- **Skill:** [`SKILL.md`](../SKILL.md) · **Design:** [`docs/superpowers/specs/2026-06-14-strategy-forge-design.md`](superpowers/specs/2026-06-14-strategy-forge-design.md)
- **Demo:** the committed tearsheets in [`examples/`](../examples) + `make demo`

*Not financial advice. Backtests are historical and do not guarantee future results.*
