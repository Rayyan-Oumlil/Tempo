"""Run the baselines and the pre-registered example strategy on saved daily data and print an honest report.

Usage: python -m tempo.evidence SYMBOL [SMA_WINDOW]      (needs data/SYMBOL_1d.csv; see tempo.data)

Strategies compared: stay flat, buy and hold, and one trend rule (hold above the SMA). Only ONE variant is
tried (the window is fixed up front, default 200), so the variants-tried count for the gate is 1. Trying more
windows and keeping the best is exactly how backtests lie; if you try more, record the count in the research log.
"""
from __future__ import annotations

import sys

from tempo.backtest import Costs, backtest, buy_and_hold, flat, negative_control, sma_trend, summarize
from tempo.data import csv_path, load_closes


def report(symbol: str, window: int, n_shuffles: int = 200) -> str:
    dates, closes = load_closes(csv_path(symbol))
    costs = Costs()
    strategies = {"flat": flat, "buy and hold": buy_and_hold, f"SMA {window} trend": sma_trend(window)}
    lines = [f"{symbol}: {len(closes)} daily bars, {dates[0]} to {dates[-1]} ({len(closes) / 252:.1f} years)",
             f"costs: {costs.per_share} USD/share (min {costs.min_per_order}), sell fee {costs.sell_fee_per_million}/M, "
             f"slippage {costs.slippage_bps} bps; signal at close t, fill at close t+1", "",
             f"{'strategy':<18}{'total':>9}{'CAGR':>8}{'Sharpe':>8}{'maxDD':>9}{'orders':>8}{'costs':>10}"]
    for name, strat in strategies.items():
        s = summarize(backtest(closes, strat(closes), costs))
        lines.append(f"{name:<18}{s['total_return']:>9.1%}{s['cagr']:>8.1%}{s['sharpe']:>8.2f}"
                     f"{s['max_drawdown']:>9.1%}{s['orders']:>8d}{s['costs']:>10.2f}")
    c = negative_control(closes, sma_trend(window), costs, n=n_shuffles)
    lines += ["", f"negative control ({c['n']} shuffled-order versions of the same returns), SMA {window}:",
              f"  real Sharpe {c['real_sharpe']:.2f}; shuffled mean {c['shuffled_mean']:.2f}, best {c['shuffled_max']:.2f}; "
              f"real beats {c['beat_pct']:.0f}% of shuffles",
              "  (a high number says the rule likes the real ordering, not that it has an edge; the gate asks for 95+)",
              "", "variants tried: 1"]
    return "\n".join(lines)


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise ValueError("usage: python -m tempo.evidence SYMBOL [SMA_WINDOW]")
        print(report(sys.argv[1].upper(), int(sys.argv[2]) if len(sys.argv) > 2 else 200))
    except (FileNotFoundError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
