"""A4 comparison: would a winsorised beta have changed the exec_v2 scores? REPORT ONLY. exec_v2 keeps its plain shrunk beta; the plan says
the decision is logged after 60 more signal days and is never tuned on a result.

Why: one earnings gap or one halt day inside the 60 return days can inflate a stock's beta (a shrunk beta of 3.7 appeared for TTMI). The
alternative clips the stock's daily returns at the 5th and 95th percentile of its own 60 days before the same shrunk regression.

Re-scoring needs no intraday data: a score row stores `ret` (direction x stock move) and `bench_ret` (= beta x direction x SPY move), so the
SPY move is bench_ret / (beta x direction) and the alternative excess is ret - beta_alt x direction x SPY move.
The sector-ETF hedge the plan also names needs a stock-to-sector map that does not exist yet (see the B4 drafts); not compared here.
Read-only; needs Gateway for daily bars.  Usage: python -m tempo.beta_compare
"""
from __future__ import annotations

import sys
from collections import defaultdict
from statistics import fmean

from tempo.data import Bars
from tempo.exec_score import BETA_DAYS, beta_before

CLIP = 0.05
BIG_SHIFT = 0.3


def clip_returns(returns: list[float], clip: float = CLIP) -> list[float]:
    """Winsorise at the `clip` and `1 - clip` empirical quantiles (nearest rank). Empty in, empty out (below about 22 values the clip points are the min and max, so nothing changes)."""
    if not returns:
        return list(returns)
    s = sorted(returns)
    lo, hi = s[int(clip * (len(s) - 1))], s[int(round((1 - clip) * (len(s) - 1)))]
    return [min(max(r, lo), hi) for r in returns]


def winsorised(stock: Bars, bench: Bars, before: str) -> Bars:
    """`stock` with its closes rebuilt from clipped daily returns of the last BETA_DAYS return days before `before` (only those that
    pair with `bench`, exactly the days beta_before regresses), so beta_before on the result is the winsorised beta."""
    s, m = dict(zip(stock.dates, stock.close)), dict(zip(bench.dates, bench.close))
    days = sorted(d for d in s.keys() & m.keys() if d < before)
    window = days[-(BETA_DAYS + 1):]
    rets = [s[b] / s[a] - 1 for a, b in zip(window, window[1:])]
    closes = [100.0]
    for r in clip_returns(rets):
        closes.append(closes[-1] * (1 + r))
    return Bars(window, closes, closes, closes, closes)


def robust_beta_before(stock: Bars, bench: Bars, before: str) -> float | None:
    return beta_before(winsorised(stock, bench, before), bench, before)


def alt_excess(score: dict, beta_alt: float) -> float:
    """Net excess of an exec_v2 score row re-hedged with `beta_alt`. bench_ret = beta x direction x SPY move, so it scales with beta."""
    if score["beta"] == 0:
        raise ValueError(f"{score['signal_id']}: stored beta is 0, the SPY move cannot be recovered")
    return score["ret"] - score["bench_ret"] * beta_alt / score["beta"] - score["round_trip_cost"]


def compare(rows: list[dict]) -> dict[str, dict]:
    """rows: {source, net_excess, alt_net_excess, beta, beta_alt}. Per source: n, mean both ways, mean beta shift, share of big shifts."""
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["source"]].append(r)
    return {s: {"n": len(v), "mean": fmean(r["net_excess"] for r in v), "mean_alt": fmean(r["alt_net_excess"] for r in v),
                "beta_shift": fmean(r["beta_alt"] - r["beta"] for r in v),
                "big_shift": sum(abs(r["beta_alt"] - r["beta"]) > BIG_SHIFT for r in v) / len(v)} for s, v in sorted(by.items())}


def render(summary: dict[str, dict]) -> str:
    lines = [f"{'source':26} {'n':>4} {'mean net':>9} {'mean net (winsorised)':>22} {'beta shift':>10} {'|shift|>0.3':>11}"]
    for s, v in summary.items():
        lines.append(f"{s:26} {v['n']:>4} {v['mean']:>+9.2%} {v['mean_alt']:>+22.2%} {v['beta_shift']:>+10.3f} {v['big_shift']:>11.0%}")
    if not summary:
        lines.append("no exec_v2 scores yet")
    lines.append("report only: exec_v2 keeps the plain shrunk beta; decide after 60 more signal days, never on a result.")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - needs Gateway
    import dataclasses

    from dotenv import load_dotenv

    from tempo.config import load_config
    from tempo.ibkr import connect
    from tempo.ledger import Ledger
    from tempo.ledger_score import ibkr_bars
    from tempo.tradeable import tradeable_scores
    load_dotenv()
    ledger = Ledger()
    scores, _ = tradeable_scores(ledger.signals(), ledger.scores())
    scores = [r for r in scores if r["horizon"] == 5]
    ib = connect(dataclasses.replace(load_config(), client_id=93))
    ib.RequestTimeout = 60
    rows, skipped, cache = [], 0, {}
    try:
        spy = ibkr_bars(ib, "SPY")
        for r in scores:
            if r["symbol"] not in cache:
                cache[r["symbol"]] = ibkr_bars(ib, r["symbol"])
            stock = cache[r["symbol"]]
            beta_alt = robust_beta_before(stock, spy, r["entry_date"]) if stock and spy else None
            if beta_alt is None:
                skipped += 1
                continue
            rows.append({"source": r["source"], "net_excess": r["net_excess"], "alt_net_excess": alt_excess(r, beta_alt),
                         "beta": r["beta"], "beta_alt": beta_alt})
    finally:
        ib.disconnect()
    print(render(compare(rows)))
    print(f"scores re-hedged: {len(rows)}; skipped for missing bars or history: {skipped}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
