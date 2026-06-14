# DoraHacks BUIDL — full submission (paste-ready)

Project: **Strategy Forge** · Hackathon: **BNB Hack: AI Trading Agent Edition** ·
Track: **Track 2 — Strategy Skills** (+ Best Use of CoinMarketCap Agent Hub).

> ⚠️ ONE action item before you can finish: a **Demo video (YouTube)** is required.
> Ask me for the 60–90s script. Everything else below is paste-ready.

---

## 1) PROFILE

**BUIDL (project) name**
```
Strategy Forge
```

**BUIDL logo** — upload `logo.png` (repo root, 480×480 PNG, ✅).

**Vision** (≤256 chars)
```
Most crypto backtests are cherry-picked and irreproducible. Strategy Forge is a CoinMarketCap Skill: describe a strategy in plain English, get a rigorous, walk-forward, look-ahead-safe backtest you can reproduce with zero API keys — in seconds.
```

**Category**: `Crypto / Web3`
- Key innovation domains (sub-categories): `AI Agents`, `Trading`, `DeFi`
- Layer-1s / L1s: `BNB Chain`
- Layer-2s / Appchains: *(leave blank)*

**Is this BUIDL an AI Agent?**: `No` *(it's a strategy-generation Skill, the Track 2 deliverable — not an autonomous agent)*

**GitHub** *
```
https://github.com/stetang98/strategy-forge
```

**Project website** *(optional)*: *(leave blank)*

**Demo video** * ⚠️ record + upload to YouTube, then paste the link here.

**Social links** (≥1)
```
https://x.com/Stetang3438
https://github.com/stetang98
```

---

## 2) DETAILS  (project description — supports markdown)

```markdown
## Strategy Forge — Quantopian for crypto, authored as a Skill

**Describe a crypto strategy in plain English → get a rigorous, reproducible backtest.**

### The problem
Crypto traders and AI-agent builders have great strategy ideas but no fast, trustworthy
way to validate them. A real backtest means writing quant code, sourcing data, and
avoiding subtle look-ahead bias — so most "backtests" are cherry-picked and impossible
to reproduce.

### What it is
Strategy Forge is an installable **CoinMarketCap Agent-Hub Skill**. You describe a
trading idea; the Skill compiles it into a structured, validated **strategy spec**, then
runs a real vectorbt backtest with **walk-forward validation, simulated transaction
costs, and look-ahead-safe execution** — returning an equity curve, Sharpe / Sortino /
Calmar / max-drawdown, and an honest out-of-sample verdict vs buy-and-hold. It's a
strategy *generator*, not one hard-coded rule.

### Results (walk-forward, cost-adjusted, reproducible with no API key)
| Strategy | Asset | Return | Sharpe | Max DD | Out-of-sample | Buy & Hold |
|---|---|---:|---:|---:|---:|---:|
| trend-rider | BNB | +840% | 1.03 | −58% | +52% | +1514% |
| trend-rider | CAKE | +39% | 0.39 | −71% | +16% | **−93%** |
| regime-guard | CAKE | +13% | 0.22 | −54% | +13% | −93% |
| fgi-contrarian (baseline) | BNB | −83% | — | −84% | — | +1514% |

The point is **risk discipline, not headline return**: the same trend-following strategy
captured most of BNB's bull at far lower drawdown — and on CAKE, which collapsed 93%, it
*made +39%* by exiting the downtrend. The naive Fear & Greed baseline loses; that's the
bar a real strategy must clear.

### CoinMarketCap Agent Hub (verified live)
Backtests are keyless and reproducible; CoinMarketCap is layered for live signals. With a
free CMC key, `scripts/market_context.py` and every backtest run pull a real-time reading
from the CMC Agent Hub (Fear & Greed, BTC/ETH dominance, price, market cap) — verified
live against the CMC API. Two access paths (live CMC + a keyless reproducible path), keyed
on CMC's differentiated data, shipped as an official `SKILL.md` Agent Skill.

### Built with AI, test-first
Built end-to-end with Claude Code, test-driven (122 tests, ~94% coverage), with an
independent adversarial code-review pass after every module — which caught and fixed real
look-ahead-bias and out-of-sample-integrity bugs before shipping. When the original
"regime-momentum" idea lost money in backtest, it was dropped: trend-following + vol-
targeting is the honest winner, and the numbers above are exactly what the engine
produced. Security: bandit clean, pip-audit clean, no secrets, validated inputs.

### Reproduce in 30 seconds (no API key)
```
make install && make demo      # regenerates every tearsheet
make test                      # 122 tests
```

### How it maps to the hackathon
- Track 2 placement: a backtestable CMC Skill that *generates and validates* strategies.
- Best Use of Agent Hub: live CMC signals + the strategy keys on CMC's differentiated data.
- Reproducibility: keyless sources → any judge re-runs every number with zero setup.

Tech: Python · vectorbt · hmmlearn · pydantic. Not financial advice.
```

> Tip: in the DoraHacks editor you can also embed the tearsheets from the repo
> (`examples/cake-trend-rider.png`, `examples/trend-rider.png`) as images.

---

## 3) TEAM

- **Team name**: `Strategy Forge`
- **Members**:
  - **Ste Tang** — Solo builder. Role: architecture, engine, strategy research, CMC
    integration, testing. GitHub: `stetang98` · X: `@Stetang3438`.
- **Looking for teammates?**: `No`

---

## 4) CONTACT

```
Email:     stetang98@gmail.com
Telegram:  @Stetang
X/Twitter: https://x.com/Stetang3438
```
*(WeChat backup, optional: SteForget)*

---

## 5) SUBMISSION

- **Hackathon**: BNB Hack: AI Trading Agent Edition (CoinMarketCap × Trust Wallet × BNB Chain)
- **Track**: `Track 2 — Strategy Skills`
- **Special prize targeted**: Best Use of CoinMarketCap Agent Hub
- **On-chain agent address (Track 1 only)**: N/A — Track 2 has no on-chain registration.
- If asked "how did you use the sponsor tools / AI": point to the README **AI Build Log**
  and `references/cmc-endpoints.md` (live CMC integration), repo
  `https://github.com/stetang98/strategy-forge`.

---

### Checklist
- [x] name · logo · vision · category · L1=BNB Chain · AI-Agent=No · GitHub · socials
- [x] details · team · contact · submission (track 2)
- [ ] **Demo video (YouTube)** — record + upload, then paste the link  ← only blocker
