# DoraHacks BUIDL — full submission (single source of truth, paste-ready)

Project: **Strategy Forge** · Hackathon: **BNB Hack: AI Trading Agent Edition** ·
Track: **Track 2 — Strategy Skills** (+ Best Use of CoinMarketCap Agent Hub).

> ⚠️ Only one thing still needed: a **Demo video (YouTube)**. Everything else below is final & paste-ready.
> This file is kept in sync as we go — it has every field for every tab.

---

## TAB 1 — PROFILE

**BUIDL name**
```
Strategy Forge
```

**Logo**: upload `logo.png` (repo root, 480×480 PNG ✅).

**Vision** (≤256 chars)
```
Most crypto backtests are cherry-picked and irreproducible. Strategy Forge is a CoinMarketCap Skill: describe a strategy in plain English, get a rigorous, walk-forward, look-ahead-safe backtest you can reproduce with zero API keys — in seconds.
```

**Category**: `Crypto / Web3`
- Key innovation domains: `AI Agents`, `Trading`, `DeFi`
- Layer-1s / L1s: `BNB Chain`
- Layer-2s / Appchains: *(leave blank)*

**Is this BUIDL an AI Agent?**: `No`

**GitHub**:
```
https://github.com/stetang98/strategy-forge
```

**Project website** *(optional)*: *(leave blank)*

**Demo video** ⚠️: record + upload to YouTube, paste the link.

**Social links**:
```
https://x.com/Stetang3438
https://github.com/stetang98
```

---

## TAB 2 — DETAILS  (paste the whole block below into the markdown editor)

````markdown
# ⚒️ Strategy Forge — Quantopian for crypto, authored as a Skill

**Describe a crypto trading strategy in plain English → get a rigorous, reproducible backtest.**

A CoinMarketCap Agent-Hub Skill. *BNB Hack: AI Trading Agent Edition — Track 2 · zero-cost · 100% reproducible · 122 tests.*

---

## The story in one chart

On **CAKE**, which collapsed **−93%**, the same trend-following strategy *made +39%* by exiting the downtrend. Buy-and-hold would have wiped you out.

![Strategy Forge on CAKE](https://raw.githubusercontent.com/stetang98/strategy-forge/main/examples/cake-trend-rider.png)

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

![Strategy Forge on BNB](https://raw.githubusercontent.com/stetang98/strategy-forge/main/examples/trend-rider.png)

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
````

---

## TAB 3 — TEAM

**Invite new members**: *(leave blank — solo project)*

**Team information** *(required, paste below)*
```
Solo build. Strategy Forge was designed and engineered end-to-end by Ste Tang (GitHub @stetang98 · X @Stetang3438) — architecture, the vectorbt backtesting engine, strategy research, the CoinMarketCap Agent Hub integration, and a 122-test suite (~94% coverage). Built test-first with Claude Code, with an adversarial code-review pass after every module. A web3 builder focused on AI agents and crypto tooling.
```

---

## TAB 4 — CONTACT
```
Email:     stetang98@gmail.com
Telegram:  @Stetang
X/Twitter: https://x.com/Stetang3438
```
*(WeChat backup, optional: SteForget)*

---

## TAB 5 — SUBMISSION
- **Hackathon**: BNB Hack: AI Trading Agent Edition
- **Track**: `Track 2 — Strategy Skills`
- **Special prize targeted**: Best Use of CoinMarketCap Agent Hub
- **On-chain agent address (Track 1 only)**: N/A — Track 2 has no on-chain registration.

---

### Checklist
- [x] TAB 1 Profile — name · logo · vision · category (L1=BNB Chain) · AI-Agent=No · GitHub · socials
- [x] TAB 2 Details — full image-rich body
- [x] TAB 3 Team — invite blank · team information
- [x] TAB 4 Contact — email · telegram · X
- [x] TAB 5 Submission — Track 2
- [ ] **Demo video (YouTube)** — record + upload, paste link  ← only remaining blocker
