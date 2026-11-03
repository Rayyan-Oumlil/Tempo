"""Run the pre-registered mean reversion test (evidence/mean_reversion_etf.json) once and print the verdict.

Usage: python -m tempo.meanrev_report      (needs data/SPY_ohlc.csv and data/QQQ_ohlc.csv; python -m tempo.data SYMBOL --ohlc)

Rules, fills, variants, slippage sweep and pass criteria come from the JSON file, written before any result existed.
Nothing here is tuned; if the verdict is FAIL, the answer is FAIL.
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass, replace

from tempo.backtest import Costs, Trade, backtest, buy_and_hold, cagr, max_drawdown, sharpe
from tempo.data import Bars, drop_incomplete_today_bars, load_ohlc, ohlc_path
from tempo.meanrev import days_invested, ibs_signals, rsi2_signals, run_longflat, shuffle_bars
from tempo.overnight import MAX_SLIPPAGE_BPS, t_statistic

SLIPPAGE_SWEEP = (0, 1, 3, 5, 10)
BASE_BPS, STRESS_BPS = 1, 3
N_SHUFFLES = 200
POST_2010 = "2010-01-01"
VARIANTS = [("RSI(2) on SPY (primary)", "SPY", "rsi2"), ("IBS on SPY", "SPY", "ibs"), ("RSI(2) on QQQ", "QQQ", "rsi2"), ("IBS on QQQ", "QQQ", "ibs")]


@dataclass(frozen=True)
class Metrics:
    sharpe: float          # net, at BASE_BPS, next-open fills
    bh_sharpe: float
    cagr_by_slip: dict[int, float]
    half1_cagr: float
    half2_cagr: float
    post2010_cagr: float
    post2010_sharpe: float
    t_stat: float
    max_dd: float
    bh_max_dd: float
    beat_pct: float        # against shuffled bars; only computed for the primary
    exposure: float
    round_trips: int
    avg_trip: float
    break_even_bps: float


def verdict(primary: Metrics, variant_cagrs_at_3bps: list[float]) -> list[tuple[str, bool]]:
    """The eight pass criteria of evidence/mean_reversion_etf.json, in order."""
    return [
        ("primary net Sharpe at 1 bp (next-open fills) at or above SPY buy and hold", primary.sharpe >= primary.bh_sharpe),
        ("primary net CAGR above 0 at 3 bps per side", primary.cagr_by_slip[STRESS_BPS] > 0),
        ("primary net CAGR above 0 at 1 bp in both halves", primary.half1_cagr > 0 and primary.half2_cagr > 0),
        ("primary post-2010: net CAGR above 0 and net Sharpe at least 0.4", primary.post2010_cagr > 0 and primary.post2010_sharpe >= 0.4),
        ("t-statistic of the primary's mean daily net return above 3.0", primary.t_stat > 3.0),
        ("primary max drawdown shallower than SPY buy and hold", primary.max_dd > primary.bh_max_dd),
        ("primary beats at least 95% of the shuffled-bar controls on net Sharpe", primary.beat_pct >= 95.0),
        ("at least 3 of the 4 variants have net CAGR above 0 at 3 bps per side", sum(1 for c in variant_cagrs_at_3bps if c > 0) >= 3),
    ]


def round_trip_returns(trades: list[Trade]) -> list[float]:
    """Net return of each completed buy-then-sell, costs included. An open trade at the end is not counted."""
    out, paid = [], None
    for tr in trades:
        if tr.side == "BUY":
            paid = tr.shares * tr.price + tr.cost
        elif paid is not None:
            out.append((tr.shares * tr.price - tr.cost - paid) / paid)
            paid = None
    return out


def signals_for(bars: Bars, rule: str) -> list[int]:
    return rsi2_signals(bars.close) if rule == "rsi2" else ibs_signals(bars.high, bars.low, bars.close)


def daily_returns(values: list[float]) -> list[float]:
    return [b / a - 1 for a, b in zip(values, values[1:])]


def break_even_slippage(bars: Bars, rule: str, costs: Costs, capital: float) -> float:
    sig = signals_for(bars, rule)

    def net(bps: float) -> float:
        return cagr(run_longflat(bars.open, bars.close, sig, replace(costs, slippage_bps=bps), capital).equity)

    if net(0.0) <= 0:
        return 0.0
    if net(MAX_SLIPPAGE_BPS) > 0:
        return MAX_SLIPPAGE_BPS
    lo, hi = 0.0, MAX_SLIPPAGE_BPS
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if net(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def measure(bars: Bars, rule: str, capital: float = 100_000.0, with_shuffles: bool = False) -> tuple[Metrics, dict]:
    base, sig = Costs(), signals_for(bars, rule)
    run = {s: run_longflat(bars.open, bars.close, sig, replace(base, slippage_bps=float(s)), capital) for s in SLIPPAGE_SWEEP}
    net = run[BASE_BPS].equity
    mid, first_2010 = len(net) // 2, next(i for i, d in enumerate(bars.dates) if d >= POST_2010)
    bh = backtest(bars.close, buy_and_hold(bars.close), replace(base, slippage_bps=float(BASE_BPS)), capital)
    trips = round_trip_returns(run[BASE_BPS].trades)
    real = sharpe(net)
    beat = float("nan")
    if with_shuffles:
        rng, fakes = random.Random(1), []
        for _ in range(N_SHUFFLES):
            fake = shuffle_bars(bars, rng)
            fakes.append(sharpe(run_longflat(fake.open, fake.close, signals_for(fake, rule), replace(base, slippage_bps=float(BASE_BPS)), capital).equity))
        beat = 100.0 * sum(1 for f in fakes if real > f) / N_SHUFFLES
        extra_fakes = (sum(fakes) / len(fakes), max(fakes))
    else:
        extra_fakes = None
    m = Metrics(sharpe=real, bh_sharpe=sharpe(bh.equity), cagr_by_slip={s: cagr(r.equity) for s, r in run.items()},
                half1_cagr=cagr(net[:mid]), half2_cagr=cagr(net[mid:]), post2010_cagr=cagr(net[first_2010:]),
                post2010_sharpe=sharpe(net[first_2010:]), t_stat=t_statistic(daily_returns(net)), max_dd=max_drawdown(net),
                bh_max_dd=max_drawdown(bh.equity), beat_pct=beat,
                exposure=days_invested(run[BASE_BPS].trades, len(net)) / len(net), round_trips=len(trips),
                avg_trip=sum(trips) / len(trips) if trips else 0.0, break_even_bps=break_even_slippage(bars, rule, base, capital))
    same = run_longflat(bars.open, bars.close, sig, replace(base, slippage_bps=float(BASE_BPS)), capital, fill="same_close")
    return m, {"run": run, "bh": bh, "same_close_cagr": cagr(same.equity), "same_close_sharpe": sharpe(same.equity),
               "fakes": extra_fakes, "costs": run[BASE_BPS].costs}


def by_year(dates: list[str], equity: list[float]) -> list[tuple[str, float]]:
    out, start = [], 0
    for i in range(1, len(dates) + 1):
        if i == len(dates) or dates[i][:4] != dates[start][:4]:
            out.append((dates[start][:4], equity[i - 1] / equity[max(start - 1, 0)] - 1))
            start = i
    return out


def report() -> tuple[str, bool]:
    series = {s: drop_incomplete_today_bars(load_ohlc(ohlc_path(s))) for s in ("SPY", "QQQ")}
    results = {name: measure(series[sym], rule, with_shuffles=(name == VARIANTS[0][0])) for name, sym, rule in VARIANTS}
    spy = series["SPY"]
    lines = [f"{len(spy.dates)} daily bars, {spy.dates[0]} to {spy.dates[-1]} ({len(spy.dates) / 252:.1f} years); fills at the NEXT OPEN; "
             f"Costs() defaults plus slippage; capital 100,000; variants tried: {len(VARIANTS)}", "",
             f"{'variant':<26}" + "".join(f"{'CAGR@' + str(b) + 'bp':>10}" for b in SLIPPAGE_SWEEP) + f"{'Sharpe@1':>10}{'maxDD':>8}{'invested':>10}{'trips':>7}{'avg/trip':>10}{'break-even':>12}"]
    for name, _, _ in VARIANTS:
        m, _x = results[name]
        lines.append(f"{name:<26}" + "".join(f"{m.cagr_by_slip[b]:>10.1%}" for b in SLIPPAGE_SWEEP)
                     + f"{m.sharpe:>10.2f}{m.max_dd:>8.1%}{m.exposure:>10.1%}{m.round_trips:>7d}{m.avg_trip:>10.2%}{m.break_even_bps:>10.2f}bp")
    primary, px = results[VARIANTS[0][0]]
    lines += ["", f"SPY buy and hold: CAGR {cagr(px['bh'].equity):.1%}, Sharpe {primary.bh_sharpe:.2f}, maxDD {primary.bh_max_dd:.1%}",
              f"primary: 1st half {primary.half1_cagr:.1%}, 2nd half {primary.half2_cagr:.1%}, post-2010 CAGR {primary.post2010_cagr:.1%} "
              f"(Sharpe {primary.post2010_sharpe:.2f}), t = {primary.t_stat:.2f}",
              f"primary shuffled-bar control ({N_SHUFFLES}): real Sharpe {primary.sharpe:.2f}; shuffled mean {px['fakes'][0]:.2f}, best {px['fakes'][1]:.2f}; "
              f"real beats {primary.beat_pct:.0f}%",
              f"REFERENCE ONLY, same-close fills (not achievable): primary CAGR {px['same_close_cagr']:.1%}, Sharpe {px['same_close_sharpe']:.2f}",
              "primary by year at 1 bp (net): " + "  ".join(f"{y} {r:+.1%}" for y, r in by_year(spy.dates, px["run"][BASE_BPS].equity))]
    small = run_longflat(spy.open, spy.close, signals_for(spy, "rsi2"), Costs(slippage_bps=float(BASE_BPS)), 10_000.0)
    lines += [f"primary with 10,000 instead of 100,000 at 1 bp: CAGR {cagr(small.equity):.1%}, costs {small.costs:,.0f}", ""]
    checks = verdict(primary, [results[name][0].cagr_by_slip[STRESS_BPS] for name, _, _ in VARIANTS])
    lines += [f"[{'PASS' if ok else 'FAIL'}] {text}" for text, ok in checks]
    passed = all(ok for _, ok in checks)
    lines += ["", "VERDICT: " + ("PASS (still not proof of an edge: next is a fill-and-slippage log with market-on-open orders on the paper account)"
                                 if passed else "FAIL (report as a failure; no extra variants, no added filters)")]
    return "\n".join(lines), passed


if __name__ == "__main__":
    try:
        print(report()[0])
    except (FileNotFoundError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
