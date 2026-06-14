# CoinMarketCap Agent Hub integration

Strategy Forge is **CoinMarketCap-native** where CMC is the differentiator, and keyless
where reproducibility matters. Two access paths, one design.

## What feeds what

| Need | Backtest source (keyless, reproducible) | Live / richer source (CMC Agent Hub) |
|---|---|---|
| Price OHLCV | `data-api.binance.vision` (daily candles) | `mcp__cmc-mcp__get_crypto_quotes_latest`, CMC `v2/cryptocurrency/ohlcv/historical` (Pro key) |
| Fear & Greed | `api.alternative.me/fng` (since 2018) | `mcp__cmc-mcp__get_global_metrics_latest`, CMC `v3/fear-and-greed/{latest,historical}` |
| Altcoin-season / dominance / macro | — | `mcp__cmc-mcp__get_global_metrics_latest` |
| Trend / technicals | computed from OHLCV | `mcp__cmc-mcp__get_crypto_technical_analysis` (SMA/EMA/MACD/RSI) |
| Derivatives (OI, liquidations) | — | `mcp__cmc-mcp__get_global_crypto_derivatives_metrics` |
| Narratives / news | — | `mcp__cmc-mcp__trending_crypto_narratives`, `get_crypto_latest_news` |

The backtest defaults to the keyless sources so **anyone can reproduce results with no
API key or cost**. The CMC MCP path lights up live signal readings and CMC-exclusive
data (altcoin-season index, derivatives positioning, narratives) for the interactive
demo and for richer strategy inputs.

## Connecting the CMC MCP (optional)

Add to your MCP client config (Claude Code `.mcp.json` / `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cmc-mcp": {
      "url": "https://mcp.coinmarketcap.com/mcp",
      "headers": { "X-CMC-MCP-API-KEY": "your-api-key" }
    }
  }
}
```

Get a free Basic key at <https://pro.coinmarketcap.com/signup> (30 calls/min, 10k
credits/month — ample for this Skill). Resolve symbols to numeric CMC IDs once via
`search_cryptos` and cache them; batch multi-coin calls to respect the rate limit.

## Live readout (verified against the CMC API)

`forge/data/cmc.py` + `scripts/market_context.py` pull a live snapshot via the CMC REST
API (the `coinmarketcapapi` client, which also supports `sandbox=True` for keyless
plumbing checks). Every backtest run is annotated with the same live reading:

```bash
python scripts/market_context.py --symbol BNB
# === CoinMarketCap Agent Hub :: BNB market context [LIVE · CMC Pro] ===
#   price: 611.12 · Fear & Greed: 21 (Fear) · BTC dominance: 58.8% · total mcap: $2.19T
```

## Why this wins "Best Use of Agent Hub"

- Uses **multiple access paths** (live CMC REST/MCP + a keyless reproducible path for backtests).
- Keys on CMC's **differentiated** data (Fear & Greed, dominance, market structure), not just price.
- **Real, verified-live integration** — not a README mention.
- Ships as an installable **CMC Agent-Hub Skill** in the official `SKILL.md` format.
