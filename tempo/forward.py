"""Forward test of the frozen mean reversion rules (evidence/forward_test.json).

Usage: python -m tempo.data SPY --ohlc ; python -m tempo.data QQQ --ohlc ; python -m tempo.forward

The four variants of evidence/mean_reversion_etf.json are judged only on bars from the freeze date on, so nothing
here can have been tuned to them. No verdict is printed until 60 pooled round trips exist or the deadline passes.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from datetime import date

from tempo.backtest import Costs, Trade, backtest, buy_and_hold, cagr, sharpe
from tempo.data import Bars, drop_incomplete_today_bars, load_ohlc, ohlc_path
from tempo.meanrev import run_longflat
from tempo.meanrev_report import round_trip_returns, signals_for
from tempo.overnight import t_statistic

FREEZE_DATE = "2026-11-03"
DEADLINE = date(2028, 11, 3)
MIN_POOLED_TRIPS = 60
SLIPPAGE_BPS = 3.0
CAPITAL = 100_000.0
MIN_TRIP_RETURN = 0.001
MIN_T = 2.0
MAX_VARIANT_SHARE = 0.6
VARIANTS = [("SPY ibs", "SPY", "ibs"), ("QQQ ibs", "QQQ", "ibs"), ("SPY rsi2", "SPY", "rsi2"), ("QQQ rsi2", "QQQ", "rsi2")]


@dataclass(frozen=True)
class Forward:
    trips: list[float]
    equity: list[float]
    trades: list[Trade]


def mask_initial_run(signals: list[int]) -> list[int]:
    """A signal already 1 at the start is ignored until it has gone back to 0 (only fresh entries count)."""
    out, i = list(signals), 0
    while i < len(out) and out[i] == 1:
        out[i] = 0
        i += 1
    return out


def forward_round_trips(bars: Bars, rule: str, start_date: str, costs: Costs, capital: float) -> Forward:
    """Signals use the whole history (the rules need warm-up), trades only from `start_date`, starting flat."""
    start = next((i for i, d in enumerate(bars.dates) if d >= start_date), None)
    if start is None:
        return Forward([], [], [])
    sig = mask_initial_run(signals_for(bars, rule)[start:])
    result = run_longflat(bars.open[start:], bars.close[start:], sig, costs, capital)
    return Forward(trips=round_trip_returns(result.trades), equity=result.equity, trades=result.trades)


def pooled_stats(trips_by_variant: dict[str, list[float]]) -> tuple[int, float, float | None]:
    pooled = [r for trips in trips_by_variant.values() for r in trips]
    if not pooled:
        return 0, 0.0, None
    return len(pooled), sum(pooled) / len(pooled), t_statistic(pooled) if len(pooled) >= 2 else None


def ready_to_judge(pooled_trips: int, today: date) -> bool:
    return pooled_trips >= MIN_POOLED_TRIPS or today >= DEADLINE


def verdict(trips_by_variant: dict[str, list[float]]) -> list[tuple[str, bool]]:
    """The three criteria of evidence/forward_test.json. Only call this once `ready_to_judge` is true."""
    n, mean, t = pooled_stats(trips_by_variant)
    sums = [sum(v) for v in trips_by_variant.values()]
    total = sum(sums)
    top_share = max(sums) / total if total > 0 else 1.0
    return [
        (f"pooled average net return per round trip above {MIN_TRIP_RETURN:.2%}", n > 0 and mean > MIN_TRIP_RETURN),
        (f"t-statistic of the pooled per-trip returns above {MIN_T}", t is not None and t > MIN_T),
        (f"no single variant above {MAX_VARIANT_SHARE:.0%} of the total profit", top_share <= MAX_VARIANT_SHARE),
    ]


def report(today: date | None = None) -> str:
    today = today or date.today()
    costs = replace(Costs(), slippage_bps=SLIPPAGE_BPS)
    series = {s: drop_incomplete_today_bars(load_ohlc(ohlc_path(s)), today) for s in ("SPY", "QQQ")}
    trips, lines = {}, [f"forward test from {FREEZE_DATE}; data through {series['SPY'].dates[-1]}; {SLIPPAGE_BPS:g} bps slippage per side; flat at the start"]
    for name, sym, rule in VARIANTS:
        bars = series[sym]
        f = forward_round_trips(bars, rule, FREEZE_DATE, costs, CAPITAL)
        trips[name] = f.trips
        win = f"{sum(1 for r in f.trips if r > 0) / len(f.trips):.0%}" if f.trips else "n/a"
        avg = f"{sum(f.trips) / len(f.trips):+.2%}" if f.trips else "n/a"
        window = f"{len(f.equity)} days"
        extra = ""
        if len(f.equity) >= 20:
            start = next(i for i, d in enumerate(bars.dates) if d >= FREEZE_DATE)
            bh = backtest(bars.close[start:], buy_and_hold(bars.close[start:]), costs, CAPITAL)
            extra = f"; strategy CAGR {cagr(f.equity):.1%}, Sharpe {sharpe(f.equity):.2f} vs buy and hold {cagr(bh.equity):.1%}, {sharpe(bh.equity):.2f}"
        lines.append(f"  {name:<9} {len(f.trips):>3} round trips, avg net {avg}, win rate {win}, window {window}{extra}")
    n, mean, t = pooled_stats(trips)
    lines.append(f"pooled: {n} round trips, average net {mean:+.2%}" + (f", t = {t:.2f}" if t is not None else ""))
    if not ready_to_judge(n, today):
        lines += ["", f"NOT ENOUGH TRIPS: {n} of {MIN_POOLED_TRIPS} (deadline {DEADLINE}). No verdict, and nothing should be concluded from these numbers."]
        return "\n".join(lines)
    checks = verdict(trips)
    lines += [""] + [f"[{'PASS' if ok else 'FAIL'}] {text}" for text, ok in checks]
    passed = all(ok for _, ok in checks)
    lines += ["", "VERDICT: " + ("PASS (new evidence, not real money: next is the gate in evidence/gate.json)" if passed else "FAIL (close the mean reversion family)")]
    return "\n".join(lines)


if __name__ == "__main__":
    try:
        print(report())
    except (FileNotFoundError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
