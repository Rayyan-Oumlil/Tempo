"""Workstream G (docs/plan-quant-v2.md, protocol frozen 2026-11-17): slow trend and momentum rules on liquid ETFs, judged on history.

Signals use closes up to the month-end signal day i; the trade happens at the close of day i+1 (one-day lag); returns accrue after that.
Nothing after 2025-12-31 is loaded (2026 is the holdout). Cash earns 0.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "EFA", "EEM", "AGG", "TIP", "GLD", "SLV", "DBC", "VNQ")
DATA = Path("data")
LAST_DAY = "2025-12-31"
START = "2008-01-01"
VOL_TARGET = 0.10
ASSET_CAP = 1 / 3
VOL_WINDOW = 60
COST = 0.0005
STRESS_COST = 0.0010
SUBPERIODS = (("2008-01-01", "2012-12-31"), ("2013-01-01", "2018-12-31"), ("2019-01-01", "2025-12-31"))
NAMES = ("G1_sma200", "G2_tsmom_12_1", "G3_dual_top3", "G4_blend")


def load_closes(data_dir: Path = DATA, symbols: tuple[str, ...] = UNIVERSE) -> pd.DataFrame:
    cols = {}
    for s in symbols:
        path = data_dir / f"{s}_1d.csv"
        if not path.exists():
            raise FileNotFoundError(f"missing bars: {path}")
        df = pd.read_csv(path, parse_dates=["date"]).set_index("date")["close"]
        cols[s] = df
    closes = pd.DataFrame(cols).sort_index()
    closes = closes[closes.index <= pd.Timestamp(LAST_DAY)]
    if closes.isna().any().any():
        closes = closes.dropna()
    return closes


def month_end_positions(index: pd.DatetimeIndex) -> list[int]:
    """Position of the last trading day of each calendar month (a partial last month is dropped by the caller via the data end)."""
    ym = index.year * 100 + index.month
    return [i for i in range(len(index) - 1) if ym[i] != ym[i + 1]]


def _vol_size(closes: pd.DataFrame, i: int, held: pd.Series) -> pd.Series:
    rets = closes.iloc[i - VOL_WINDOW : i + 1].pct_change().dropna()
    vol = rets.std() * math.sqrt(252)
    w = (VOL_TARGET / vol).clip(upper=ASSET_CAP) * held
    total = float(w.sum())
    return w / total if total > 1 else w


def weights_at(kind: str, closes: pd.DataFrame, i: int) -> pd.Series:
    """Target weights from data up to and including row i. Not enough history gives all zeros (cash)."""
    zero = pd.Series(0.0, index=closes.columns)
    c = closes.iloc[: i + 1]
    if kind == "G1_sma200":
        if len(c) < 200:
            return zero
        return _vol_size(closes, i, (c.iloc[-1] > c.iloc[-200:].mean()).astype(float))
    if kind == "G2_tsmom_12_1":
        if len(c) < 253:
            return zero
        return _vol_size(closes, i, ((c.iloc[-22] / c.iloc[-253] - 1) > 0).astype(float))
    if kind == "G3_dual_top3":
        if len(c) < 127:
            return zero
        r = c.iloc[-1] / c.iloc[-127] - 1
        top = r[r > 0].nlargest(3)
        w = zero.copy()
        w[top.index] = 1 / 3
        return w
    if kind == "G4_blend":
        return (weights_at("G1_sma200", closes, i) + weights_at("G2_tsmom_12_1", closes, i)) / 2
    if kind == "SPY":
        w = zero.copy()
        w["SPY"] = 1.0
        return w
    if kind == "60_40":
        w = zero.copy()
        w["SPY"], w["AGG"] = 0.6, 0.4
        return w
    raise ValueError(f"unknown rule {kind}")


def backtest(kind: str, closes: pd.DataFrame, cost: float = COST, cash_daily: pd.Series | None = None) -> pd.Series:
    """Daily net return series. Rebalance at the close after each month-end signal; turnover is measured against drifted weights.

    cash_daily (Workstream H): daily return earned by the uninvested fraction; None keeps cash at 0 (Workstream G)."""
    rets = closes.pct_change().fillna(0.0).to_numpy()
    cash = np.zeros(len(closes)) if cash_daily is None else cash_daily.reindex(closes.index).fillna(0.0).to_numpy()
    n = len(closes)
    signals = month_end_positions(closes.index)
    out = np.zeros(n)
    cur = np.zeros(closes.shape[1])
    pending: tuple[int, np.ndarray] | None = None
    sig_at = {i + 1: i for i in signals}
    for t in range(1, n):
        if t in sig_at:
            new = weights_at(kind, closes, sig_at[t]).to_numpy()
            out[t] -= cost * float(np.abs(new - cur).sum())  # traded at the close of day t, after that day's return
            pending = (t, new)
        gain = float(cur @ rets[t]) + (1.0 - float(cur.sum())) * cash[t]
        out[t] += gain
        grown = cur * (1 + rets[t])
        cur = grown / (1 + gain) if (1 + gain) != 0 else grown
        if pending and pending[0] == t:
            cur = pending[1]
            pending = None
    return pd.Series(out, index=closes.index)


@dataclass(frozen=True)
class Stats:
    sharpe: float
    cagr: float
    max_dd: float
    days: int
    skew: float
    kurt: float


def stats(r: pd.Series) -> Stats:
    r = r[r.index >= pd.Timestamp(START)]
    sd = float(r.std())
    sharpe = float(r.mean() / sd * math.sqrt(252)) if sd > 0 else 0.0
    eq = (1 + r).cumprod()
    years = len(r) / 252
    cagr = float(eq.iloc[-1] ** (1 / years) - 1)
    dd = float((eq / eq.cummax() - 1).min())
    return Stats(sharpe, cagr, dd, len(r), float(r.skew()), float(r.kurt()) + 3.0)


def subperiod_cagrs(r: pd.Series) -> list[float]:
    out = []
    for a, b in SUBPERIODS:
        seg = r[(r.index >= pd.Timestamp(a)) & (r.index <= pd.Timestamp(b))]
        eq = (1 + seg).cumprod()
        out.append(float(eq.iloc[-1] ** (252 / len(seg)) - 1))
    return out


def deflated_sharpe_prob(sr_daily: float, t: int, skew: float, kurt: float, trial_srs: list[float]) -> float:
    """Bailey and Lopez de Prado (2014): probability that the true Sharpe exceeds what the best of N unskilled trials would show."""
    n = len(trial_srs)
    if n < 2 or t < 3:
        raise ValueError("need at least 2 trials and 3 observations")
    nd = NormalDist()
    var = float(np.var(trial_srs, ddof=1))
    gamma = 0.5772156649
    sr0 = math.sqrt(var) * ((1 - gamma) * nd.inv_cdf(1 - 1 / n) + gamma * nd.inv_cdf(1 - 1 / (n * math.e)))
    denom = 1 - skew * sr_daily + (kurt - 1) / 4 * sr_daily**2
    if denom <= 0:
        raise ValueError("non-positive variance term")
    return nd.cdf((sr_daily - sr0) * math.sqrt(t - 1) / math.sqrt(denom))


def judge(name: str, r: pd.Series, r_stress: pd.Series, bench: Stats, trial_srs: list[float]) -> tuple[bool, list[str]]:
    s, s2 = stats(r), stats(r_stress)
    dsr = deflated_sharpe_prob(s.sharpe / math.sqrt(252), s.days, s.skew, s.kurt, trial_srs)
    subs = subperiod_cagrs(r)
    checks = {
        "net Sharpe >= 0.60": s.sharpe >= 0.60,
        "net Sharpe >= 60/40 Sharpe": s.sharpe >= bench.sharpe,
        f"Deflated Sharpe prob {dsr:.2f} >= 0.95": dsr >= 0.95,
        "max drawdown no deeper than 60/40": s.max_dd >= bench.max_dd,
        "net CAGR > 0 in every sub-period": all(c > 0 for c in subs),
        "Sharpe >= 0.40 at 10 bps": s2.sharpe >= 0.40,
    }
    return all(checks.values()), [f"{'ok  ' if v else 'FAIL'} {k}" for k, v in checks.items()]


def main() -> int:  # pragma: no cover - reads the local data
    closes = load_closes()
    results = {k: backtest(k, closes) for k in (*NAMES, "SPY", "60_40")}
    stress = {k: backtest(k, closes, STRESS_COST) for k in NAMES}
    bench = stats(results["60_40"])
    trial_srs = [stats(results[k]).sharpe / math.sqrt(252) for k in NAMES]
    print(f"WORKSTREAM G verdicts (protocol rule 7; {START} to {LAST_DAY}; cost {COST * 1e4:.0f} bps a side; cash earns 0)\n")
    print(f"{'rule':16}{'Sharpe':>8}{'CAGR':>8}{'maxDD':>8}   sub-period CAGR")
    for k in (*NAMES, "SPY", "60_40"):
        s = stats(results[k])
        sub = " / ".join(f"{c:+.1%}" for c in subperiod_cagrs(results[k]))
        print(f"{k:16}{s.sharpe:8.2f}{s.cagr:8.1%}{s.max_dd:8.1%}   {sub}")
    print()
    for k in NAMES:
        ok, lines = judge(k, results[k], stress[k], bench, trial_srs)
        print(f"{k}: {'PASS (candidate for a paper trade)' if ok else 'NO'}")
        for ln in lines:
            print("   " + ln)
    print("\nLimits: ETFs that exist today (survivorship), cash earns 0, one 15-year path, N = 4 trials counted. PASS is a candidate, never a promise.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
