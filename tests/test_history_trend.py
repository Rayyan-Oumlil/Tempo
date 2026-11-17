import math

import numpy as np
import pandas as pd
import pytest

from tempo.history_trend import (
    backtest,
    deflated_sharpe_prob,
    month_end_positions,
    stats,
    subperiod_cagrs,
    weights_at,
)


def frame(n=400, drift=0.001, seed=1):
    idx = pd.bdate_range("2007-01-01", periods=n)
    rng = np.random.default_rng(seed)
    cols = {}
    for s in ("SPY", "AGG", "GLD"):
        r = rng.normal(drift, 0.01, n)
        cols[s] = 100 * np.cumprod(1 + r)
    return pd.DataFrame(cols, index=idx)


def test_month_end_positions_are_last_trading_days():
    idx = pd.DatetimeIndex(["2024-01-30", "2024-01-31", "2024-02-01", "2024-02-29", "2024-03-01"])
    assert month_end_positions(idx) == [1, 3]


def test_weights_need_history_else_cash():
    c = frame(100)
    assert float(weights_at("G1_sma200", c, 99).sum()) == 0.0
    assert float(weights_at("G2_tsmom_12_1", c, 99).sum()) == 0.0


def test_sma_rule_holds_uptrend_and_skips_downtrend():
    idx = pd.bdate_range("2007-01-01", periods=300)
    up = pd.Series(np.linspace(100, 200, 300), index=idx)
    down = pd.Series(np.linspace(200, 100, 300), index=idx)
    c = pd.DataFrame({"SPY": up, "AGG": down})
    w = weights_at("G1_sma200", c, 299)
    assert w["SPY"] > 0 and w["AGG"] == 0


def test_weights_respect_caps():
    c = frame(400, drift=0.002)
    for kind in ("G1_sma200", "G2_tsmom_12_1", "G3_dual_top3", "G4_blend"):
        w = weights_at(kind, c, 399)
        assert w.sum() <= 1.0 + 1e-9 and (w <= 1 / 3 + 1e-9).all() and (w >= 0).all()


def test_dual_momentum_holds_at_most_three_positive_assets():
    idx = pd.bdate_range("2007-01-01", periods=200)
    c = pd.DataFrame({s: np.linspace(100, 100 + k, 200) for s, k in zip("ABCDE", (50, 40, 30, 20, -10))}, index=idx)
    w = weights_at("G3_dual_top3", c, 199)
    assert sorted(w[w > 0].index) == ["A", "B", "C"]


def test_no_lookahead_future_data_cannot_change_a_weight():
    c = frame(400)
    w1 = weights_at("G4_blend", c, 300)
    c2 = c.copy()
    c2.iloc[301:] *= 5
    assert weights_at("G4_blend", c2, 300).equals(w1)


def test_spy_buy_and_hold_costs_once_and_tracks_the_asset():
    c = frame(300, drift=0.0005)
    r = backtest("SPY", c, cost=0.0005)
    gross = (c["SPY"].iloc[-1] / c["SPY"].iloc[22] - 1)
    net = (1 + r.iloc[23:]).prod() - 1
    assert net == pytest.approx(gross, rel=0.05, abs=0.05)


def test_costs_lower_returns():
    c = frame(500, drift=0.001)
    assert backtest("G4_blend", c, 0.001).sum() < backtest("G4_blend", c, 0.0).sum()


def test_unknown_rule_raises():
    with pytest.raises(ValueError):
        weights_at("nope", frame(300), 299)


def test_stats_on_a_known_series():
    r = pd.Series(0.001, index=pd.bdate_range("2008-01-01", periods=252))
    r.iloc[::2] = 0.002
    s = stats(r)
    assert s.max_dd == 0.0 and s.sharpe > 0 and s.cagr > 0.3


def test_subperiod_cagrs_one_per_period():
    r = pd.Series(0.0004, index=pd.bdate_range("2008-01-01", "2025-12-31"))
    assert len(subperiod_cagrs(r)) == 3 and all(c > 0 for c in subperiod_cagrs(r))


def test_dsr_more_trials_lowers_confidence_and_needs_inputs():
    srs3 = [0.02, 0.05, 0.08]
    srs8 = [0.02, 0.05, 0.08, 0.01, 0.09, 0.03, 0.06, 0.04]
    a = deflated_sharpe_prob(0.06, 4000, 0.0, 3.0, srs3)
    b = deflated_sharpe_prob(0.06, 4000, 0.0, 3.0, srs8)
    assert 0 < b < a < 1
    with pytest.raises(ValueError):
        deflated_sharpe_prob(0.06, 4000, 0.0, 3.0, [0.05])
    assert math.isfinite(a)
