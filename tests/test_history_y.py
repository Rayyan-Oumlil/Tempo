import numpy as np
import pandas as pd

from tempo import history_y as y


def series(vals, name="BTC-USD"):
    return pd.Series(vals, index=pd.date_range("2020-01-01", periods=len(vals)), name=name)


def test_x4_weight_is_zero_when_signal_off_and_capped_at_one():
    flat = series(np.full(200, 100.0))
    assert y.x4_weights(flat).iloc[-1, 0] == 0.0
    rng = np.random.default_rng(0)
    calm = series(100 * np.cumprod(1 + rng.normal(0.002, 0.001, 300)))  # tiny vol -> target would exceed 1
    w = y.x4_weights(calm).iloc[:, 0]
    assert w.max() <= 1.0 and w.iloc[-1] == 1.0


def test_x4_band_suppresses_small_changes_but_flip_acts_at_once():
    rng = np.random.default_rng(1)
    up = 100 * np.cumprod(1 + rng.normal(0.003, 0.03, 300))
    w = y.x4_weights(series(up)).iloc[:, 0]
    changes = (w.diff().abs() > 0).sum()
    assert changes < 120  # a daily-resizing rule would change on almost every one of ~200 days
    down = np.r_[up, up[-1] * np.cumprod(np.full(60, 0.97))]
    assert y.x4_weights(series(down)).iloc[-1, 0] == 0.0


def test_y1_asset_enters_only_after_253_days_and_caps_at_one_over_k():
    idx = pd.bdate_range("2010-01-01", periods=400)
    rng = np.random.default_rng(2)
    a = pd.Series(100 * np.cumprod(1 + rng.normal(0.001, 0.005, 400)), index=idx)
    b = a.copy()
    b.iloc[:200] = np.nan
    c = pd.DataFrame({"A": a, "B": b})
    w = y.y1_weights(c, 300)  # B has 101 days: not yet in
    assert w["B"] == 0.0 and 0 < w["A"] <= 1.0
    w2 = y.y1_weights(c, 399)  # B has 200 days: still not in
    assert w2["B"] == 0.0
    c2 = pd.DataFrame({"A": a, "B": a * 1.0})
    w3 = y.y1_weights(c2, 399)
    assert (w3 <= 0.5 + 1e-12).all()


def test_monthly_backtest_charges_cost_on_turnover_and_pays_cash():
    idx = pd.bdate_range("2020-01-01", periods=80)
    c = pd.DataFrame({"A": np.full(80, 100.0)}, index=idx)
    cash = pd.Series(0.0001, index=idx)
    r = y.monthly_backtest(lambda cl, i: pd.Series([1.0], index=cl.columns), c, np.array([0.001]), cash)
    assert abs(r.min() + 0.0009) < 1e-9  # trade day: 1 bp cash earned, then 10 bps entry cost; flat prices earn nothing after
    r0 = y.monthly_backtest(lambda cl, i: pd.Series([0.0], index=cl.columns), c, np.array([0.001]), cash)
    assert abs(r0.iloc[1:].sum() - 0.0001 * 79) < 1e-12  # all cash earns the rate every day after the first
