"""Workstream X (docs/plan-quant-v2.md, protocol frozen 2026-11-23): gold (GLD proxy) and crypto trend rules judged on history.

Signal at the close of day t, trade at the close of day t+1, the new position earns from then on, so the weight applied to
day d's return comes from the signal of day d-2. Nothing after 2025-12-31 is loaded (2026 is the holdout).
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tempo import history_trend as g

LAST_DAY = "2025-12-31"
COST_GLD, COST_CRYPTO = 0.0005, 0.0010
STRESS_MULT = 3
NAMES = ("X1_gld_sma200", "X2_btc_sma100", "X3_btc_eth_mom90")


@dataclass(frozen=True)
class Spec:
    assets: tuple[str, ...]
    start: str
    subperiods: tuple[tuple[str, str], ...]
    periods: int
    cost: float


SPECS = {
    "X1_gld_sma200": Spec(("GLD",), "2008-01-01", (("2008-01-01", "2012-12-31"), ("2013-01-01", "2018-12-31"), ("2019-01-01", "2025-12-31")), 252, COST_GLD),
    "X2_btc_sma100": Spec(("BTC-USD",), "2015-01-01", (("2015-01-01", "2018-12-31"), ("2019-01-01", "2021-12-31"), ("2022-01-01", "2025-12-31")), 365, COST_CRYPTO),
    "X3_btc_eth_mom90": Spec(("BTC-USD", "ETH-USD"), "2018-03-01", (("2018-03-01", "2019-12-31"), ("2020-01-01", "2021-12-31"), ("2022-01-01", "2025-12-31")), 365, COST_CRYPTO),
}


def load_close(data_dir: Path, symbol: str) -> pd.Series:
    s = pd.read_csv(data_dir / f"{symbol.replace('^', '_')}_1d.csv", parse_dates=["date"]).set_index("date")["close"].sort_index()
    return s[s.index <= pd.Timestamp(LAST_DAY)]


def signal(name: str, closes: pd.DataFrame) -> pd.DataFrame:
    """Target weight per asset decided at the close of each row (uses data up to and including that row)."""
    if name == "X1_gld_sma200":
        return (closes > closes.rolling(200).mean()).astype(float)
    if name == "X2_btc_sma100":
        return (closes > closes.rolling(100).mean()).astype(float)
    if name == "X3_btc_eth_mom90":
        return (closes / closes.shift(90) - 1 > 0).astype(float) / 2
    raise ValueError(f"unknown rule {name}")


def run(weights_signal: pd.DataFrame, closes: pd.DataFrame, cash_daily: pd.Series, cost: float) -> pd.Series:
    """Daily net return. weights_signal row t is applied to the return of day t+2 (trade at t+1's close)."""
    rets = closes.pct_change().fillna(0.0)
    pos = weights_signal.shift(2).fillna(0.0)
    gross = (pos * rets).sum(axis=1) + (1.0 - pos.sum(axis=1)) * cash_daily.reindex(closes.index).fillna(0.0)
    turnover = pos.diff().abs().sum(axis=1).fillna(0.0)
    return gross - cost * turnover


def buy_hold(closes: pd.DataFrame, cash_daily: pd.Series, cost: float) -> pd.Series:
    """One asset: held from the first day. Several: equal weight rebalanced at each month start, turnover costed."""
    rets = closes.pct_change().fillna(0.0)
    k = closes.shape[1]
    w = pd.DataFrame(1.0 / k, index=closes.index, columns=closes.columns)
    gross = (w * rets).sum(axis=1)
    month = pd.Series(closes.index.year * 100 + closes.index.month, index=closes.index)
    drift_turnover = pd.Series(0.0, index=closes.index)
    if k > 1:
        cum = (1 + rets).cumprod()
        for _, idx in month.groupby(month):
            seg = cum.loc[idx.index]
            ratio = seg.div(seg.iloc[0])
            held = ratio.div(ratio.sum(axis=1), axis=0)
            drift_turnover.loc[idx.index[-1]] = float((held.iloc[-1] - 1.0 / k).abs().sum())
    return gross - cost * drift_turnover


def tbill_daily(data_dir: Path, index: pd.DatetimeIndex, periods: int) -> pd.Series:
    df = pd.read_csv(data_dir / "DTB3.csv", parse_dates=["observation_date"]).set_index("observation_date")["DTB3"]
    df = pd.to_numeric(df, errors="coerce").dropna()
    df = df[df.index <= pd.Timestamp(LAST_DAY)]
    prev = df.reindex(df.index.union(index)).ffill().shift(1).reindex(index)
    return prev.fillna(0.0) / 100 / periods


def stats_for(r: pd.Series, start: str, periods: int) -> g.Stats:
    r = r[r.index >= pd.Timestamp(start)]
    sd = float(r.std())
    sharpe = float(r.mean() / sd * math.sqrt(periods)) if sd > 0 else 0.0
    eq = (1 + r).cumprod()
    cagr = float(eq.iloc[-1] ** (periods / len(r)) - 1)
    dd = float((eq / eq.cummax() - 1).min())
    return g.Stats(sharpe, cagr, dd, len(r), float(r.skew()), float(r.kurt()) + 3.0)


def sub_cagrs(r: pd.Series, subs: tuple[tuple[str, str], ...], periods: int) -> list[float]:
    out = []
    for a, b in subs:
        seg = r[(r.index >= pd.Timestamp(a)) & (r.index <= pd.Timestamp(b))]
        out.append(float((1 + seg).prod() ** (periods / len(seg)) - 1))
    return out


def evaluate(name: str, data_dir: Path) -> tuple[pd.Series, pd.Series, pd.Series]:
    spec = SPECS[name]
    closes = pd.DataFrame({a: load_close(data_dir, a) for a in spec.assets}).dropna()
    cash = tbill_daily(data_dir, closes.index, spec.periods)
    sig = signal(name, closes)
    net = run(sig, closes, cash, spec.cost)
    stress = run(sig, closes, cash, spec.cost * STRESS_MULT)
    bh = buy_hold(closes, cash, spec.cost)
    return net, stress, bh


def judge(name: str, net: pd.Series, stress: pd.Series, bh: pd.Series, trial_srs: list[float]) -> tuple[bool, list[str]]:
    spec = SPECS[name]
    s, s2, b = (stats_for(x, spec.start, spec.periods) for x in (net, stress, bh))
    dsr = g.deflated_sharpe_prob(s.sharpe / math.sqrt(spec.periods), s.days, s.skew, s.kurt, trial_srs)
    subs = sub_cagrs(net, spec.subperiods, spec.periods)
    checks = {
        "net Sharpe >= 0.60": s.sharpe >= 0.60,
        f"net Sharpe {s.sharpe:.2f} >= buy-and-hold {b.sharpe:.2f}": s.sharpe >= b.sharpe,
        f"Deflated Sharpe prob {dsr:.2f} >= 0.95": dsr >= 0.95,
        f"max drawdown {s.max_dd:.0%} within 75% of buy-and-hold's {b.max_dd:.0%}": abs(s.max_dd) <= 0.75 * abs(b.max_dd),
        "net CAGR > 0 in every sub-period": all(c > 0 for c in subs),
        "Sharpe >= 0.40 at 3x cost": s2.sharpe >= 0.40,
    }
    return all(checks.values()), [f"{'ok  ' if v else 'FAIL'} {k}" for k, v in checks.items()]


def main(data_dir: Path = g.DATA) -> int:  # pragma: no cover - reads the local data
    runs = {n: evaluate(n, data_dir) for n in NAMES}
    trial_srs = [stats_for(runs[n][0], SPECS[n].start, SPECS[n].periods).sharpe / math.sqrt(SPECS[n].periods) for n in NAMES]
    print(f"WORKSTREAM X verdicts (protocol rule 6; N = {len(NAMES)}; through {LAST_DAY})\n")
    print(f"{'rule':20}{'Sharpe':>8}{'CAGR':>8}{'maxDD':>8}   sub-period CAGR   | buy-and-hold Sharpe / CAGR / maxDD")
    for n in NAMES:
        spec = SPECS[n]
        net, _, bh = runs[n]
        s, b = stats_for(net, spec.start, spec.periods), stats_for(bh, spec.start, spec.periods)
        sub = " / ".join(f"{c:+.1%}" for c in sub_cagrs(net, spec.subperiods, spec.periods))
        print(f"{n:20}{s.sharpe:8.2f}{s.cagr:8.1%}{s.max_dd:8.1%}   {sub:18}| {b.sharpe:.2f} / {b.cagr:.1%} / {b.max_dd:.1%}")
    print()
    for n in NAMES:
        ok, lines = judge(n, *runs[n], trial_srs)
        print(f"{n}: {'PASS (candidate for a paper trade)' if ok else 'NO'}")
        for ln in lines:
            print("   " + ln)
    print("\nLimits: GLD is not spot XAUUSD; BTC and ETH are hindsight survivors on one 11-year path; daily bars; costs are assumptions. PASS is a candidate, never a promise.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else g.DATA))
