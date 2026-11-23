"""Workstream Y (docs/plan-quant-v2.md, protocol frozen 2026-11-23): X4 vol-targeted BTC trend, X5 robustness grid, Y1 cross-asset trend.

Same timing as Workstreams G and X: signal at the close of day t, trade at the close of t+1, the weight applied to day d's
return comes from the signal of day d-2 (daily rules) or the month-end close (Y1). Nothing after 2025-12-31 is loaded.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from tempo import history_cash as hc
from tempo import history_trend as g
from tempo import history_xc as x

X4_TARGET_VOL, X4_VOL_WINDOW, X4_BAND, X4_SMA = 0.40, 30, 0.10, 100
Y_UNIVERSE = ("SPY", "IWM", "EFA", "EEM", "TLT", "IEF", "TIP", "GLD", "SLV", "DBC", "USO", "UNG", "DBA", "UUP", "BTC-USD", "ETH-USD")
CRYPTO = ("BTC-USD", "ETH-USD")
Y_START = "2008-01-01"
Y_SUBS = (("2008-01-01", "2012-12-31"), ("2013-01-01", "2018-12-31"), ("2019-01-01", "2025-12-31"))
Y_TARGET_VOL, Y_VOL_WINDOW, Y_MIN_HISTORY = 0.10, 60, 253
Y_COST_ETF, Y_COST_CRYPTO = 0.0005, 0.0010
X4_SUBS = (("2015-01-01", "2018-12-31"), ("2019-01-01", "2021-12-31"), ("2022-01-01", "2025-12-31"))
N_DSR = 11


def x4_weights(close: pd.Series) -> pd.DataFrame:
    """Decided weight per day: the X2 signal sized to a vol target, changed only on a flip or a move beyond the band."""
    sig = (close > close.rolling(X4_SMA).mean()).to_numpy()
    vol = (close.pct_change().rolling(X4_VOL_WINDOW).std() * math.sqrt(365)).to_numpy()
    out = np.zeros(len(close))
    cur, prev_sig = 0.0, False
    for i in range(len(close)):
        if not np.isnan(vol[i]):
            target = min(1.0, X4_TARGET_VOL / vol[i]) if sig[i] else 0.0
            if bool(sig[i]) != prev_sig or abs(target - cur) > X4_BAND:
                cur = target
            prev_sig = bool(sig[i])
        out[i] = cur
    return pd.DataFrame({close.name or "A": out}, index=close.index)


def x4_run(data_dir: Path, cost: float) -> tuple[pd.Series, pd.Series]:
    close = x.load_close(data_dir, "BTC-USD").rename("BTC-USD")
    closes = close.to_frame()
    cash = x.tbill_daily(data_dir, closes.index, 365)
    return x.run(x4_weights(close), closes, cash, cost), x.buy_hold(closes, cash, x.COST_CRYPTO)


def sma_signal(closes: pd.DataFrame, n: int) -> pd.DataFrame:
    return (closes > closes.rolling(n).mean()).astype(float)


def mom_signal(closes: pd.DataFrame, n: int) -> pd.DataFrame:
    return (closes / closes.shift(n) - 1 > 0).astype(float) / closes.shape[1]


def x5_grid(data_dir: Path) -> list[tuple[str, int, float, float]]:
    rows = []
    for name, lengths, fn in (("X2_btc_sma", (50, 100, 150, 200), sma_signal), ("X3_btc_eth_mom", (30, 60, 90, 120), mom_signal)):
        key = "X2_btc_sma100" if name.startswith("X2") else "X3_btc_eth_mom90"
        spec = x.SPECS[key]
        closes = pd.DataFrame({a: x.load_close(data_dir, a) for a in spec.assets}).dropna()
        cash = x.tbill_daily(data_dir, closes.index, 365)
        bh = x.stats_for(x.buy_hold(closes, cash, spec.cost), spec.start, 365).sharpe
        for n in lengths:
            r = x.run(fn(closes, n), closes, cash, spec.cost)
            rows.append((name, n, x.stats_for(r, spec.start, 365).sharpe, bh))
    return rows


# ---- Y1 -------------------------------------------------------------------------------------------------------------


def load_panel(data_dir: Path, symbols: tuple[str, ...]) -> pd.DataFrame:
    base = x.load_close(data_dir, "SPY").index
    cols = {s: x.load_close(data_dir, s).reindex(base) for s in symbols}
    return pd.DataFrame(cols, index=base)


def y1_weights(closes: pd.DataFrame, i: int) -> pd.Series:
    zero = pd.Series(0.0, index=closes.columns)
    c = closes.iloc[: i + 1]
    avail = c.notna().sum() >= Y_MIN_HISTORY
    k = int(avail.sum())
    if k == 0:
        return zero
    cc = c.loc[:, avail]
    sma = (cc.iloc[-1] > cc.iloc[-200:].mean()).astype(float) if len(cc) >= 200 else pd.Series(0.0, index=cc.columns)
    mom = ((cc.iloc[-22] / cc.iloc[-253] - 1) > 0).astype(float) if len(cc) >= 253 else pd.Series(0.0, index=cc.columns)
    s = (sma + mom) / 2
    vol = cc.iloc[-Y_VOL_WINDOW - 1 :].pct_change().std() * math.sqrt(252)
    w = s * (Y_TARGET_VOL / vol).clip(upper=1.0) / k
    zero[w.index] = w.fillna(0.0)
    return zero


def equal_weights(closes: pd.DataFrame, i: int) -> pd.Series:
    avail = closes.iloc[: i + 1].notna().sum() >= Y_MIN_HISTORY
    w = pd.Series(0.0, index=closes.columns)
    if avail.any():
        w[avail] = 1.0 / int(avail.sum())
    return w


def monthly_backtest(weight_fn, closes: pd.DataFrame, cost_vec: np.ndarray, cash_daily: pd.Series | None) -> pd.Series:  # type: ignore[no-untyped-def]
    """Same mechanics as history_trend.backtest, with per-asset costs and an optional cash yield."""
    rets = closes.pct_change().fillna(0.0).to_numpy()
    cash = np.zeros(len(closes)) if cash_daily is None else cash_daily.reindex(closes.index).fillna(0.0).to_numpy()
    n = len(closes)
    sig_at = {i + 1: i for i in g.month_end_positions(closes.index)}
    out = np.zeros(n)
    cur = np.zeros(closes.shape[1])
    for t in range(1, n):
        gain = float(cur @ rets[t]) + (1.0 - float(cur.sum())) * cash[t]
        out[t] += gain
        grown = cur * (1 + rets[t])
        cur = grown / (1 + gain) if (1 + gain) != 0 else grown
        if t in sig_at:
            new = weight_fn(closes, sig_at[t]).to_numpy()
            out[t] -= float(np.abs(new - cur) @ cost_vec)
            cur = new
    return pd.Series(out, index=closes.index)


def y1_run(data_dir: Path) -> dict[str, pd.Series]:
    closes = load_panel(data_dir, Y_UNIVERSE)
    cash = x.tbill_daily(data_dir, closes.index, 252)
    cost = np.array([Y_COST_CRYPTO if c in CRYPTO else Y_COST_ETF for c in closes.columns])
    bench = load_panel(data_dir, ("SPY", "AGG"))
    b_cost = np.array([Y_COST_ETF, Y_COST_ETF])
    return {
        "Y1": monthly_backtest(y1_weights, closes, cost, cash),
        "Y1_stress": monthly_backtest(y1_weights, closes, cost * 2, cash),
        "60_40": monthly_backtest(lambda c, i: pd.Series([0.6, 0.4], index=c.columns), bench, b_cost, None),
        "equal_weight": monthly_backtest(equal_weights, closes, cost, cash),
    }


def sub(r: pd.Series, subs: tuple[tuple[str, str], ...], periods: int) -> list[float]:
    return x.sub_cagrs(r, subs, periods)


def trial_sharpes(data_dir: Path, x4_net: pd.Series, y1_net: pd.Series) -> list[float]:
    res, _ = hc.run_all(data_dir)
    out = [g.stats(res[k]).sharpe / math.sqrt(252) for k in (*g.NAMES, *hc.HNAMES)]
    for n in x.NAMES:
        spec = x.SPECS[n]
        out.append(x.stats_for(x.evaluate(n, data_dir)[0], spec.start, spec.periods).sharpe / math.sqrt(spec.periods))
    out.append(x.stats_for(x4_net, "2015-01-01", 365).sharpe / math.sqrt(365))
    out.append(x.stats_for(y1_net, Y_START, 252).sharpe / math.sqrt(252))
    return out


def judge_x4(net: pd.Series, stress: pd.Series, bh: pd.Series, trials: list[float]) -> tuple[bool, list[str]]:
    s, s2, b = (x.stats_for(r, "2015-01-01", 365) for r in (net, stress, bh))
    dsr = g.deflated_sharpe_prob(s.sharpe / math.sqrt(365), s.days, s.skew, s.kurt, trials)
    subs = sub(net, X4_SUBS, 365)
    checks = {
        "net Sharpe >= 0.60": s.sharpe >= 0.60,
        f"net Sharpe {s.sharpe:.2f} >= BTC buy-and-hold {b.sharpe:.2f}": s.sharpe >= b.sharpe,
        f"Deflated Sharpe prob {dsr:.2f} >= 0.95 (N={len(trials)})": dsr >= 0.95,
        f"max drawdown {s.max_dd:.0%} no deeper than 45%": abs(s.max_dd) <= 0.45,
        f"net CAGR {s.cagr:.1%} >= 15%": s.cagr >= 0.15,
        "net CAGR > 0 in every sub-period": all(c > 0 for c in subs),
        "Sharpe >= 0.40 at 3x cost": s2.sharpe >= 0.40,
    }
    return all(checks.values()), [f"{'ok  ' if v else 'FAIL'} {k}" for k, v in checks.items()]


def judge_y1(r: dict[str, pd.Series], trials: list[float]) -> tuple[bool, list[str]]:
    s, s2, b = (x.stats_for(r[k], Y_START, 252) for k in ("Y1", "Y1_stress", "60_40"))
    dsr = g.deflated_sharpe_prob(s.sharpe / math.sqrt(252), s.days, s.skew, s.kurt, trials)
    subs = sub(r["Y1"], Y_SUBS, 252)
    checks = {
        "net Sharpe >= 0.60": s.sharpe >= 0.60,
        f"net Sharpe {s.sharpe:.2f} >= 60/40 {b.sharpe:.2f}": s.sharpe >= b.sharpe,
        f"Deflated Sharpe prob {dsr:.2f} >= 0.95 (N={len(trials)})": dsr >= 0.95,
        f"max drawdown {s.max_dd:.0%} no deeper than 60/40's {b.max_dd:.0%}": s.max_dd >= b.max_dd,
        "net CAGR > 0 in every sub-period": all(c > 0 for c in subs),
        "Sharpe >= 0.40 at 2x cost": s2.sharpe >= 0.40,
    }
    return all(checks.values()), [f"{'ok  ' if v else 'FAIL'} {k}" for k, v in checks.items()]


def main(data_dir: Path = g.DATA) -> int:  # pragma: no cover - reads the local data
    x4_net, bh = x4_run(data_dir, x.COST_CRYPTO)
    x4_stress, _ = x4_run(data_dir, x.COST_CRYPTO * 3)
    y1 = y1_run(data_dir)
    trials = trial_sharpes(data_dir, x4_net, y1["Y1"])
    print(f"WORKSTREAM Y verdicts (protocol rules 2, 3, 7; global N = 12, Deflated Sharpe N = {len(trials)})\n")
    s, b = x.stats_for(x4_net, "2015-01-01", 365), x.stats_for(bh, "2015-01-01", 365)
    print(f"X4 vol-targeted BTC trend   Sharpe {s.sharpe:.2f}  CAGR {s.cagr:.1%}  maxDD {s.max_dd:.1%}  subs " + " / ".join(f"{c:+.1%}" for c in sub(x4_net, X4_SUBS, 365)) + f"   | B&H {b.sharpe:.2f} / {b.cagr:.1%} / {b.max_dd:.1%}")
    ok, lines = judge_x4(x4_net, x4_stress, bh, trials)
    print(f"X4: {'PASS (candidate for a paper trade)' if ok else 'NO'}")
    for ln in lines:
        print("   " + ln)
    print("\nX5 robustness grid (net Sharpe vs buy and hold):")
    grid = x5_grid(data_dir)
    for name, n, sh, bsh in grid:
        print(f"   {name}{n:<4} Sharpe {sh:5.2f}   B&H {bsh:5.2f}   {'beats' if sh >= bsh else 'below'}")
    beat = sum(1 for _, _, sh, bsh in grid if sh >= bsh) / len(grid)
    robust = all(sh >= 0.80 for _, _, sh, _ in grid) and beat >= 0.75
    print(f"X5: {'ROBUST' if robust else 'FRAGILE'} ({beat:.0%} of cells beat buy and hold; min Sharpe {min(sh for _, _, sh, _ in grid):.2f})")
    print("\nY1 cross-asset trend (2008-2025):")
    for k in ("Y1", "60_40", "equal_weight"):
        st = x.stats_for(y1[k], Y_START, 252)
        print(f"   {k:14} Sharpe {st.sharpe:5.2f}  CAGR {st.cagr:6.1%}  maxDD {st.max_dd:7.1%}  subs " + " / ".join(f"{c:+.1%}" for c in sub(y1[k], Y_SUBS, 252)))
    ok, lines = judge_y1(y1, trials)
    print(f"Y1: {'PASS (candidate for a paper trade)' if ok else 'NO'}")
    for ln in lines:
        print("   " + ln)
    print("\nLimits: today's ETFs and two surviving coins, one path, assumed costs, UNG/USO contango inside returns, 2026 untouched. PASS is a candidate, never a promise.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else g.DATA))
