import numpy as np
import pandas as pd

from tempo import history_trend as g
from tempo.history_cash import load_tbill_daily, put_returns


def frame(n=400):
    idx = pd.bdate_range("2007-01-01", periods=n)
    rng = np.random.default_rng(3)
    return pd.DataFrame({s: 100 * np.cumprod(1 + rng.normal(0.0005, 0.01, n)) for s in ("SPY", "AGG", "GLD")}, index=idx)


def test_tbill_uses_previous_day_value_no_lookahead(tmp_path):
    pd.DataFrame({"observation_date": ["2024-01-02", "2024-01-03", "2024-01-04"], "DTB3": [5.04, 2.52, "."]}).to_csv(tmp_path / "DTB3.csv", index=False)
    idx = pd.DatetimeIndex(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
    c = load_tbill_daily(tmp_path, idx)
    assert c.iloc[0] == 0.0  # nothing known before the first print
    assert abs(c.iloc[1] - 0.0504 / 252) < 1e-12  # day t earns day t-1's rate
    assert abs(c.iloc[2] - 0.0252 / 252) < 1e-12
    assert abs(c.iloc[3] - 0.0252 / 252) < 1e-12  # '.' (holiday) carries the last value forward


def test_tbill_ignores_dates_after_the_holdout(tmp_path):
    pd.DataFrame({"observation_date": ["2025-12-30", "2026-01-05"], "DTB3": [4.0, 9.0]}).to_csv(tmp_path / "DTB3.csv", index=False)
    c = load_tbill_daily(tmp_path, pd.DatetimeIndex(["2026-01-06"]))
    assert abs(c.iloc[0] - 0.04 / 252) < 1e-12


def test_cash_zero_equals_default_and_cash_adds_only_on_uninvested_fraction():
    c = frame()
    base = g.backtest("G1_sma200", c)
    assert g.backtest("G1_sma200", c, cash_daily=pd.Series(0.0, index=c.index)).equals(base)
    cash = pd.Series(0.0004, index=c.index)
    lifted = g.backtest("G1_sma200", c, cash_daily=cash)
    assert (lifted - base).min() >= -1e-12  # earning on cash never hurts
    assert (lifted - base).max() > 0  # and it does help while uninvested
    all_cash = g.backtest("G1_sma200", c.iloc[:150], cash_daily=pd.Series(0.0004, index=c.index[:150]))
    assert abs(all_cash.sum() - 0.0004 * (all_cash != 0).sum()) < 1e-9  # under 200 days: pure cash earns exactly the rate


def test_put_returns_subtract_drag_and_stop_at_the_holdout(tmp_path):
    pd.DataFrame({"date": ["2025-12-30", "2025-12-31", "2026-01-02"], "close": [100.0, 101.0, 500.0]}).to_csv(tmp_path / "_PUT_1d.csv", index=False)
    r = put_returns(tmp_path, drag=0.0252)
    assert len(r) == 2
    assert abs(r.iloc[1] - (0.01 - 0.0252 / 252)) < 1e-12
