"""Workstream W (docs/plan-quant-v2.md, protocol frozen 2026-11-28, commit 5066e84): VIX term-structure filter on SPY, sector
momentum, gold against real yields. Reuses the X machinery (signal at t, trade at t+1); nothing after 2025-12-31 is loaded."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tempo import history_trend as g
from tempo import history_xc as x
from tempo import history_z as z

SECTORS = ("XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY")
COST = 0.0005
STRESS_MULT = 3
GOLD_LOOKBACK = 63
TOP_SECTORS = 3
START_W1_W3, START_W2 = "2008-01-01", "2001-01-01"
SUBS_W1_W3 = (("2008-01-01", "2013-12-31"), ("2014-01-01", "2019-12-31"), ("2020-01-01", "2025-12-31"))
SUBS_W2 = (("2001-01-01", "2008-12-31"), ("2009-01-01", "2016-12-31"), ("2017-01-01", "2025-12-31"))
Z_LOGGED = ((0.99, 365), (0.71, 365), (0.55, 365), (0.39, 252), (0.87, 252))  # ETH, LTC, BCH, turn-of-month, USMV


def vix_weights(vix: pd.Series, vix3m: pd.Series, index: pd.DatetimeIndex) -> pd.DataFrame:
    """A day with either close missing is not 'VIX below VIX3M', so it is cash."""
    return (vix.reindex(index) < vix3m.reindex(index)).astype(float).to_frame("SPY")


def sector_weights(closes: pd.DataFrame, top: int = TOP_SECTORS) -> pd.DataFrame:
    last_days = pd.Series(closes.index, index=closes.index).groupby([closes.index.year, closes.index.month]).max()
    month_end = closes.loc[pd.DatetimeIndex(last_days)]
    momentum = (month_end.shift(1) / month_end.shift(12) - 1).dropna()
    picks = (momentum.rank(axis=1, ascending=False, method="first") <= top).astype(float) / top
    return picks.reindex(closes.index).ffill().fillna(0.0)


def gold_weights(real_yield: pd.Series, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Bond-market holidays on which GLD trades keep the last published yield."""
    y = real_yield.reindex(real_yield.index.union(index)).ffill().reindex(index)
    return (y < y.shift(GOLD_LOOKBACK)).astype(float).to_frame("GLD")


def trial_sharpes(own_daily: list[float]) -> list[float]:
    return z.prior_daily_sharpes() + [sr / math.sqrt(per) for sr, per in Z_LOGGED] + own_daily


def judge(*, excess: float, bench_excess: list[float], dsr: float, dd: float, bench_dd: float, subs: list[float], stress_excess: float) -> tuple[bool, list[str]]:
    benches = " and ".join(f"{b:.2f}" for b in bench_excess)
    checks = {
        f"Sharpe over cash {excess:.2f} >= benchmarks {benches}": all(excess >= b for b in bench_excess),
        f"Deflated Sharpe prob {dsr:.2f} >= 0.95": dsr >= 0.95,
        f"max drawdown {dd:.0%} shallower than benchmark {bench_dd:.0%}": dd > bench_dd,
        "net CAGR > 0 in every sub-period (" + " / ".join(f"{c:+.1%}" for c in subs) + ")": all(c > 0 for c in subs),
        f"Sharpe over cash {stress_excess:.2f} >= 0.30 at 3x cost": stress_excess >= 0.30,
    }
    return all(checks.values()), [f"{'ok  ' if v else 'FAIL'} {k}" for k, v in checks.items()]


@dataclass(frozen=True)
class Trial:
    name: str
    closes: pd.DataFrame
    weights: pd.DataFrame
    benchmarks: dict[str, pd.DataFrame]  # the first one is the drawdown benchmark
    start: str
    subs: tuple[tuple[str, str], ...]


def _fred(data_dir: Path, name: str) -> pd.Series:  # pragma: no cover - reads the local data
    s = pd.read_csv(data_dir / f"{name}.csv", parse_dates=["observation_date"]).set_index("observation_date")[name]
    s = pd.to_numeric(s, errors="coerce").dropna()
    return s[s.index <= pd.Timestamp(x.LAST_DAY)]


def _trials(data_dir: Path) -> list[Trial]:  # pragma: no cover - reads the local data
    spy = x.load_close(data_dir, "SPY").to_frame("SPY")
    gld = x.load_close(data_dir, "GLD").to_frame("GLD")
    sectors = pd.DataFrame({s: x.load_close(data_dir, s) for s in SECTORS}).dropna()
    vix, vix3m = x.load_close(data_dir, "^VIX"), x.load_close(data_dir, "^VIX3M")
    days = spy.index[spy.index >= pd.Timestamp(START_W1_W3)]
    print(f"missing closes since {START_W1_W3} on SPY days: VIX {int(vix.reindex(days).isna().sum())}, VIX3M {int(vix3m.reindex(days).isna().sum())}")
    spy_on_sectors = spy.reindex(sectors.index)
    if spy_on_sectors["SPY"].isna().any():
        raise ValueError("SPY is missing on sector trading days")
    return [
        Trial("W1 VIX term filter", spy, vix_weights(vix, vix3m, spy.index), {"SPY": spy}, START_W1_W3, SUBS_W1_W3),
        Trial("W2 sector momentum", sectors, sector_weights(sectors), {"9 sectors equal weight": sectors, "SPY": spy_on_sectors}, START_W2, SUBS_W2),
        Trial("W3 gold vs real yields", gld, gold_weights(_fred(data_dir, "DFII10"), gld.index), {"GLD": gld}, START_W1_W3, SUBS_W1_W3),
    ]


def main(data_dir: Path = Path("data/w")) -> int:  # pragma: no cover - reads the local data
    runs = []
    for t in _trials(data_dir):
        cash = x.tbill_daily(data_dir, t.closes.index, 252)
        net, stress = (x.run(t.weights, t.closes, cash, COST * m) for m in (1, STRESS_MULT))
        benches = {k: x.buy_hold(v, cash, COST) for k, v in t.benchmarks.items()}
        runs.append((t, cash, net, stress, benches))
    all_trials = trial_sharpes([x.stats_for(net, t.start, 252).sharpe / math.sqrt(252) for t, _, net, _, _ in runs])
    print(f"WORKSTREAM W verdicts (global N = 20, Deflated Sharpe N = {len(all_trials)}; through {x.LAST_DAY})\n")
    for t, cash, net, stress, benches in runs:
        s = x.stats_for(net, t.start, 252)
        b = {k: x.stats_for(v, t.start, 252) for k, v in benches.items()}
        excess = x.stats_for(net - cash, t.start, 252).sharpe
        bench_excess = {k: x.stats_for(v - cash, t.start, 252).sharpe for k, v in benches.items()}
        ok, lines = judge(
            excess=excess,
            bench_excess=list(bench_excess.values()),
            dsr=g.deflated_sharpe_prob(s.sharpe / math.sqrt(252), s.days, s.skew, s.kurt, all_trials),
            dd=s.max_dd,
            bench_dd=next(iter(b.values())).max_dd,
            subs=x.sub_cagrs(net, t.subs, 252),
            stress_excess=x.stats_for(stress - cash, t.start, 252).sharpe,
        )
        invested = float(t.weights[t.weights.index >= pd.Timestamp(t.start)].sum(axis=1).mean())
        print(f"{t.name} (from {t.start}): Sharpe {s.sharpe:.2f}, over cash {excess:.2f}, CAGR {s.cagr:.1%}, maxDD {s.max_dd:.1%}, invested {invested:.0%}")
        for k, v in b.items():
            print(f"   vs {k}: Sharpe {v.sharpe:.2f}, over cash {bench_excess[k]:.2f}, CAGR {v.cagr:.1%}, maxDD {v.max_dd:.1%}")
        print(f"   {'PASS (candidate for a paper trade)' if ok else 'NO'}")
        for ln in lines:
            print("      " + ln)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/w")))
