# Strategy Forge — Design Spec

> A CoinMarketCap-powered crypto **strategy generation + backtesting Skill**.
> BNB Hack: AI Trading Agent Edition — **Track 2 (Strategy Skills)**, zero-cost path.
> Date: 2026-06-14 · Build deadline: 2026-06-21 · Author: Ste Tang (AI-assisted)

## 1. Goal & winning thesis

Win a Track 2 placement ($3k/$2k/$1k) **and** the cross-track **Best Use of Agent Hub ($2k)** with one zero-cost build.

Track 2 is panel-judged on four axes: **technical execution, originality, real-world relevance, demo**. Our edge as a solo+AI builder is *craft*, not luck. So we optimize each axis deliberately:

- **Originality** — Don't ship "one momentum strategy with RSI+MACD+Fear&Greed" (what most entrants will do). Ship a *strategy **generator***: natural-language intent → a structured, backtestable **strategy spec** (intermediate representation) → a rigorous backtest. This is the brief's own framing ("Quantopian-style strategy generation, adapted to crypto and authored as an LLM Skill"), executed literally.
- **Technical execution** — Real `vectorbt` backtests on real CMC historical data, with **walk-forward / out-of-sample validation**, transaction costs, and overfit honesty. Reproducible from a public repo. ≥80% unit-test coverage on pure logic.
- **Real-world relevance** — Clear user (a trader/agent-author who wants idea → validated strategy without writing quant code). Adoption path: installs as a CMC Agent-Hub Skill in Claude Code / OpenClaw; the *same spec* can drive a live Track-1 agent. Not a toy.
- **Demo** — One screen: NL request → compiled spec → backtest → an equity curve (regime-shaded) that **beats a naive Fear & Greed baseline**, with Sharpe/drawdown side by side.

## 2. Headline strategy (what the demo showcases)

**Primary:** Regime-switched **time-series (trend) momentum** + **Fear & Greed overlay**, **volatility-targeted**.
- Regime: HMM on returns+realized-vol → `trend` vs `chop`. Trade momentum only in `trend`.
- Momentum: trailing N-day return / fast-vs-slow MA crossover from CMC OHLCV.
- Sizing: `target_vol / realized_vol` (vol-scaling) → roughly constant dollar risk.
- Sentiment overlay: tilt up on extreme fear (F&G ≤ 25), trim on extreme greed (≥ 75).

**Baseline to beat (also shipped):** naive Fear & Greed contrarian (`buy ≤20 / sell ≥80`). The single comparison chart — *naive F&G vs regime-switched vol-scaled momentum + F&G* — tells the whole story.

**Evidence basis (from research):** time-series momentum is the best-documented crypto edge (reported Sharpe ~1.5–1.7 vs HODL ~0.8–1.3); regime-switching + vol-targeting lifts risk-adjusted return and survives costs. **Funding-rate carry is intentionally NOT a headline signal** — CMC does not serve perpetual funding natively (cross-confirmed); we mention it only as a flagged optional extension.

## 3. Architecture

Two clean layers: the **Skill** (LLM-facing orchestrator, the Track 2 deliverable) and the **engine** (a real, tested Python package the Skill's black-box script calls).

```
strategy-forge/                         # repo root (= working dir)
├── SKILL.md                            # orchestrator: NL intent → spec → backtest → results (progressive disclosure)
├── scripts/
│   ├── backtest.py                     # black-box CLI: spec JSON in → metrics JSON + tearsheet PNG out
│   └── requirements.txt                # vectorbt|backtesting.py, python-coinmarketcap, hmmlearn, pandas, numpy, pydantic, matplotlib
├── forge/                              # the engine package (pure, tested, importable)
│   ├── data/loader.py                  # CMC adapter: OHLCV + Fear&Greed → validated DataFrame; SQLite cache
│   ├── data/cmc_client.py              # thin wrapper over python-coinmarketcap + REST v3 fear-and-greed
│   ├── strategy/spec.py                # StrategySpec schema (pydantic) — the IR; validation at the boundary
│   ├── strategy/signals.py             # PURE signal functions (momentum, F&G overlay, vol-target)
│   ├── strategy/regime.py              # HMM regime detection (ported from MarketRegimeTrader, MIT)
│   ├── backtest/engine.py              # vectorbt wrapper → stats dict + equity/drawdown plots
│   └── backtest/validate.py            # walk-forward split, in/out-of-sample, overfit metrics
├── references/                         # loaded on demand by the Skill
│   ├── strategy-spec-schema.md         # the human-readable spec contract
│   ├── cmc-endpoints.md                # which CMC MCP/REST tool feeds which field
│   ├── momentum.md / mean-reversion.md / regime-switching.md
├── assets/                             # ready-to-run spec templates
│   ├── regime-momentum.json            # the headline
│   ├── fgi-contrarian.json             # the baseline
│   └── ema-crossover.json
├── tests/                              # pytest; ≥80% on forge/strategy + forge/data
├── examples/                           # committed sample tearsheets + a recorded run
├── README.md                           # setup, reproducible demo, on-chain-free note, AI Build Log
└── LICENSE                             # MIT
```

**Data flow:** `SKILL.md` parses user intent → emits a `StrategySpec` JSON → calls `python scripts/backtest.py --spec spec.json` (black box) → `forge` loads CMC data (cached to SQLite for determinism), builds pure boolean signals, runs vectorbt, walk-forward-validates, writes `metrics.json` + `tearsheet.png` → `SKILL.md` renders a fixed results template (CAGR, Sharpe, max DD, win rate, paths) + green/red flags + "not financial advice".

**The StrategySpec is the keystone IR** — it is simultaneously the human-readable artifact, the backtest input, and (future) the live-agent config. Example:

```json
{
  "name": "regime-momentum",
  "universe": ["BTC", "ETH", "BNB"],
  "interval": "1d",
  "date_range": ["2022-01-01", "2025-12-31"],
  "signal": {"type": "ts_momentum", "lookback_days": 30, "fast_ma": 10, "slow_ma": 100},
  "regime_gate": {"type": "hmm", "features": ["returns", "realized_vol"], "trade_in": "trend"},
  "sentiment_overlay": {"fng_buy_below": 25, "fng_trim_above": 75},
  "sizing": {"type": "vol_target", "target_vol": 0.20, "vol_lookback_days": 20},
  "costs": {"slippage_bps": 30, "fee_bps": 25},
  "validation": {"scheme": "walk_forward", "train_days": 365, "test_days": 90}
}
```

## 4. Tech stack & reuse map (license-checked)

| Layer | Choice | License | How used |
|---|---|---|---|
| Backtest engine | `vectorbt` | Apache-2.0 + Commons Clause | pip dep, wrapped; attribute. Fallback `backtesting.py` (AGPL) behind same interface if Numba/3.13 breaks. |
| Data client | `rsz44/python-coinmarketcap` | MIT | OHLCV historical + v3 Fear&Greed |
| Regime brain | port from `0x596173736972/MarketRegimeTrader` | MIT | HMM detector, cost model, walk-forward harness — **port, attribute** |
| HMM | `hmmlearn` | BSD-3 | regime fitting |
| Spec validation | `pydantic` | MIT | StrategySpec schema, boundary validation |
| Skill format | `anthropics/skills` template + CMC `crypto-research/SKILL.md` house style | Apache-2.0 / MIT | scaffold, frontmatter conventions, black-box-script pattern |
| Live demo data | CMC Agent Hub **MCP** (`mcp.coinmarketcap.com/mcp`) | proprietary API (free Basic key) | live signal read in the demo → "Best Use of Agent Hub" |

**License discipline:** never copy GPL (`freqtrade-strategies`) or no-license (`hackingthemarkets/...`) files — port ideas only. Do not vendor `marketcalls/vectorbt-backtesting-skills` (license returns null). Build the Skill scaffold clean from open templates.

## 5. CMC Agent Hub integration ("Best Use of Agent Hub" case)

**Data sourcing decision (verified 2026-06-14).** Backtests use a **100% keyless, reproducible** base so any judge can re-run with no API key or cost:
- **Price OHLCV:** `data-api.binance.vision` (Binance public mirror) — keyless daily candles back to ≥2021. (Binance.com proper is geo-blocked from the build location; the mirror is not.)
- **Fear & Greed history:** `api.alternative.me/fng` — keyless, full daily series 2018-02-01→present (3,052 pts verified).

**CMC layers on top** (not as the reproducibility-critical path) to win "Best Use of Agent Hub": (1) **MCP** (`mcp.coinmarketcap.com/mcp`) for the live interactive demo — `get_crypto_quotes_latest`, `get_global_metrics_latest` (Fear&Greed + altcoin-season), `get_crypto_technical_analysis`, `trending_crypto_narratives`; (2) **`coinmarketcapapi`** (rsz44) for `fearandgreed_*`, `globalmetrics_*`, `cryptocurrency_ohlcv_historical` when a Pro/hackathon key is present. The data layer is behind one `MarketDataSource` interface; CMC is a swappable provider, defaulting to the keyless sources so nothing breaks without a key.

## 6. Risks & first-week de-risking

1. **vectorbt + Numba on Python 3.13 (HIGHEST RISK).** Spike install first. Fallbacks in order: pinned numpy/numba in a 3.11 venv → `backtesting.py` → minimal hand-rolled vectorized backtest. Engine is behind an interface so the strategy code never depends on the choice.
2. ~~CMC free-tier OHLCV history~~ **RESOLVED** — backtests use keyless `data-api.binance.vision` (daily OHLCV ≥2021) + `api.alternative.me/fng` (F&G since 2018); CMC OHLCV is an optional provider when a Pro/hackathon key exists.
3. ~~v3 Fear&Greed wrapper currency~~ **RESOLVED** — keyless `alternative.me` is the reproducible F&G source; `coinmarketcapapi.fearandgreed_*` is the CMC-branded live alternative behind the same interface.
   - **Open follow-up:** obtain a free CMC Basic key to light up CMC-specific live signals + MCP demo (not blocking; CMC mocked in tests).
4. **MarketRegimeTrader coupling.** Port pure functions, not its data layer.
5. **`skills-ref validate` accepts CMC non-standard frontmatter** (`user-invocable`, `allowed-tools`). Verify; keep both spec-valid and CMC-installable.

## 7. Build plan (7 days)

- **D1 (today, 6/14):** Free CMC key; project scaffold; **spike the engine install matrix** (vectorbt→fallback); confirm CMC OHLCV + Fear&Greed reachable. Wire CMC MCP into the session for the demo.
- **D2:** `forge/data` (loader + cmc_client + SQLite cache) TDD; `StrategySpec` schema. → code review.
- **D3:** `forge/strategy` pure signals + HMM regime (ported) TDD. → code review.
- **D4:** `forge/backtest` engine + walk-forward validation; produce first real tearsheet. → code review.
- **D5:** `scripts/backtest.py` black-box CLI + `SKILL.md` orchestrator + `references/` + `assets/` specs. Validate with `skills-ref`.
- **D6:** Polish demo (regime-shaded equity curve, baseline comparison), README + AI Build Log, examples; full code+security review.
- **D7 (≤6/21):** Harden, finalize repo, record demo video, submit on DoraHacks.

## 8. Definition of done

- [ ] `SKILL.md` validates; installable as a CMC Skill; runs end-to-end from NL intent.
- [ ] `python scripts/backtest.py --spec assets/regime-momentum.json` produces metrics JSON + tearsheet, reproducibly, from a clean checkout.
- [ ] Headline strategy demonstrably beats the F&G baseline on out-of-sample data, with costs.
- [ ] ≥80% unit coverage on `forge/strategy` + `forge/data`; every code milestone passed code review (CRITICAL/HIGH fixed).
- [ ] README reproducible; demo video; AI Build Log; MIT license + third-party attributions.
- [ ] Submitted to DoraHacks before 2026-06-21.
