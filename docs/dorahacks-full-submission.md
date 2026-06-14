# DoraHacks BUIDL — full submission (single source of truth, paste-ready)

Project: **Strategy Forge** · Hackathon: **BNB Hack: AI Trading Agent Edition** ·
Track: **Track 2 — Strategy Skills** (+ Best Use of CoinMarketCap Agent Hub).

> A Demo video is **optional** — the hackathon accepts "public repo + a demo link/video
> **OR** clear setup instructions", and this repo already provides the repo + setup +
> example charts. A short video only adds to the "demo" score; you can submit without it.
> This file is kept in sync as we go — every field for every tab.

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

**Demo video** *(optional, bonus)*: a 75s screen-recording lifts the demo score (script
below). Not required — the repo + setup instructions already satisfy the requirement, so
you can leave this blank and submit, then add a video later (BUIDLs are editable).

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
- **Track**: `📊 Strategy Skills ($6,000)` ✅
  - "Add More Tracks →": if a "Best Use of CoinMarketCap Agent Hub" (CMC special prize)
    track is listed there, add it too; otherwise leave just Strategy Skills.
- **Ask hackers questions** (contact):
  ```
  Telegram: @Stetang  (email: stetang98@gmail.com)
  ```
- **Ask BUIDLers questions** (contact):
  ```
  Telegram: @Stetang  (email: stetang98@gmail.com)
  ```
- **Share your agent address here (for track 1)**:
  ```
  N/A — Track 2 (Strategy Skills), no on-chain agent / registration
  ```
- ☑️ Check **"I agree to the Terms of Use Agreement and Participant Agreement"**

---

## DEMO VIDEO SCRIPT (~75s, one-take terminal screen-recording)

**Setup:** macOS QuickTime → File → New Screen Recording (or `Cmd+Shift+5`). Large
terminal font. In the repo with the venv active: `cd ~/Desktop/BNB_Hack && source .venv/bin/activate`.
Upload the result to YouTube (Unlisted is fine) and paste the link in the Demo video field.

| Time | Do this on screen | Say / caption |
|---|---|---|
| 0:00–0:08 | Show the repo README (or just the terminal title) | "Most crypto backtests are cherry-picked and impossible to reproduce. Strategy Forge fixes that — describe a strategy in plain English, get a rigorous, reproducible backtest." |
| 0:08–0:22 | Run: `python scripts/market_context.py --symbol BNB` | "Live CoinMarketCap Agent Hub data — Fear & Greed, dominance, price — pulled in real time." |
| 0:22–0:33 | Run: `python scripts/backtest.py --spec assets/cake-trend-rider.json --out examples` | "It compiles a strategy spec and runs a walk-forward, cost-adjusted backtest." |
| 0:33–0:52 | Run: `open examples/cake-trend-rider.png` (the chart opens) | "On CAKE — which fell 93% — the SAME trend strategy made +39% by exiting the downtrend. Buy-and-hold would've wiped you out." |
| 0:52–1:05 | Run: `python -m pytest -q tests/ | tail -1` (shows `122 passed`) | "122 tests, ~94% coverage. 100% reproducible — no API key. `make demo` regenerates everything." |
| 1:05–1:18 | Show `SKILL.md` or the GitHub repo page | "An installable CoinMarketCap Skill. BNB Hack Track 2, Best Use of Agent Hub. github.com/stetang98/strategy-forge." |

**Tips:** captions are enough if you don't want voiceover. Keep each command's output on
screen ~2–3s. The CAKE chart (0:33) is the money shot — let it linger.

---

## (OPTIONAL) MILESTONE / PROGRESS UPDATE

Not required for submission — a nice engagement touch on the BUIDL page. If you add one:

- **Milestone type**: `里程碑 / Milestone`  *(avoid "Funding information" — the hackathon bans fundraising during the event)*
- **Date**: keep default (today) — e.g. `2026/06/14`
- **Details**:
  ```
  Strategy Forge v1.0 is live — a CoinMarketCap Agent-Hub Skill that turns a plain-English strategy idea into a walk-forward, cost-adjusted, keyless-reproducible backtest. 122 tests (~94% coverage), verified-live CMC Agent Hub integration, look-ahead-safe execution. Submitted to BNB Hack: AI Trading Agent Edition — Track 2 (Strategy Skills).
  ```
- **Related links**:
  - Related webpage: *(blank)*
  - GitHub repo: `https://github.com/stetang98/strategy-forge`
  - X/Twitter post: *(blank, optional)*

---

### Checklist
- [x] TAB 1 Profile — name · logo · vision · category (L1=BNB Chain) · AI-Agent=No · GitHub · socials
- [x] TAB 2 Details — full image-rich body
- [x] TAB 3 Team — invite blank · team information
- [x] TAB 4 Contact — email · telegram · X
- [x] TAB 5 Submission — Track 2
- [ ] *(optional)* **Demo video** — bonus for the demo score; NOT required (repo + setup instructions already satisfy it). Can be added after submitting.
