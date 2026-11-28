import numpy as np
import pandas as pd

from tempo import history_w as w


def test_vix_rule_holds_only_in_contango_and_a_missing_close_means_cash():
    i = pd.bdate_range("2020-01-01", periods=4)
    vix = pd.Series([15.0, 25.0, 18.0, 15.0], i)
    vix3m = pd.Series([18.0, 22.0, 18.0], i[:3])
    assert list(w.vix_weights(vix, vix3m, i)["SPY"]) == [1.0, 0.0, 0.0, 0.0]


def test_sector_momentum_picks_top_three_and_skips_the_latest_month():
    i = pd.bdate_range("2020-01-01", "2021-06-30")
    steps = {"A": 0.004, "B": 0.003, "C": 0.002, "D": -0.001, "E": 0.0}
    closes = pd.DataFrame({k: 100 * (1 + v) ** np.arange(len(i)) for k, v in steps.items()}, index=i)
    closes.loc["2021-06-01":, "D"] *= 10  # a jump inside the skipped month must not count
    last = w.sector_weights(closes).loc["2021-06-30"]
    assert [k for k in last.index if last[k] > 0] == ["A", "B", "C"]
    assert abs(last.sum() - 1) < 1e-9


def test_sector_momentum_changes_only_at_month_end_and_starts_in_cash():
    i = pd.bdate_range("2020-01-01", "2021-12-31")
    rng = np.random.default_rng(1)
    closes = pd.DataFrame(100 * np.cumprod(1 + rng.normal(0, 0.02, (len(i), 5)), axis=0), index=i, columns=list("ABCDE"))
    weights = w.sector_weights(closes)
    assert weights.loc[:"2021-01-28"].to_numpy().sum() == 0
    assert weights.loc["2021-01-29"].sum() > 0.99
    changed = weights.diff().abs().sum(axis=1) > 0
    month_ends = set(pd.Series(i, index=i).groupby([i.year, i.month]).max())
    assert set(changed[changed].index) <= month_ends


def test_gold_rule_compares_with_63_trading_days_earlier():
    i = pd.bdate_range("2020-01-01", periods=70)
    falling = w.gold_weights(pd.Series(np.linspace(2.0, 1.0, 70), i), i)["GLD"]
    assert falling.iloc[62] == 0.0 and falling.iloc[63] == 1.0
    assert w.gold_weights(pd.Series(np.linspace(1.0, 2.0, 70), i), i)["GLD"].sum() == 0.0


def test_gold_rule_uses_the_last_published_yield_on_a_bond_holiday():
    i = pd.bdate_range("2020-01-01", periods=70)
    y = pd.Series(np.linspace(2.0, 1.0, 70), i).drop(i[65])
    assert w.gold_weights(y, i)["GLD"].iloc[65] == 1.0


def test_every_check_can_fail_the_verdict():
    good = dict(excess=0.8, bench_excess=[0.5, 0.6], dsr=0.97, dd=-0.2, bench_dd=-0.5, subs=[0.1, 0.1, 0.1], stress_excess=0.5)
    assert w.judge(**good)[0]
    bad = {"excess": 0.55, "dsr": 0.9, "dd": -0.6, "subs": [0.1, -0.01, 0.1], "stress_excess": 0.2}
    for key, value in bad.items():
        assert not w.judge(**{**good, key: value})[0], key


def test_trial_list_is_the_19_the_protocol_names():
    assert len(w.trial_sharpes([0.01, 0.02, 0.03])) == 19
