# Third-Party Notices & Attributions

Strategy Forge is MIT-licensed. It depends on and adapts the following open-source
work. We thank their authors.

## Runtime dependencies (installed via pip, not vendored)

| Project | License | Use |
|---|---|---|
| [vectorbt](https://github.com/polakowo/vectorbt) | Apache-2.0 + Commons Clause | Backtesting engine (portfolio simulation, stats, plots). We do **not** resell vectorbt; we import it. Note: the Commons Clause restricts selling software whose value derives primarily from vectorbt — anyone building a *commercial* product on this Skill must comply with vectorbt's license. |
| [hmmlearn](https://github.com/hmmlearn/hmmlearn) | BSD-3-Clause | Hidden Markov Model for market-regime detection. |
| [pydantic](https://github.com/pydantic/pydantic) | MIT | Strategy-spec schema validation. |
| [python-coinmarketcap (rsz44)](https://github.com/rsz44/python-coinmarketcap) | MIT | Optional CoinMarketCap data provider (`coinmarketcapapi`). |
| [requests](https://github.com/psf/requests) | Apache-2.0 | HTTP for keyless data sources + CMC REST. |
| numpy / pandas / scipy / scikit-learn / matplotlib | BSD-3-Clause | Numerics, data handling, plotting. |

## Ported ideas (re-implemented, not copied)

- **Regime detection + walk-forward harness** — design inspired by
  [MarketRegimeTrader](https://github.com/0x596173736972/MarketRegimeTrader) (MIT).
  Logic is re-implemented for this codebase; no source files copied.
- **Skill packaging conventions** — follow the open
  [Agent Skills specification](https://agentskills.io/specification) and the house
  style of [CoinMarketCap's official skills](https://github.com/coinmarketcap-official/skills-for-ai-agents-by-CoinMarketCap) (MIT).

## Data sources

| Source | Access | Use |
|---|---|---|
| [data-api.binance.vision](https://github.com/binance/binance-public-data) | Keyless public mirror | Historical daily OHLCV (reproducible backtests). |
| [alternative.me Fear & Greed Index](https://alternative.me/crypto/fear-and-greed-index/) | Keyless public API | Historical Fear & Greed series since 2018. |
| [CoinMarketCap Agent Hub](https://coinmarketcap.com/api/agent) | Free Basic key / MCP | Live differentiated signals + demo ("Best Use of Agent Hub"). |

No third-party code under GPL/AGPL or unlicensed terms is copied into this repository.
