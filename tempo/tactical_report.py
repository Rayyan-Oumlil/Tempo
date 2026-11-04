"""Run the pre-registered tactical asset allocation test (evidence/tactical_allocation.json) once.

Usage: python -m tempo.tactical_report      (needs data/{SPY,EFA,AGG,DBC,VNQ}_1d.csv; python -m tempo.data SYMBOL)

Universe, rule, variants, benchmarks and pass criteria come from the JSON file, written before any result existed.
Implementation detail decided before the first run (see docs/research/log.md): the strategies sit in cash while their
averages warm up, which would handicap them against benchmarks that invest at once, so every strategy and benchmark
is measured over the SAME window, starting at the 12th month end (the longest warm-up among the four variants).
Nothing here is tuned; if the verdict is FAIL, the answer is FAIL.
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass, replace
from pathlib import Path

from tempo.backtest import Costs, backtest, buy_and_hold, cagr, max_drawdown, sharpe
from tempo.data import csv_path, load_closes
from tempo.reporting import by_year, daily_returns
from tempo.overnight import t_statistic
from tempo.pairs_report import drop_incomplete_today
from tempo.portfolio import PResult, align, month_end_indices, run_weighted, same_permutation_shuffle
from tempo.tactical import fixed_weight_fn, trend_weight_fn

SPEC = Path(__file__).resolve().parents[1] / "evidence" / "tactical_allocation.json"
SLIPPAGE_SWEEP = (0, 1, 3, 5, 10)
BASE_BPS = 1
CAPITAL = 100_000.0
N_SHUFFLES = 200
VARIANT_MONTHS = [("M=10 (primary)", 10), ("M=6", 6), ("M=8", 8), ("M=12", 12)]
WARMUP_MONTH_END = 12


@dataclass(frozen=True)
class Metrics:
    sharpe: float
    ew_sharpe: float
    sixty_sharpe: float
    cagr_by_slip: dict[int, float]
    sixty_cagr: float
    max_dd: float
    spy_max_dd: float
    ew_max_dd: float
    half1_sharpe: float
    half2_sharpe: float
    t_stat: float
    beat_pct: float
    variant_sharpes: list[float]  # all four, primary first
    cash_share: float


def verdict(m: Metrics) -> list[tuple[str, bool]]:
    """The eight pass criteria of evidence/tactical_allocation.json, in order."""
    return [
        ("primary net Sharpe at 1 bp at or above BOTH the always-held equal-weight benchmark and the 60/40",
         m.sharpe >= m.ew_sharpe and m.sharpe >= m.sixty_sharpe),
        ("primary max drawdown shallower than BOTH SPY buy and hold and the always-held equal-weight benchmark",
         m.max_dd > m.spy_max_dd and m.max_dd > m.ew_max_dd),
        ("primary net CAGR above the 60/40's net CAGR", m.cagr_by_slip[BASE_BPS] > m.sixty_cagr),
        ("primary net Sharpe above 0 in both halves", m.half1_sharpe > 0 and m.half2_sharpe > 0),
        ("t-statistic of the primary's mean daily net return above 3.0", m.t_stat > 3.0),
        ("primary net CAGR above 0 at 5 bps per side", m.cagr_by_slip[5] > 0),
        ("primary beats at least 95% of the shuffled controls on net Sharpe", m.beat_pct >= 95.0),
        ("at least 3 of the 4 variants have net Sharpe at or above the always-held equal-weight benchmark",
         sum(1 for s in m.variant_sharpes if s >= m.ew_sharpe) >= 3),
    ]


def load_universe(symbols: list[str]):
    return align({s: drop_incomplete_today(*load_closes(csv_path(s))) for s in symbols})


def report() -> tuple[str, bool]:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    symbols = sorted(spec["universe"].values())
    dates, closes = load_universe(symbols)
    weight_each = 1.0 / len(symbols)
    start = month_end_indices(dates)[WARMUP_MONTH_END - 1]
    base = replace(Costs(), slippage_bps=float(BASE_BPS))
    window = dates[start:]

    def tactical(months: int, bps: float, data=closes) -> PResult:
        return run_weighted(dates, data, replace(Costs(), slippage_bps=bps), trend_weight_fn(data, dates, months, weight_each), CAPITAL)

    runs = {name: tactical(m, float(BASE_BPS)) for name, m in VARIANT_MONTHS}
    sweep = {b: tactical(10, float(b)) for b in SLIPPAGE_SWEEP}
    ew = run_weighted(dates, closes, base, fixed_weight_fn({s: weight_each for s in symbols}), CAPITAL)
    sixty = run_weighted(dates, closes, base, fixed_weight_fn({"SPY": 0.6, "AGG": 0.4}), CAPITAL)
    spy = backtest(closes["SPY"], buy_and_hold(closes["SPY"]), base, CAPITAL)
    sl = lambda eq: eq[start:]  # noqa: E731

    rows = [(name, r.equity, len(r.trades), r.costs) for name, r in runs.items()]
    rows += [("equal weight 5, always held", ew.equity, len(ew.trades), ew.costs), ("60/40 SPY/AGG", sixty.equity, len(sixty.trades), sixty.costs),
             ("SPY buy and hold", spy.equity, len(spy.trades), spy.costs)]
    lines = [f"{len(symbols)} assets ({', '.join(symbols)}); window {window[0]} to {window[-1]} ({len(window) / 252:.1f} years), identical for every row; "
             f"Costs() defaults plus {BASE_BPS} bp slippage; variants tried: {len(VARIANT_MONTHS)}", "",
             f"{'strategy':<30}{'CAGR':>8}{'Sharpe':>8}{'maxDD':>9}{'orders':>8}{'costs':>9}"]
    for name, eq, orders, cost in rows:
        lines.append(f"{name:<30}{cagr(sl(eq)):>8.1%}{sharpe(sl(eq)):>8.2f}{max_drawdown(sl(eq)):>9.1%}{orders:>8d}{cost:>9.0f}")
    lines += ["", "primary net CAGR at 0 / 1 / 3 / 5 / 10 bps per side: " + " / ".join(f"{cagr(sl(sweep[b].equity)):.1%}" for b in SLIPPAGE_SWEEP)]

    primary = sl(runs[VARIANT_MONTHS[0][0]].equity)
    mid = len(primary) // 2
    rng = random.Random(1)
    fakes = []
    for _ in range(N_SHUFFLES):
        fake = same_permutation_shuffle(closes, rng)
        fakes.append(sharpe(sl(tactical(10, float(BASE_BPS), fake).equity)))
    real = sharpe(primary)
    beat = 100.0 * sum(1 for f in fakes if real > f) / N_SHUFFLES
    weights = [trend_weight_fn(closes, dates, 10, weight_each)(t) for t in month_end_indices(dates) if t >= start]
    cash_share = sum(1.0 - sum(w.values()) for w in weights) / len(weights)
    lines += [f"negative control ({N_SHUFFLES} same-permutation shuffles): real Sharpe {real:.2f}; shuffled mean {sum(fakes) / N_SHUFFLES:.2f}, best {max(fakes):.2f}; real beats {beat:.0f}%",
              f"average share of equity in cash at month ends: {cash_share:.0%}",
              "by year (primary / 60/40 / SPY): " + "  ".join(
                  f"{y} {a:+.0%}/{b:+.0%}/{c:+.0%}" for (y, a), (_, b), (_, c) in zip(by_year(window, primary), by_year(window, sl(sixty.equity)), by_year(window, sl(spy.equity)))), ""]
    m = Metrics(sharpe=real, ew_sharpe=sharpe(sl(ew.equity)), sixty_sharpe=sharpe(sl(sixty.equity)),
                cagr_by_slip={b: cagr(sl(sweep[b].equity)) for b in SLIPPAGE_SWEEP}, sixty_cagr=cagr(sl(sixty.equity)),
                max_dd=max_drawdown(primary), spy_max_dd=max_drawdown(sl(spy.equity)), ew_max_dd=max_drawdown(sl(ew.equity)),
                half1_sharpe=sharpe(primary[:mid]), half2_sharpe=sharpe(primary[mid:]), t_stat=t_statistic(daily_returns(primary)),
                beat_pct=beat, variant_sharpes=[sharpe(sl(r.equity)) for r in runs.values()], cash_share=cash_share)
    checks = verdict(m)
    lines += [f"t-statistic {m.t_stat:.2f}; Sharpe by half {m.half1_sharpe:.2f} / {m.half2_sharpe:.2f}", ""]
    lines += [f"[{'PASS' if ok else 'FAIL'}] {text}" for text, ok in checks]
    passed = all(ok for _, ok in checks)
    lines += ["", "VERDICT: " + ("PASS (still not proof of an edge: next is a forward test through the signal ledger)" if passed
                                 else "FAIL (report as a failure; no extra assets, no re-weighting, no different averages)")]
    return "\n".join(lines), passed


if __name__ == "__main__":
    try:
        print(report()[0])
    except (FileNotFoundError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
