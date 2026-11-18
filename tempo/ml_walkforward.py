"""Workstream M runner (protocol frozen 2026-11-17 in docs/plan-quant-v2.md).

  python -m tempo.ml_walkforward build     build and cache the panel (data/history/ml/panel.parquet)
  python -m tempo.ml_walkforward run [core] purged walk-forward over 2022-2025: three models, six books, placebo, verdicts
  python -m tempo.ml_walkforward retest    R1: weekly_reversal_v1 on the merged ~2,200-symbol universe

Hyperparameters are fixed in the protocol and never tuned. A FORWARD verdict means 'worth a forward test', never real money.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from tempo.autopsy import bh_threshold, p_value
from tempo.history_core import Trade, Verdict, judge
from tempo.ml_panel import FEATURES
from tempo.sequential import hac_variance_of_mean

DATA = Path(__file__).resolve().parents[1] / "data"
PANEL = DATA / "history" / "ml" / "panel.parquet"
REPORT = DATA / "history" / "ml" / "ml_report.json"
TEST_YEARS = (2022, 2023, 2024, 2025)
PURGE_SESSIONS = 10
COST = 0.002
HORIZON = 5
NW_HORIZON = 7           # judge() uses lag = horizon - 1 = 6: cohorts overlap for 6 days
MAX_PER_SIDE, SIDE_FRACTION, MIN_PER_SIDE = 50, 0.10, 10
SEED = 7
MODELS = ("lgbm", "ridge", "reversal")


def per_side(n: int) -> int:
    return max(MIN_PER_SIDE, min(MAX_PER_SIDE, int(SIDE_FRACTION * n)))


def train_cutoff(sessions: list[str], test_year: int) -> str:
    """Last session a training row may have: PURGE_SESSIONS before the first session of the test year."""
    first = next(i for i, d in enumerate(sessions) if d.startswith(str(test_year)))
    return sessions[first - PURGE_SESSIONS]


def pick_books(day: pd.DataFrame, score: np.ndarray) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """Top and bottom K by score as (symbol, gross beta-hedged return). Ties resolved by symbol so the result is deterministic."""
    k = per_side(len(day))
    order = np.lexsort((day["symbol"].to_numpy(), -score))
    gross = day["gross"].to_numpy()
    sym = day["symbol"].to_numpy()
    top = [(str(sym[i]), float(gross[i])) for i in order[:k]]
    bottom = [(str(sym[i]), float(gross[i])) for i in order[-k:]]
    return top, bottom


def books_from_scores(test: pd.DataFrame, score: np.ndarray) -> dict[str, list[Trade]]:
    ls: list[Trade] = []
    lo: list[Trade] = []
    entries = test["entry"].to_numpy()
    for _, idx in test.groupby("date").indices.items():
        day = test.iloc[idx]
        top, bottom = pick_books(day, score[idx])
        entry = str(entries[idx[0]])[:10]
        for s, g in top:
            ls.append(Trade(entry, s, g))
            lo.append(Trade(entry, s, g))
        for s, g in bottom:
            ls.append(Trade(entry, s, -g))
    return {"long_short": ls, "long_only": lo}


def daily_ic(test: pd.DataFrame, score: np.ndarray) -> list[float]:
    ics = []
    for _, idx in test.groupby("date").indices.items():
        s = pd.Series(score[idx]).rank().to_numpy()
        y = test["y"].to_numpy()[idx]
        if s.std() > 0 and y.std() > 0:
            ics.append(float(np.corrcoef(s, y)[0, 1]))
    return ics


def ic_summary(ics: list[float]) -> tuple[float, float | None]:
    if len(ics) < 30:
        return float("nan"), None
    mean = float(np.mean(ics))
    se = float(np.sqrt(hac_variance_of_mean(ics, NW_HORIZON - 1)))
    return mean, (mean / se if se > 0 else None)


def bh_flags(verdicts: dict[str, Verdict]) -> dict[str, bool]:
    ps = {k: (1.0 if v.t is None or v.t <= 0 else p_value(v.t) / 2) for k, v in verdicts.items()}  # one-sided: only a positive edge counts
    thr = bh_threshold(list(ps.values()))
    return {k: thr is not None and p <= thr for k, p in ps.items()}


def fit_predict(kind: str, train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:  # pragma: no cover - fits models
    if kind == "reversal":
        return -test["r5"].to_numpy(dtype=float)
    y = train["y"].to_numpy()
    if kind == "placebo":
        rng = np.random.default_rng(SEED)
        y = train.groupby("date")["y"].transform(lambda s: rng.permutation(s.to_numpy())).to_numpy()
    if kind == "ridge":
        from sklearn.linear_model import Ridge
        m = Ridge(alpha=1000.0).fit(np.nan_to_num(train[FEATURES].to_numpy()), y)
        return m.predict(np.nan_to_num(test[FEATURES].to_numpy()))
    import lightgbm as lgb
    m = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=31, min_child_samples=500, subsample=0.7, subsample_freq=1,
                          colsample_bytree=0.7, random_state=SEED, n_jobs=12, verbose=-1)
    m.fit(train[FEATURES].to_numpy(), y)
    return m.predict(test[FEATURES].to_numpy())


def render(rows: dict[str, dict], title: str) -> str:  # pragma: no cover
    lines = [title, ""]
    for name, r in rows.items():
        v: Verdict = r["verdict"]
        if v.mean_net is None or v.ci is None or v.mean_net_stress is None:
            lines.append(f"{name:24s} {v.decision}: {'; '.join(v.reasons)}")
            continue
        t = f"{v.t:.2f}" if v.t is not None else "n/a"
        lines.append(f"{name:24s} events {v.events:6d} net {v.mean_net:+.2%} [{v.ci[0]:+.2%}, {v.ci[1]:+.2%}] t {t:>5s}  1.5x {v.mean_net_stress:+.2%}  "
                     f"BH {'pass' if r.get('bh') else 'no':4s} => {v.decision}")
        lines.append(" " * 25 + "by year: " + "  ".join(f"{y} {m:+.2%}" for y, (_, m) in v.years.items()))
    return "\n".join(lines)


def run(core: bool = False) -> int:  # pragma: no cover - fits models on the local panel
    panel = pd.read_parquet(PANEL)
    if core:  # M10: only symbols chosen independently of insider signals
        keep = {p.stem for p in (DATA / "history" / "shortvol" / "bars").glob("*.csv")}
        panel = panel[panel["symbol"].isin(keep)].reset_index(drop=True)
    sessions = sorted(panel["date"].unique())
    print(f"panel {len(panel):,} rows, {panel['symbol'].nunique()} symbols, {sessions[0]} to {sessions[-1]}", flush=True)
    kinds = (*MODELS, "placebo")
    trades: dict[str, dict[str, list[Trade]]] = {k: {"long_short": [], "long_only": []} for k in kinds}
    ics: dict[str, list[float]] = defaultdict(list)
    for year in TEST_YEARS:
        cut = train_cutoff(sessions, year)
        train = panel[panel["date"] <= cut]
        test = panel[panel["date"].str.startswith(str(year))].reset_index(drop=True)
        print(f"fold {year}: train {len(train):,} rows (to {cut}), test {len(test):,} rows", flush=True)
        for kind in kinds:
            score = fit_predict(kind, train, test)
            for book, tr in books_from_scores(test, score).items():
                trades[kind][book].extend(tr)
            ics[kind].extend(daily_ic(test, score))
            print(f"  {kind} done", flush=True)
    years = tuple(str(y) for y in TEST_YEARS)
    verdicts = {f"{k}/{b}": judge(t, COST, NW_HORIZON, years) for k in MODELS for b, t in trades[k].items()}
    flags = bh_flags(verdicts)
    rows = {name: {"verdict": v, "bh": flags[name]} for name, v in verdicts.items()}
    placebo = {f"placebo/{b}": {"verdict": judge(t, COST, NW_HORIZON, years)} for b, t in trades["placebo"].items()}
    print(render(rows, f"M{' CORE (563 shortvol symbols)' if core else ''}: CROSS-SECTIONAL RANKING, purged walk-forward, test 2022-2025, 5-session books, net of 0.20% per trade"))
    print()
    print(render(placebo, "PLACEBO (labels permuted within each day): must not pass"))
    print()
    for k in kinds:
        m, t = ic_summary(ics[k])
        print(f"rank IC {k:9s} mean {m:+.4f}  NW t {('n/a' if t is None else f'{t:.2f}')}")
    print("\nLimits: today's constituents (long legs flattered); daily bars only; borrow and shorting costs not modelled; 4 out-of-sample years.")
    report = REPORT.with_name("ml_report_core.json") if core else REPORT
    report.parent.mkdir(parents=True, exist_ok=True)
    out = {n: {"decision": r["verdict"].decision, "events": r["verdict"].events, "mean_net": r["verdict"].mean_net, "ci": r["verdict"].ci, "t": r["verdict"].t,
               "years": r["verdict"].years, "stress": r["verdict"].mean_net_stress, "bh": r.get("bh"), "reasons": list(r["verdict"].reasons)} for n, r in {**rows, **placebo}.items()}
    out["ic"] = {k: ic_summary(v) for k, v in ics.items()}
    report.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


def retest() -> int:  # pragma: no cover - reads the local data
    from tempo import history_reversal as hr
    from tempo.history_core import Series
    from tempo.history_report import load_spy
    from tempo.ml_panel import load_symbol, symbols
    spy = load_spy()
    universe = {}
    for s in symbols():
        df = load_symbol(s)
        if df is None or len(df) < 200:
            continue
        df = df.dropna()
        df = df[(df["open"] > 0) & (df["close"] > 0)]
        df = df.loc[:"2025-12-31"]
        universe[s] = Series(list(df.index), df["open"].tolist(), df["close"].tolist(), df["volume"].tolist())
    print(f"{len(universe)} symbols with bars")
    trades, counts = hr.reversal_trades(universe, spy, "2023-01-02")
    v = judge(trades, hr.COST, hr.HORIZON)
    print(render({"weekly_reversal_v1 (2,200-symbol universe)": {"verdict": v}}, "R1 RE-TEST, test 2023-2025, rule unchanged"))
    print("counts:", dict(counts))
    return 0


def main(argv: list[str]) -> int:  # pragma: no cover
    if argv[:1] == ["build"]:
        from tempo.ml_panel import build_panel
        panel = build_panel()
        panel["date"] = panel["date"].astype(str)
        panel["entry"] = panel["entry"].astype(str).str[:10]
        PANEL.parent.mkdir(parents=True, exist_ok=True)
        panel.to_parquet(PANEL)
        print(f"{len(panel):,} rows, {panel['symbol'].nunique()} symbols, {panel['date'].min()} to {panel['date'].max()}")
        return 0
    if argv[:1] == ["run"]:
        return run(core=argv[1:2] == ["core"])
    if argv[:1] == ["retest"]:
        return retest()
    print(__doc__)
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main(sys.argv[1:]))
