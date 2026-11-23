import numpy as np
import pandas as pd

from tempo import history_xc as x


def px(vals, start="2020-01-01"):
    return pd.DataFrame({"A": vals}, index=pd.date_range(start, periods=len(vals), freq="D"))


def test_sma_signal_uses_only_data_up_to_the_row():
    c = px(np.r_[np.full(120, 100.0), np.full(10, 200.0)])
    s = x.signal("X2_btc_sma100", c)
    assert s["A"].iloc[98] == 0.0  # not enough history: rolling mean is NaN, comparison False
    assert s["A"].iloc[120] == 1.0  # first jump day already above the 100-day mean
    assert s["A"].iloc[119] == 0.0  # the day before the jump knows nothing of it


def test_position_lags_signal_by_two_days_and_costs_turnover():
    c = px([100.0, 100.0, 100.0, 110.0, 121.0, 133.1])
    sig = pd.DataFrame({"A": [0, 1, 1, 1, 1, 1.0]}, index=c.index)
    cash = pd.Series(0.0, index=c.index)
    r = x.run(sig, c, cash, cost=0.001)
    assert r.iloc[2] == 0.0
    # signal row 1 -> position from row 3: earns day-3 return 10% minus 0.1% cost on the entry
    assert abs(r.iloc[3] - (0.10 - 0.001)) < 1e-12
    assert abs(r.iloc[4] - 0.10) < 1e-12


def test_cash_earns_only_when_uninvested():
    c = px([100.0] * 6)
    cash = pd.Series(0.001, index=c.index)
    assert abs(x.run(pd.DataFrame({"A": 0.0}, index=c.index), c, cash, 0.0).sum() - 0.006) < 1e-12
    assert abs(x.run(pd.DataFrame({"A": 1.0}, index=c.index), c, cash, 0.0).iloc[3:].sum()) < 1e-12


def test_momentum_signal_is_half_weight_and_needs_90_days():
    c = pd.DataFrame({"A": np.linspace(100, 200, 120), "B": np.linspace(200, 100, 120)}, index=pd.date_range("2020-01-01", periods=120))
    s = x.signal("X3_btc_eth_mom90", c)
    assert s["A"].iloc[100] == 0.5 and s["B"].iloc[100] == 0.0
    assert s["A"].iloc[50] == 0.0  # fewer than 90 days of history


def test_holdout_is_cut(tmp_path):
    pd.DataFrame({"date": ["2025-12-31", "2026-01-01"], "close": [1.0, 99.0]}).to_csv(tmp_path / "BTC-USD_1d.csv", index=False)
    assert x.load_close(tmp_path, "BTC-USD").index.max() == pd.Timestamp("2025-12-31")
