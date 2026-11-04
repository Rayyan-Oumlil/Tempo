"""Run the pre-registered overnight drift test (evidence/overnight_drift.json) once and print the verdict.

Usage: python -m tempo.overnight_report      (needs data/SPY_ohlc.csv and data/QQQ_ohlc.csv; python -m tempo.data SYMBOL --ohlc)

Instruments, rule, slippage sweep and pass criteria come from the JSON file, written before any result existed.
Nothing here is tuned; if the verdict is FAIL, the answer is FAIL.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, replace

from tempo.backtest import Costs, backtest, buy_and_hold, cagr, max_drawdown, sharpe
from tempo.data import Bars, drop_incomplete_today_bars, load_ohlc, ohlc_path
from tempo.reporting import by_year, daily_returns
from tempo.overnight import break_even_slippage, run_overnight, t_statistic

SLIPPAGE_SWEEP = (0, 1, 3, 5, 10)
BASE_BPS = 1
STRESS_BPS = 3
CAPITALS = (100_000.0, 10_000.0)
POST_2010 = "2010-01-01"


@dataclass(frozen=True)
class Metrics:
    sharpe: float          # net, at BASE_BPS
    bh_sharpe: float
    cagr_by_slip: dict[int, float]
    half1_cagr: float      # at BASE_BPS
    half2_cagr: float
    post2010_cagr: float
    t_stat: float          # of the mean daily net return at BASE_BPS
    max_dd: float
    bh_max_dd: float
    break_even_bps: float


def verdict(spy: Metrics, qqq: Metrics) -> list[tuple[str, bool]]:
    """The seven pass criteria of evidence/overnight_drift.json, in order."""
    return [
        ("SPY net Sharpe at 1 bp per side at or above SPY buy and hold", spy.sharpe >= spy.bh_sharpe),
        ("SPY net CAGR above 0 at 3 bps per side", spy.cagr_by_slip[STRESS_BPS] > 0),
        ("SPY net CAGR above 0 at 1 bp in both halves of the sample", spy.half1_cagr > 0 and spy.half2_cagr > 0),
        ("SPY net CAGR above 0 at 1 bp in the post-2010 part alone", spy.post2010_cagr > 0),
        ("t-statistic of SPY's mean daily net return above 3.0", spy.t_stat > 3.0),
        ("SPY max drawdown shallower than SPY buy and hold", spy.max_dd > spy.bh_max_dd),
        ("QQQ also passes: positive CAGR at 3 bps, in both halves, and Sharpe at or above buy and hold",
         qqq.cagr_by_slip[STRESS_BPS] > 0 and qqq.half1_cagr > 0 and qqq.half2_cagr > 0 and qqq.sharpe >= qqq.bh_sharpe),
    ]


def measure(bars: Bars, capital: float = 100_000.0) -> tuple[Metrics, dict]:
    base = Costs()
    run = {s: run_overnight(bars.open, bars.close, replace(base, slippage_bps=float(s)), capital) for s in SLIPPAGE_SWEEP}
    net = run[BASE_BPS].equity
    mid = len(net) // 2
    first_2010 = next(i for i, d in enumerate(bars.dates) if d >= POST_2010)
    bh = backtest(bars.close, buy_and_hold(bars.close), replace(base, slippage_bps=float(BASE_BPS)), capital)
    m = Metrics(sharpe=sharpe(net), bh_sharpe=sharpe(bh.equity), cagr_by_slip={s: cagr(r.equity) for s, r in run.items()},
                half1_cagr=cagr(net[:mid]), half2_cagr=cagr(net[mid:]), post2010_cagr=cagr(net[first_2010:]),
                t_stat=t_statistic(daily_returns(net)), max_dd=max_drawdown(net), bh_max_dd=max_drawdown(bh.equity),
                break_even_bps=break_even_slippage(bars.open, bars.close, base, capital))
    night = [bars.open[t] / bars.close[t - 1] - 1 for t in range(1, len(bars.close))]
    day = [bars.close[t] / bars.open[t] - 1 for t in range(len(bars.close))]
    extra = {"run": run, "bh": bh, "mean_night": sum(night) / len(night), "mean_day": sum(day) / len(day),
             "orders": len(run[BASE_BPS].trades), "costs": run[BASE_BPS].costs}
    return m, extra


def report() -> tuple[str, bool]:
    series = {s: drop_incomplete_today_bars(load_ohlc(ohlc_path(s))) for s in ("SPY", "QQQ")}
    results = {s: measure(b) for s, b in series.items()}
    lines = []
    for s, bars in series.items():
        m, x = results[s]
        lines += [f"{s}: {len(bars.dates)} daily bars, {bars.dates[0]} to {bars.dates[-1]} ({len(bars.dates) / 252:.1f} years); "
                  f"Costs() defaults plus slippage; capital 100,000",
                  f"  gross mean daily return: overnight {x['mean_night']:+.4%}  intraday (open to close) {x['mean_day']:+.4%}",
                  f"  {'slippage bps/side':<20}" + "".join(f"{b:>9}" for b in SLIPPAGE_SWEEP),
                  f"  {'net CAGR':<20}" + "".join(f"{m.cagr_by_slip[b]:>9.1%}" for b in SLIPPAGE_SWEEP),
                  f"  at 1 bp: Sharpe {m.sharpe:.2f} (buy and hold {m.bh_sharpe:.2f}), maxDD {m.max_dd:.1%} (buy and hold {m.bh_max_dd:.1%}), "
                  f"1st half {m.half1_cagr:.1%}, 2nd half {m.half2_cagr:.1%}, post-2010 {m.post2010_cagr:.1%}, "
                  f"t = {m.t_stat:.2f}, orders {x['orders']}, costs {x['costs']:,.0f}",
                  f"  break-even slippage: {m.break_even_bps:.2f} bps per side (net CAGR reaches 0)",
                  f"  buy and hold CAGR {cagr(x['bh'].equity):.1%}", ""]
    spy_bars = series["SPY"]
    lines.append("SPY by year at 1 bp (net): " + "  ".join(f"{y} {r:+.1%}" for y, r in by_year(spy_bars.dates, results["SPY"][1]["run"][BASE_BPS].equity)))
    small = run_overnight(spy_bars.open, spy_bars.close, Costs(slippage_bps=float(BASE_BPS)), CAPITALS[1])
    lines += [f"SPY with 10,000 instead of 100,000 at 1 bp: CAGR {cagr(small.equity):.1%}, costs {small.costs:,.0f} "
              f"(the 1.00 minimum commission matters at this size)", ""]
    checks = verdict(results["SPY"][0], results["QQQ"][0])
    lines += [f"[{'PASS' if ok else 'FAIL'}] {text}" for text, ok in checks]
    passed = all(ok for _, ok in checks)
    lines += ["", "VERDICT: " + ("PASS (still not proof of an edge: next is a fill-and-slippage log on the paper account)" if passed
                                 else "FAIL (report as a failure; the break-even slippage above is still the useful number)")]
    return "\n".join(lines), passed


if __name__ == "__main__":
    try:
        print(report()[0])
    except (FileNotFoundError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
