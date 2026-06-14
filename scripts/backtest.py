#!/usr/bin/env python3
"""Strategy Forge — black-box backtest runner.

Reads a StrategySpec JSON, fetches keyless market data, runs a look-ahead-safe
backtest, writes ``<name>.metrics.json`` + ``<name>.png`` into the output dir, and
prints a fixed results block. The Skill calls this script; it does not read the
engine source.

    python scripts/backtest.py --spec assets/trend-rider.json --out examples
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running straight from the repo without `pip install`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forge import run  # noqa: E402


def _fmt(stats: dict) -> str:
    def g(k: str, scale: float = 1.0, suffix: str = "", as_pct: bool = False) -> str:
        v = stats.get(k)
        if v is None:
            return "n/a"
        return f"{v * scale:+.1f}{suffix}" if as_pct else f"{v:.2f}"
    return (f"return {g('total_return', 100, '%', as_pct=True)}  "
            f"Sharpe {g('sharpe')}  Sortino {g('sortino')}  "
            f"Calmar {g('calmar')}  maxDD {g('max_drawdown', 100, '%', as_pct=True)}  "
            f"win {g('win_rate', 100, '%', as_pct=True)}  trades {stats.get('n_trades') or 0}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backtest a Strategy Forge strategy spec.")
    parser.add_argument("--spec", required=True, help="path to a StrategySpec JSON file")
    parser.add_argument("--out", default="examples", help="output directory (default: examples)")
    args = parser.parse_args(argv)

    try:
        spec = run.load_spec(args.spec)
    except Exception as exc:  # invalid path or spec
        print(f"error: could not load spec '{args.spec}': {exc}", file=sys.stderr)
        return 2

    try:
        out = run.run_spec(spec, args.out)
    except Exception as exc:  # data fetch or backtest failure
        print(f"error: backtest failed: {exc}", file=sys.stderr)
        return 1

    s = out["summary"]
    print(f"=== Strategy Forge :: {s['name']} on {s['symbol']} "
          f"[{s['period'][0]}..{s['period'][1]}] ===")
    print(f"FULL          {_fmt(s['stats_full'])}")
    if s["stats_oos"] is not None:
        print(f"OUT-OF-SAMPLE {_fmt(s['stats_oos'])}  (from {s['oos_start']})")
    bh = s["benchmark_total_return"]
    print(f"BUY & HOLD    return {bh * 100:+.1f}%" if bh is not None else "BUY & HOLD    n/a")
    print(f"validation: {s['validation']}   |   not financial advice")
    ctx = s.get("cmc_context")
    if ctx:
        print(f"CMC live (Agent Hub): Fear&Greed {ctx.get('fear_greed')} "
              f"({ctx.get('fear_greed_label')}) · BTC dom {ctx.get('btc_dominance')} · "
              f"{s['symbol']} ${ctx.get('price')}")
    print(f"wrote: {out['paths']['metrics']}")
    print(f"wrote: {out['paths']['tearsheet']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
