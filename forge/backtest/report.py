"""Serialize a BacktestResult to JSON metrics and render a tearsheet PNG.

The tearsheet is the demo's centerpiece: strategy equity vs buy-and-hold (log
scale), drawdown, and a shaded out-of-sample region, with the headline stats
called out. Kept dependency-light (matplotlib only) and headless (Agg backend).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import matplotlib

if "MPLBACKEND" not in os.environ:  # default headless, but respect an explicit choice
    matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from forge.backtest.engine import BacktestResult  # noqa: E402

_FORGE_INK = "#0b0e14"
_STRAT_COLOR = "#3ddc97"
_BENCH_COLOR = "#8a93a6"
_DD_COLOR = "#ff5d5d"
_OOS_SHADE = "#3ddc97"


def _sanitize_floats(obj: Any) -> Any:
    """Replace non-finite floats (NaN/Inf) with None so json.dumps stays RFC 8259 valid."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _sanitize_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_floats(v) for v in obj]
    return obj


def result_to_dict(result: BacktestResult) -> dict[str, Any]:
    """A fully JSON-serializable summary of a backtest (NaN/Inf coerced to null)."""
    spec = result.spec
    bench = result.benchmark_equity
    base = bench.iloc[0]
    benchmark_total_return = float(bench.iloc[-1] / base - 1.0) if base else float("nan")
    payload = {
        "name": spec.name,
        "symbol": spec.symbol,
        "interval": spec.interval,
        "signal": spec.signal.type,
        "period": [str(result.equity.index.min().date()), str(result.equity.index.max().date())],
        "validation": spec.validation.scheme,
        "oos_start": str(result.oos_start.date()) if result.oos_start is not None else None,
        "stats_full": result.stats_full,
        "stats_oos": result.stats_oos,
        "benchmark_total_return": benchmark_total_return,
        "spec": spec.model_dump(mode="json"),
    }
    return _sanitize_floats(payload)


def _stat_caption(stats: dict[str, Any], label: str) -> str:
    return (f"{label}:  return {stats['total_return'] * 100:+.0f}%   "
            f"Sharpe {stats['sharpe']:.2f}   maxDD {stats['max_drawdown'] * 100:.0f}%   "
            f"trades {stats['n_trades']}")


def render_tearsheet(result: BacktestResult, out_dir: Path | str,
                     basename: str | None = None) -> Path:
    """Render the equity/drawdown tearsheet to ``<out_dir>/<basename>.png``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    basename = basename or result.spec.name
    out_path = out_dir / f"{basename}.png"

    equity = result.equity
    bench = result.benchmark_equity
    drawdown = equity / equity.cummax() - 1.0

    fig, (ax_eq, ax_dd) = plt.subplots(
        2, 1, figsize=(11, 7), height_ratios=[3, 1], sharex=True,
        gridspec_kw={"hspace": 0.08},
    )
    fig.patch.set_facecolor("white")
    try:
        # --- equity panel ---
        ax_eq.plot(bench.index, bench.values, color=_BENCH_COLOR, lw=1.4,
                   label="Buy & Hold", linestyle="--")
        ax_eq.plot(equity.index, equity.values, color=_STRAT_COLOR, lw=2.0,
                   label=f"{result.spec.name}")
        ax_eq.set_yscale("log")
        ax_eq.set_ylabel("Portfolio value (log)")
        ax_eq.legend(loc="upper left", frameon=False)
        ax_eq.grid(True, which="both", alpha=0.15)
        ax_eq.set_title(
            f"Strategy Forge — {result.spec.name} on {result.spec.symbol}",
            color=_FORGE_INK, fontsize=14, fontweight="bold", loc="left",
        )

        if result.oos_start is not None:
            ax_eq.axvspan(result.oos_start, equity.index.max(), color=_OOS_SHADE, alpha=0.07)
            ax_eq.axvline(result.oos_start, color=_STRAT_COLOR, alpha=0.4, lw=1.0, linestyle=":")
            ax_eq.text(result.oos_start, 0.99, "  out-of-sample",
                       transform=ax_eq.get_xaxis_transform(),  # layout-independent y
                       va="top", ha="left", fontsize=8, color="#2b8a6f")

        # --- drawdown panel ---
        ax_dd.fill_between(drawdown.index, drawdown.values * 100, 0,
                           color=_DD_COLOR, alpha=0.35)
        ax_dd.set_ylabel("Drawdown %")
        ax_dd.grid(True, alpha=0.15)

        # --- captions ---
        base = bench.iloc[0]
        bh_ret = (bench.iloc[-1] / base - 1) * 100 if base else float("nan")
        caption = _stat_caption(result.stats_full, "Full")
        if result.stats_oos is not None:
            caption += "\n" + _stat_caption(result.stats_oos, "Out-of-sample")
        caption += f"\nBuy & Hold return {bh_ret:+.0f}%   ·   not financial advice"
        fig.text(0.011, -0.02, caption, fontsize=9, color=_FORGE_INK, family="monospace")

        fig.savefig(out_path, dpi=120, bbox_inches="tight", facecolor="white")
    finally:
        plt.close(fig)
    return out_path


def write_report(result: BacktestResult, out_dir: Path | str,
                 basename: str | None = None) -> dict[str, Path]:
    """Write both ``<basename>.metrics.json`` and ``<basename>.png``; return their paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    basename = basename or result.spec.name

    metrics_path = out_dir / f"{basename}.metrics.json"
    metrics_path.write_text(json.dumps(result_to_dict(result), indent=2))
    tearsheet_path = render_tearsheet(result, out_dir, basename)
    return {"metrics": metrics_path, "tearsheet": tearsheet_path}
