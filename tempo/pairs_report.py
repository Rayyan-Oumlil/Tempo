"""Run the pre-registered pairs test (evidence/pairs_trading.json) once and print the verdict.

Usage: python -m tempo.pairs_report      (needs data/SYMBOL_1d.csv for every leg and SPY; see tempo.data)

Pairs, rule, variants and pass criteria come from the JSON file, written before any result existed.
Nothing here is tuned; if the verdict is FAIL, the answer is FAIL.
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tempo.backtest import Costs, max_drawdown, sharpe
from tempo.data import csv_path, load_closes
from tempo.pairs import PairParams, pair_signals, run_pair
from tempo.reporting import daily_returns
from tempo.portfolio import align, same_permutation_shuffle

SPEC = Path(__file__).resolve().parents[1] / "evidence" / "pairs_trading.json"
MIN_DAYS = 15 * 252
CAPITAL = 100_000.0
BORROW, BORROW_STRESS = 0.003, 0.015
N_SHUFFLES = 200
VARIANTS = [("W=60 E=2.0 (primary)", PairParams(60, 2.0)), ("W=40 E=2.0", PairParams(40, 2.0)), ("W=90 E=2.0", PairParams(90, 2.0)),
            ("W=60 E=1.5", PairParams(60, 1.5)), ("W=60 E=2.5", PairParams(60, 2.5))]


@dataclass(frozen=True)
class Metrics:
    sharpe: float
    stress_sharpe: float
    beat_pct: float
    half1: float
    half2: float
    variant_sharpes: list[float]  # all five, primary first
    spy_corr: float
    pair_win_share: float
    max_dd: float


def verdict(m: Metrics) -> list[tuple[str, bool]]:
    """The eight pass criteria of evidence/pairs_trading.json, in order."""
    return [
        ("primary net Sharpe >= 0.5 at 0.3% borrow", m.sharpe >= 0.5),
        ("primary net Sharpe > 0.3 at 1.5% borrow", m.stress_sharpe > 0.3),
        ("beats at least 95% of the shuffled controls", m.beat_pct >= 95.0),
        ("Sharpe above 0 in both halves", m.half1 > 0 and m.half2 > 0),
        ("at least 4 of 5 variants have Sharpe above 0", sum(1 for s in m.variant_sharpes if s > 0) >= 4),
        ("absolute correlation with SPY below 0.3", abs(m.spy_corr) < 0.3),
        ("at least 60% of pairs have positive net P&L", m.pair_win_share >= 0.6),
        ("max drawdown shallower than 20%", m.max_dd > -0.20),
    ]


def drop_incomplete_today(dates: list[str], closes: list[float], today: date | None = None):
    """The newest daily bar of a day still in progress is not a close: drop it."""
    today_s = (today or date.today()).isoformat()
    if dates and dates[-1] >= today_s:
        return dates[:-1], closes[:-1]
    return dates, closes


def usable_pairs(pairs, series):
    """A pair is dropped only if a leg has fewer than 15 years of data (the registered rule); returns the reasons."""
    kept, dropped = [], []
    for a, b in pairs:
        short = next(((s, len(series[s][0])) for s in (a, b) if len(series[s][0]) < MIN_DAYS), None)
        if short:
            dropped.append(((a, b), f"{short[0]} has {short[1]} days, under the {MIN_DAYS} needed"))
        else:
            kept.append((a, b))
    return kept, dropped


def run_portfolio(closes, pairs, params: PairParams, costs: Costs, borrow: float):
    """Equal capital per pair; returns (summed equity, per-pair results)."""
    results = [run_pair(closes[a], closes[b], pair_signals(closes[a], closes[b], params), costs, CAPITAL / len(pairs), borrow)
               for a, b in pairs]
    return [sum(vals) for vals in zip(*(r.equity for r in results))], results


def correlation(x: list[float], y: list[float]) -> float:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    vx, vy = sum((a - mx) ** 2 for a in x), sum((b - my) ** 2 for b in y)
    return 0.0 if vx == 0 or vy == 0 else cov / (vx * vy) ** 0.5


def report() -> tuple[str, bool]:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    symbols = sorted({s for pair in spec["candidate_pairs"] for s in pair} | {"SPY"})
    series = {s: drop_incomplete_today(*load_closes(csv_path(s))) for s in symbols}
    pairs, dropped = usable_pairs(spec["candidate_pairs"], series)
    lines = [f"pairs kept {len(pairs)}: " + ", ".join(f"{a}/{b}" for a, b in pairs)]
    lines += [f"pair dropped {a}/{b}: {why}" for (a, b), why in dropped]
    if len(pairs) < 6:
        return "\n".join(lines + ["", "INCONCLUSIVE: fewer than 6 usable pairs (registered rule); not a pass or a fail"]), False
    legs = {s for p in pairs for s in p} | {"SPY"}
    dates, closes = align({s: series[s] for s in legs})
    costs = Costs()
    lines += [f"{len(dates)} common days, {dates[0]} to {dates[-1]} ({len(dates) / 252:.1f} years); capital {CAPITAL:,.0f} split equally; "
              f"borrow {BORROW:.1%} a year (stress {BORROW_STRESS:.1%}); costs: Costs() defaults", "",
              f"{'variant':<22}{'Sharpe':>8}{'maxDD':>9}{'1st half':>10}{'2nd half':>10}{'orders':>8}{'costs':>9}{'borrow':>9}"]
    variant_sharpes, primary = [], None
    for name, params in VARIANTS:
        equity, results = run_portfolio(closes, pairs, params, costs, BORROW)
        mid = len(equity) // 2
        s = sharpe(equity)
        variant_sharpes.append(s)
        if primary is None:
            primary = (equity, results)
        lines.append(f"{name:<22}{s:>8.2f}{max_drawdown(equity):>9.1%}{sharpe(equity[:mid]):>10.2f}{sharpe(equity[mid:]):>10.2f}"
                     f"{sum(len(r.trades) for r in results):>8d}{sum(r.costs for r in results):>9.0f}{sum(r.borrow for r in results):>9.0f}")
    equity, results = primary
    mid = len(equity) // 2
    stress = sharpe(run_portfolio(closes, pairs, VARIANTS[0][1], costs, BORROW_STRESS)[0])
    lines += ["", "primary, per pair (net P&L on its own capital, orders):"]
    for (a, b), r in zip(pairs, results):
        lines.append(f"  {a}/{b:<5} {r.equity[-1] - CAPITAL / len(pairs):>10,.0f}  {len(r.trades):>4d} orders")
    win_share = sum(1 for r in results if r.equity[-1] > CAPITAL / len(pairs)) / len(pairs)

    rng = random.Random(1)
    fakes = []
    pair_closes = {s: closes[s] for s in legs - {"SPY"}}
    for _ in range(N_SHUFFLES):
        fake = same_permutation_shuffle(pair_closes, rng)
        fakes.append(sharpe(run_portfolio(fake, pairs, VARIANTS[0][1], costs, BORROW)[0]))
    real = sharpe(equity)
    beat = 100.0 * sum(1 for f in fakes if real > f) / N_SHUFFLES
    lines += ["", f"negative control ({N_SHUFFLES} same-permutation shuffles): real Sharpe {real:.2f}; shuffled mean "
              f"{sum(fakes) / N_SHUFFLES:.2f}, best {max(fakes):.2f}; real beats {beat:.0f}%",
              f"Sharpe at 1.5% borrow: {stress:.2f}"]
    corr = correlation(daily_returns(equity), daily_returns(closes["SPY"]))
    m = Metrics(sharpe=real, stress_sharpe=stress, beat_pct=beat, half1=sharpe(equity[:mid]), half2=sharpe(equity[mid:]),
                variant_sharpes=variant_sharpes, spy_corr=corr, pair_win_share=win_share, max_dd=max_drawdown(equity))
    lines += [f"correlation of daily returns with SPY: {corr:.2f}; pairs with positive P&L: {win_share:.0%}", ""]
    checks = verdict(m)
    lines += [f"[{'PASS' if ok else 'FAIL'}] {text}" for text, ok in checks]
    passed = all(ok for _, ok in checks)
    lines += ["", "VERDICT: " + ("PASS (still not proof of an edge: next is shadow mode and paper trading per evidence/gate.json)"
                                 if passed else "FAIL (report as a failure; no retuning, no dropping pairs)")]
    return "\n".join(lines), passed


if __name__ == "__main__":
    try:
        print(report()[0])
    except (FileNotFoundError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
