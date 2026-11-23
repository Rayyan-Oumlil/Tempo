"""Workstream Z (docs/plan-quant-v2.md, protocol frozen 2026-11-23, commit 76ff992): X4 rule on ETH/LTC/BCH, turn-of-month on SPY,
USMV against SPY, and an independence diagnostic. Reuses the Y/X machinery unchanged; nothing after 2025-12-31 is loaded."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from tempo import history_trend as g
from tempo import history_xc as x
from tempo import history_y as y

COINS = ("ETH-USD", "LTC-USD", "BCH-USD")
COST_ETF = 0.0005
Z2_START, Z2_END = "2000-01-01", "2025-12-31"
Z2_SUBS = (("2000-01-01", "2008-12-31"), ("2009-01-01", "2017-12-31"), ("2018-01-01", "2025-12-31"))
Z3_START = "2012-01-01"
# Logged Sharpes of the 11 earlier trials and their annualisation (plan v2, Workstream Z, trial accounting).
PRIOR_TRIALS = (
    (0.59, 252), (0.60, 252), (0.55, 252), (0.62, 252), (0.63, 252), (0.43, 252),  # G1-G6
    (0.52, 252), (1.31, 365), (0.90, 365), (1.38, 365), (0.95, 252),  # X1, X2, X3, X4, Y1
)


def prior_daily_sharpes() -> list[float]:
    return [sr / math.sqrt(per) for sr, per in PRIOR_TRIALS]


def equal_subperiods(start: pd.Timestamp, end: pd.Timestamp) -> tuple[tuple[str, str], ...]:
    """Three sub-periods of equal calendar length covering [start, end]."""
    step = (end - start) / 3
    cuts = [start, start + step, start + 2 * step, end]
    out = []
    for i in range(3):
        a = cuts[i] if i == 0 else (cuts[i] + pd.Timedelta(days=1)).normalize()
        b = cuts[i + 1].normalize()
        out.append((a.strftime("%Y-%m-%d"), b.strftime("%Y-%m-%d")))
    return tuple(out)


def turn_of_month_days(index: pd.DatetimeIndex) -> pd.Series:
    """True on the last trading day of each month and on trading days 1, 2, 3 of each month."""
    s = pd.Series(index, index=index)
    month = s.dt.year * 100 + s.dt.month
    pos_from_start = s.groupby(month).cumcount()
    pos_from_end = s.groupby(month).cumcount(ascending=False)
    return (pos_from_start < 3) | (pos_from_end == 0)


def turn_of_month_run(closes: pd.Series, cash_daily: pd.Series, cost: float) -> pd.Series:
    rets = closes.pct_change().fillna(0.0)
    pos = turn_of_month_days(closes.index).astype(float)
    gross = pos * rets + (1.0 - pos) * cash_daily.reindex(closes.index).fillna(0.0)
    return gross - cost * pos.diff().abs().fillna(0.0)


def buy_hold_with_entry(closes: pd.Series, cost: float) -> pd.Series:
    r = closes.pct_change().fillna(0.0)
    r.iloc[0] -= cost
    return r


def coin_run(data_dir: Path, coin: str, cost: float) -> tuple[pd.Series, pd.Series, str]:
    close = x.load_close(data_dir, coin).rename(coin)
    closes = close.to_frame()
    cash = x.tbill_daily(data_dir, closes.index, 365)
    net = x.run(y.x4_weights(close), closes, cash, cost)
    bh = x.buy_hold(closes, cash, x.COST_CRYPTO)
    start = (close.index[0] + pd.Timedelta(days=365)).strftime("%Y-%m-%d")
    return net, bh, start


def judge_coin(net: pd.Series, stress: pd.Series, bh: pd.Series, start: str, trials: list[float]) -> tuple[bool, list[str]]:
    s, s2, b = (x.stats_for(r, start, 365) for r in (net, stress, bh))
    dsr = g.deflated_sharpe_prob(s.sharpe / math.sqrt(365), s.days, s.skew, s.kurt, trials)
    subs = x.sub_cagrs(net, equal_subperiods(pd.Timestamp(start), net.index[-1]), 365)
    checks = {
        "net Sharpe >= 0.60": s.sharpe >= 0.60,
        f"net Sharpe {s.sharpe:.2f} >= buy-and-hold {b.sharpe:.2f}": s.sharpe >= b.sharpe,
        f"Deflated Sharpe prob {dsr:.2f} >= 0.95 (N={len(trials)})": dsr >= 0.95,
        f"max drawdown {s.max_dd:.0%} no deeper than 45%": abs(s.max_dd) <= 0.45,
        f"net CAGR {s.cagr:.1%} >= 15%": s.cagr >= 0.15,
        "net CAGR > 0 in every sub-period": all(c > 0 for c in subs),
        "Sharpe >= 0.40 at 3x cost": s2.sharpe >= 0.40,
    }
    return all(checks.values()), [f"{'ok  ' if v else 'FAIL'} {k}" for k, v in checks.items()]


def judge_tom(net: pd.Series, stress: pd.Series, bh: pd.Series, trials: list[float]) -> tuple[bool, list[str]]:
    s, s2, b = (x.stats_for(r, Z2_START, 252) for r in (net, stress, bh))
    dsr = g.deflated_sharpe_prob(s.sharpe / math.sqrt(252), s.days, s.skew, s.kurt, trials)
    subs = x.sub_cagrs(net, Z2_SUBS, 252)
    checks = {
        f"net Sharpe {s.sharpe:.2f} >= SPY {b.sharpe:.2f}": s.sharpe >= b.sharpe,
        f"Deflated Sharpe prob {dsr:.2f} >= 0.95 (N={len(trials)})": dsr >= 0.95,
        "net CAGR > 0 in every sub-period": all(c > 0 for c in subs),
        "Sharpe >= 0.40 at 2x cost": s2.sharpe >= 0.40,
    }
    return all(checks.values()), [f"{'ok  ' if v else 'FAIL'} {k}" for k, v in checks.items()]


def judge_lowvol(net: pd.Series, bh: pd.Series, trials: list[float]) -> tuple[bool, list[str]]:
    s, b = (x.stats_for(r, Z3_START, 252) for r in (net, bh))
    dsr = g.deflated_sharpe_prob(s.sharpe / math.sqrt(252), s.days, s.skew, s.kurt, trials)
    checks = {
        f"net Sharpe {s.sharpe:.2f} >= SPY {b.sharpe:.2f}": s.sharpe >= b.sharpe,
        f"max drawdown {s.max_dd:.0%} shallower than SPY's {b.max_dd:.0%}": s.max_dd > b.max_dd,
        f"Deflated Sharpe prob {dsr:.2f} >= 0.95 (N={len(trials)})": dsr >= 0.95,
    }
    return all(checks.values()), [f"{'ok  ' if v else 'FAIL'} {k}" for k, v in checks.items()]


def on_trading_days(r: pd.Series, days: pd.DatetimeIndex) -> pd.Series:
    """Compound a daily return series between the given trading dates (crypto trades on weekends)."""
    eq = (1 + r.fillna(0.0)).cumprod().reindex(r.index.union(days)).ffill().reindex(days)
    return eq.pct_change().dropna()


def independence(sleeves: dict[str, pd.Series], days: pd.DatetimeIndex) -> tuple[pd.DataFrame, dict[str, float]]:
    aligned = pd.DataFrame({k: on_trading_days(v, days) for k, v in sleeves.items()}).dropna()
    corr = aligned.corr()
    base = aligned["X4_BTC"]
    blend: dict[str, float] = {}
    for k in aligned.columns:
        if k == "X4_BTC":
            continue
        inv = np.array([1 / base.std(), 1 / aligned[k].std()])
        w = inv / inv.sum()
        mix = w[0] * base + w[1] * aligned[k]
        blend[k] = float(mix.mean() / mix.std() * math.sqrt(252))
    return corr, blend


def main(data_dir: Path = Path("data/z")) -> int:  # pragma: no cover - reads the local data
    trials = prior_daily_sharpes()
    results: dict[str, tuple[pd.Series, str, float, int]] = {}
    verdicts: dict[str, bool] = {}
    n_total = len(trials) + 5
    print(f"WORKSTREAM Z verdicts (protocol Z1-Z5; global N = 17, Deflated Sharpe N = {n_total})\n")

    coin_out = {}
    for coin in COINS:
        net, bh, start = coin_run(data_dir, coin, x.COST_CRYPTO)
        stress, _, _ = coin_run(data_dir, coin, x.COST_CRYPTO * 3)
        coin_out[coin] = (net, stress, bh, start)
    tbill = x.tbill_daily(data_dir, x.load_close(data_dir, "SPY").index, 252)
    spy = x.load_close(data_dir, "SPY")
    spy2 = spy[spy.index >= pd.Timestamp(Z2_START)]
    tom = turn_of_month_run(spy2, tbill.reindex(spy2.index), COST_ETF)
    tom_stress = turn_of_month_run(spy2, tbill.reindex(spy2.index), COST_ETF * 2)
    spy_bh = buy_hold_with_entry(spy2, COST_ETF)
    spy3 = spy[spy.index >= pd.Timestamp(Z3_START)]
    usmv = buy_hold_with_entry(x.load_close(data_dir, "USMV").loc[lambda s: s.index >= pd.Timestamp(Z3_START)], COST_ETF)
    spy3_bh = buy_hold_with_entry(spy3, COST_ETF)

    own = [x.stats_for(coin_out[c][0], coin_out[c][3], 365).sharpe / math.sqrt(365) for c in COINS]
    own.append(x.stats_for(tom, Z2_START, 252).sharpe / math.sqrt(252))
    own.append(x.stats_for(usmv, Z3_START, 252).sharpe / math.sqrt(252))
    all_trials = trials + own

    for coin in COINS:
        net, stress, bh, start = coin_out[coin]
        s, b = x.stats_for(net, start, 365), x.stats_for(bh, start, 365)
        subs = x.sub_cagrs(net, equal_subperiods(pd.Timestamp(start), net.index[-1]), 365)
        ok, lines = judge_coin(net, stress, bh, start, all_trials)
        verdicts[coin] = ok
        print(f"Z1 {coin} (from {start})  Sharpe {s.sharpe:.2f}  CAGR {s.cagr:.1%}  maxDD {s.max_dd:.1%}  subs " + " / ".join(f"{c:+.1%}" for c in subs) + f"   | B&H {b.sharpe:.2f} / {b.cagr:.1%} / {b.max_dd:.1%}")
        print(f"   {'PASS (candidate)' if ok else 'NO'}")
        for ln in lines:
            print("      " + ln)
    s, b = x.stats_for(tom, Z2_START, 252), x.stats_for(spy_bh, Z2_START, 252)
    invested = float(y_invested(spy2.index))
    ok, lines = judge_tom(tom, tom_stress, spy_bh, all_trials)
    verdicts["Z2"] = ok
    print(f"\nZ2 turn-of-month SPY  Sharpe {s.sharpe:.2f}  CAGR {s.cagr:.1%}  maxDD {s.max_dd:.1%}  subs " + " / ".join(f"{c:+.1%}" for c in x.sub_cagrs(tom, Z2_SUBS, 252)) + f"   | SPY B&H {b.sharpe:.2f} / {b.cagr:.1%} / {b.max_dd:.1%}   invested {invested:.0%} of days")
    print(f"   {'PASS (candidate)' if ok else 'NO'}")
    for ln in lines:
        print("      " + ln)
    s, b = x.stats_for(usmv, Z3_START, 252), x.stats_for(spy3_bh, Z3_START, 252)
    ok, lines = judge_lowvol(usmv, spy3_bh, all_trials)
    verdicts["Z3"] = ok
    print(f"\nZ3 USMV vs SPY (2012-2025)  Sharpe {s.sharpe:.2f}  CAGR {s.cagr:.1%}  maxDD {s.max_dd:.1%}   | SPY {b.sharpe:.2f} / {b.cagr:.1%} / {b.max_dd:.1%}")
    print(f"   {'PASS (candidate)' if ok else 'NO'}")
    for ln in lines:
        print("      " + ln)

    x4, _ = y.x4_run(data_dir, x.COST_CRYPTO)
    sleeves = {"X4_BTC": x4, "Z1a_ETH": coin_out["ETH-USD"][0], "Z1b_LTC": coin_out["LTC-USD"][0], "Z1c_BCH": coin_out["BCH-USD"][0], "Z2_TOM": tom, "Z3_USMV": usmv, "SPY_BH": spy_bh}
    corr, blend = independence(sleeves, spy.index[spy.index >= pd.Timestamp(Z3_START)])
    print("\nZ0 independence (daily returns on trading days, common window from 2018-11 on, info only, no verdict):")
    print(corr.round(2).to_string())
    print("Sharpe of an inverse-volatility blend of X4 with each:", {k: round(v, 2) for k, v in blend.items()})
    print("\nLimits: survivor coins, one path, assumed costs, 2026 untouched. PASS is a candidate, never a promise. Z5: a pass also needs a Z0 correlation with X4 below 0.5.")
    return 0


def y_invested(index: pd.DatetimeIndex) -> float:
    return float(turn_of_month_days(index).mean())


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/z")))
