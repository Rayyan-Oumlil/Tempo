"""Workstream H (docs/plan-quant-v2.md, protocol frozen 2026-11-23): G5 cash-yield trend blend and G6 put-write index.

G5 is the G4 blend with the uninvested fraction earning the previous day's 3-month T-bill rate (FRED DTB3).
G6 is buy and hold of the CBOE PutWrite index (^PUT) less a fixed yearly drag. Nothing after 2025-12-31 is loaded.
Reuses the Workstream G engine; the judging rule is G rule 7 with N = 6 trials.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

from tempo import history_trend as g

TBILL_FILE = "DTB3.csv"
PUT_FILE = "_PUT_1d.csv"
PUT_DRAG = 0.005
PUT_DRAG_STRESS = 0.010
HNAMES = ("G5_blend_cash", "G6_putwrite")


def load_tbill_daily(data_dir: Path, index: pd.DatetimeIndex) -> pd.Series:
    """Daily cash return on each date of `index`: the previous available DTB3 value / 100 / 252 (no look-ahead)."""
    df = pd.read_csv(data_dir / TBILL_FILE, parse_dates=["observation_date"]).set_index("observation_date")["DTB3"]
    df = pd.to_numeric(df, errors="coerce").dropna()
    df = df[df.index <= pd.Timestamp(g.LAST_DAY)]
    prev = df.reindex(df.index.union(index)).ffill().shift(1).reindex(index)
    return (prev.fillna(0.0) / 100 / 252).rename("cash")


def put_returns(data_dir: Path, drag: float = PUT_DRAG) -> pd.Series:
    s = pd.read_csv(data_dir / PUT_FILE, parse_dates=["date"]).set_index("date")["close"].sort_index()
    s = s[s.index <= pd.Timestamp(g.LAST_DAY)]
    return (s.pct_change().fillna(0.0) - drag / 252).rename("G6_putwrite")


def run_all(data_dir: Path) -> tuple[dict[str, pd.Series], dict[str, pd.Series]]:
    closes = g.load_closes(data_dir)
    cash = load_tbill_daily(data_dir, closes.index)
    res = {k: g.backtest(k, closes) for k in (*g.NAMES, "SPY", "60_40")}
    stress = {k: g.backtest(k, closes, g.STRESS_COST) for k in g.NAMES}
    res["G5_blend_cash"] = g.backtest("G4_blend", closes, cash_daily=cash)
    stress["G5_blend_cash"] = g.backtest("G4_blend", closes, g.STRESS_COST, cash_daily=cash)
    res["G6_putwrite"] = put_returns(data_dir).reindex(closes.index).fillna(0.0)
    stress["G6_putwrite"] = put_returns(data_dir, PUT_DRAG_STRESS).reindex(closes.index).fillna(0.0)
    res["_cash"] = cash
    return res, stress


def main(data_dir: Path = g.DATA) -> int:  # pragma: no cover - reads the local data
    res, stress = run_all(data_dir)
    cash = res.pop("_cash")
    bench = g.stats(res["60_40"])
    counted = (*g.NAMES, *HNAMES)
    trial_srs = [g.stats(res[k]).sharpe / math.sqrt(252) for k in counted]
    print(f"WORKSTREAM H verdicts (protocol rule 4; N = {len(counted)}; {g.START} to {g.LAST_DAY})\n")
    print(f"{'rule':16}{'Sharpe':>8}{'CAGR':>8}{'maxDD':>8}{'xs Sharpe':>11}   sub-period CAGR")
    for k in (*counted, "SPY", "60_40"):
        s = g.stats(res[k])
        ex = res[k] - cash
        xs = float(ex[ex.index >= pd.Timestamp(g.START)].mean() / ex[ex.index >= pd.Timestamp(g.START)].std() * math.sqrt(252))
        sub = " / ".join(f"{c:+.1%}" for c in g.subperiod_cagrs(res[k]))
        print(f"{k:16}{s.sharpe:8.2f}{s.cagr:8.1%}{s.max_dd:8.1%}{xs:11.2f}   {sub}")
    print()
    for k in HNAMES:
        ok, lines = g.judge(k, res[k], stress[k], bench, trial_srs)
        print(f"{k}: {'PASS (candidate for a paper trade)' if ok else 'NO'}")
        for ln in lines:
            print("   " + ln)
    print("\nLimits: ETFs that exist today, one 18-year path, ^PUT is an index (not tradable as is), T-bill yield before any broker spread, Yahoo adjusted closes not IBKR bars. PASS is a candidate, never a promise.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else g.DATA))
