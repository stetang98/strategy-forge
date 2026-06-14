#!/usr/bin/env python3
"""Print a live CoinMarketCap Agent Hub market-context snapshot.

Uses your CMC key (live data) when CMC_API_KEY is set in the environment or .env,
otherwise falls back to the public CMC sandbox so the integration is demonstrable
without a key (sandbox values are mock data).

    python scripts/market_context.py --symbol BNB
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forge import env  # noqa: E402
from forge.data import cmc  # noqa: E402


def _fmt(v, suffix=""):
    return "n/a" if v is None else f"{v}{suffix}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Live CoinMarketCap market context.")
    parser.add_argument("--symbol", default="BNB", help="base asset symbol (e.g. BNB, ETH)")
    args = parser.parse_args(argv)

    env.load_dotenv()
    key = os.environ.get("CMC_API_KEY")
    if key:
        client, mode = cmc.make_client(key, sandbox=False), "LIVE · CMC Pro"
    else:
        client, mode = cmc.make_client(sandbox=True), "SANDBOX (mock) · set CMC_API_KEY for live data"

    ctx = cmc.live_market_context(client, args.symbol)
    print(f"=== CoinMarketCap Agent Hub :: {args.symbol} market context [{mode}] ===")
    print(f"  price:             {_fmt(ctx['price'])}")
    print(f"  24h change:        {_fmt(ctx['percent_change_24h'], '%')}")
    print(f"  Fear & Greed:      {_fmt(ctx['fear_greed'])} ({_fmt(ctx['fear_greed_label'])})")
    print(f"  BTC dominance:     {_fmt(ctx['btc_dominance'])}")
    print(f"  ETH dominance:     {_fmt(ctx['eth_dominance'])}")
    print(f"  total market cap:  {_fmt(ctx['total_market_cap'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
