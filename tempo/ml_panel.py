"""Workstream M (docs/plan-quant-v2.md, protocol frozen 2026-11-17): the daily panel of features and labels for the cross-sectional ranking test.

Every feature of day t uses data up to the close of t; the label starts at the open of t+1. Nothing here is fitted. Local files only.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tempo import history_insider as hi
from tempo.exec_score import SHRINK

DATA = Path(__file__).resolve().parents[1] / "data"
BAR_DIRS = (DATA / "history" / "fast" / "bars", DATA / "history" / "shortvol" / "bars")
SPY_FILE = DATA / "SPY_ohlc.csv"
SETS_DIR = DATA / "insider_sets"
BARS_START, PANEL_START, PANEL_END = "2018-01-01", "2019-01-02", "2025-12-31"
MIN_PRICE, MIN_ADV, MIN_HISTORY = 5.0, 5_000_000.0, 126
HORIZON = 5
INSIDER_SESSIONS = 21  # about 30 calendar days
BUY_QUARTERS = [f"{y}q{q}" for y in range(2019, 2026) for q in (1, 2, 3, 4)]

BASE_FEATURES = ["r1", "r5", "r21", "r63", "r126", "mom_12_1", "vol21", "vol63", "dvol", "vratio", "gap", "intraday", "hi252", "beta60"]
INSIDER_FEATURES = ["ins_n30", "ins_val30", "ins_od30", "ins_days"]
FEATURES = BASE_FEATURES + INSIDER_FEATURES


def load_calendar() -> pd.DataFrame:
    spy = pd.read_csv(SPY_FILE, usecols=["date", "open", "close"]).set_index("date")
    return spy.loc[BARS_START:PANEL_END]  # 2026 is never read: it stays a holdout


def load_symbol(symbol: str) -> pd.DataFrame | None:
    frames = []
    for d in BAR_DIRS:
        p = d / f"{symbol}.csv"
        if p.exists():
            frames.append(pd.read_csv(p, usecols=["date", "open", "close", "volume"]).set_index("date"))
    if not frames:
        return None
    df = pd.concat(frames)
    return df[~df.index.duplicated(keep="first")].sort_index()


def symbols() -> list[str]:
    return sorted({p.stem for d in BAR_DIRS for p in d.glob("*.csv")} - {"SPY"})


def insider_buys() -> pd.DataFrame:
    rows = []
    for q in BUY_QUARTERS:
        path = SETS_DIR / f"{q}_form345.zip"
        if not path.exists():
            raise SystemExit(f"missing {path}: fetch the Form sets first (python -m tempo.history_fetch sets)")
        for b in hi.buys_from_zip(path.read_bytes()):
            rows.append((b["filing_date"], b["symbol"], b["value"], 1 if b["officer_director"] else 0))
    return pd.DataFrame(rows, columns=["filed", "symbol", "value", "od"])


def insider_features(buys: pd.DataFrame, symbol: str, index: pd.Index) -> pd.DataFrame:
    """Counts, value and officer/director purchases filed in the last 21 sessions, and calendar days since the last filing (cap 365)."""
    out = pd.DataFrame(0.0, index=index, columns=INSIDER_FEATURES)
    out["ins_days"] = 365.0
    sub = buys[buys["symbol"] == symbol]
    if sub.empty:
        return out
    pos = index.searchsorted(sub["filed"].to_numpy())  # first session on or after the filing date
    ok = pos < len(index)
    sub, pos = sub[ok], pos[ok]
    n_arr, val_arr, od_arr = np.zeros(len(index)), np.zeros(len(index)), np.zeros(len(index))
    np.add.at(n_arr, pos, 1.0)
    np.add.at(val_arr, pos, sub["value"].to_numpy())
    np.add.at(od_arr, pos, sub["od"].to_numpy().astype(float))
    n, val, od = (pd.Series(a, index=index) for a in (n_arr, val_arr, od_arr))
    out["ins_n30"] = n.rolling(INSIDER_SESSIONS, min_periods=1).sum()
    out["ins_val30"] = np.log1p(val.rolling(INSIDER_SESSIONS, min_periods=1).sum())
    out["ins_od30"] = od.rolling(INSIDER_SESSIONS, min_periods=1).sum()
    seen = pd.Series(np.where(n.to_numpy() > 0, np.arange(len(index)), np.nan), index=index).ffill()
    dates = pd.to_datetime(pd.Series(index, index=index))
    last = pd.Series(pd.NaT, index=index, dtype="datetime64[ns]")
    ok_seen = seen.notna()
    last[ok_seen] = dates.iloc[seen[ok_seen].astype(int).to_numpy()].to_numpy()
    out["ins_days"] = ((dates - last).dt.days).fillna(365).clip(upper=365)
    return out


def symbol_frame(df: pd.DataFrame, cal: pd.DataFrame, buys: pd.DataFrame, symbol: str) -> pd.DataFrame:
    idx = cal.index
    d = df.reindex(idx)
    bad = (d["close"] <= 0) | (d["open"] <= 0)  # a zero or negative price is a data error, never a move
    d.loc[bad, ["open", "close", "volume"]] = np.nan
    o, c, v = d["open"], d["close"], d["volume"]
    ret1 = c.pct_change(fill_method=None)
    spy_c, spy_o = cal["close"], cal["open"]
    spy_ret = spy_c.pct_change()
    f = pd.DataFrame(index=idx)
    for n in (1, 5, 21, 63, 126):
        f[f"r{n}"] = c / c.shift(n) - 1
    f["mom_12_1"] = c.shift(21) / c.shift(252) - 1
    f["vol21"] = ret1.rolling(21, min_periods=15).std()
    f["vol63"] = ret1.rolling(63, min_periods=40).std()
    adv = (c * v).rolling(20, min_periods=15).mean()
    f["dvol"] = np.log(adv.where(adv > 0))
    f["vratio"] = v / v.rolling(20, min_periods=15).mean()
    f["gap"] = o / c.shift(1) - 1
    f["intraday"] = c / o - 1
    f["hi252"] = c / c.rolling(252, min_periods=126).max() - 1
    f["beta60"] = ret1.rolling(60, min_periods=40).cov(spy_ret) / spy_ret.rolling(60, min_periods=40).var()
    f = f.join(insider_features(buys, symbol, idx))
    f["close"], f["adv"] = c, adv
    f["nhist"] = c.notna().cumsum()
    fwd = c.shift(-(1 + HORIZON)) / o.shift(-1) - 1
    fwd_spy = spy_c.shift(-(1 + HORIZON)) / spy_o.shift(-1) - 1
    f["fwd_excess"] = fwd - fwd_spy
    f["gross"] = fwd - (SHRINK * f["beta60"] + (1 - SHRINK)) * fwd_spy  # exec_v2: beta-hedged, shrunk beta
    f["entry"] = pd.Series(idx, index=idx).shift(-1)
    return f.replace([np.inf, -np.inf], np.nan)


def build_panel() -> pd.DataFrame:  # pragma: no cover - reads the local data
    cal = load_calendar()
    buys = insider_buys()
    frames = []
    for s in symbols():
        df = load_symbol(s)
        if df is None or len(df) < 200:
            continue
        f = symbol_frame(df, cal, buys, s)
        f = f.loc[PANEL_START:]
        keep = (f["close"] >= MIN_PRICE) & (f["adv"] >= MIN_ADV) & (f["nhist"] >= MIN_HISTORY) & f["beta60"].notna() & f["gross"].notna() & f["fwd_excess"].notna()
        f = f[keep].copy()
        f["symbol"] = s
        frames.append(f)
    panel = pd.concat(frames)
    panel.index.name = "date"
    panel = panel.reset_index()
    ranked = panel.groupby("date")[FEATURES].rank(pct=True) - 0.5
    panel[FEATURES] = ranked.astype("float32")
    panel["y"] = (panel.groupby("date")["fwd_excess"].rank(pct=True) - 0.5).astype("float32")
    return panel
