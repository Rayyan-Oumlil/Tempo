"""Run the pre-registered momentum rotation test (evidence/momentum_rotation.json) once and print the verdict.

Usage: python -m tempo.rotation_report      (needs data/SYMBOL_1d.csv for the whole universe; see tempo.data)

The universe, rule, variants and pass criteria come from the JSON file, which was written before any result existed.
Nothing here is tuned; if the verdict is FAIL, the answer is FAIL.
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

from tempo.backtest import Costs, backtest, buy_and_hold, cagr, max_drawdown, sharpe
from tempo.data import csv_path, load_closes
from tempo.portfolio import PResult, align, run_rotation, same_permutation_shuffle

SPEC = Path(__file__).resolve().parents[1] / "evidence" / "momentum_rotation.json"
VARIANTS = [("12-1 top3 (primary)", 252, 3), ("6-1 top3", 126, 3), ("9-1 top3", 189, 3),
            ("12-1 top2", 252, 2), ("12-1 top4", 252, 4)]
N_SHUFFLES = 200


@dataclass(frozen=True)
class Metrics:
    sharpe: float
    max_dd: float
    half1: float
    half2: float


def metrics_of(equity: list[float]) -> Metrics:
    mid = len(equity) // 2
    return Metrics(sharpe=sharpe(equity), max_dd=max_drawdown(equity), half1=sharpe(equity[:mid]), half2=sharpe(equity[mid:]))


def verdict(primary: Metrics, spy: Metrics, ew: Metrics, beat_pct: float, other_variant_sharpes: list[float]) -> list[tuple[str, bool]]:
    """The five pass criteria of evidence/momentum_rotation.json, in order."""
    beating_ew = 1 + sum(1 for s in other_variant_sharpes if s > ew.sharpe) if primary.sharpe > ew.sharpe else sum(
        1 for s in other_variant_sharpes if s > ew.sharpe)
    return [
        ("Sharpe above SPY buy-and-hold AND above equal-weight-all", primary.sharpe > spy.sharpe and primary.sharpe > ew.sharpe),
        ("max drawdown shallower than SPY buy-and-hold", primary.max_dd > spy.max_dd),
        ("Sharpe above 0 in both halves", primary.half1 > 0 and primary.half2 > 0),
        ("beats at least 95% of the shuffled controls", beat_pct >= 95.0),
        ("at least 4 of 5 variants beat equal-weight-all", beating_ew >= 4),
    ]


def load_universe(symbols: list[str]):
    return align({s: load_closes(csv_path(s)) for s in symbols})


def report() -> tuple[str, bool]:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    dates, closes = load_universe(spec["universe"])
    costs = Costs()
    years = len(dates) / 252
    lines = [f"universe {len(closes)} ETFs, {dates[0]} to {dates[-1]} ({years:.1f} years); costs: Costs() defaults; "
             f"variants tried: {len(VARIANTS)}", ""]

    results: dict[str, PResult] = {name: run_rotation(dates, closes, costs, lookback=lb, top_n=n) for name, lb, n in VARIANTS}
    ew = run_rotation(dates, closes, costs, top_n=len(closes), mode="equal_weight")
    spy = backtest(closes["SPY"], buy_and_hold(closes["SPY"]), costs)

    lines.append(f"{'strategy':<24}{'CAGR':>8}{'Sharpe':>8}{'maxDD':>9}{'1st half':>10}{'2nd half':>10}{'orders':>8}{'costs':>10}")
    rows = [(name, r.equity, len(r.trades), r.costs) for name, r in results.items()]
    rows += [("equal weight all (bench)", ew.equity, len(ew.trades), ew.costs), ("SPY buy and hold (bench)", spy.equity, len(spy.trades), spy.costs)]
    for name, equity, orders, cost in rows:
        m = metrics_of(equity)
        lines.append(f"{name:<24}{cagr(equity):>8.1%}{m.sharpe:>8.2f}{m.max_dd:>9.1%}{m.half1:>10.2f}{m.half2:>10.2f}{orders:>8d}{cost:>10.0f}")

    primary_name, lb, n = VARIANTS[0]
    real = sharpe(results[primary_name].equity)
    rng = random.Random(1)
    fakes = []
    for _ in range(N_SHUFFLES):
        fake = same_permutation_shuffle(closes, rng)
        fakes.append(sharpe(run_rotation(dates, fake, costs, lookback=lb, top_n=n).equity))
    beat = 100.0 * sum(1 for f in fakes if real > f) / N_SHUFFLES
    lines += ["", f"negative control ({N_SHUFFLES} same-permutation shuffles): real Sharpe {real:.2f}; shuffled mean "
              f"{sum(fakes) / N_SHUFFLES:.2f}, best {max(fakes):.2f}; real beats {beat:.0f}%", ""]

    checks = verdict(metrics_of(results[primary_name].equity), metrics_of(spy.equity), metrics_of(ew.equity), beat,
                     [sharpe(results[name].equity) for name, *_ in VARIANTS[1:]])
    lines += [f"[{'PASS' if ok else 'FAIL'}] {text}" for text, ok in checks]
    passed = all(ok for _, ok in checks)
    lines += ["", "VERDICT: " + ("PASS (still not proof of an edge: next is paper trading per evidence/gate.json)" if passed else
                                 "FAIL (report as a failure; no retuning)")]
    return "\n".join(lines), passed


if __name__ == "__main__":
    try:
        text, _ = report()
        print(text)
    except (FileNotFoundError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
