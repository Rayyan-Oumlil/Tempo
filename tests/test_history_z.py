import pandas as pd

from tempo import history_z as z


def test_turn_of_month_days_are_last_day_and_first_three():
    idx = pd.bdate_range("2024-01-01", "2024-03-29")
    flags = z.turn_of_month_days(idx)
    jan = idx[idx.month == 1]
    feb = idx[idx.month == 2]
    assert flags[jan[-1]] and flags[feb[0]] and flags[feb[1]] and flags[feb[2]]
    assert not flags[feb[3]] and not flags[jan[-2]]


def test_turn_of_month_invested_share_is_about_a_fifth():
    idx = pd.bdate_range("2010-01-01", "2020-12-31")
    assert 0.15 < z.turn_of_month_days(idx).mean() < 0.25


def test_turn_of_month_run_pays_cost_on_entry_and_earns_cash_off_days():
    idx = pd.bdate_range("2024-01-01", "2024-02-29")
    closes = pd.Series(100.0, index=idx)
    cash = pd.Series(0.0001, index=idx)
    r = z.turn_of_month_run(closes, cash, 0.0005)
    off = idx[(idx.month == 1) & ~z.turn_of_month_days(idx).to_numpy()]
    assert (r[off[1:]] == 0.0001).all()
    assert r.min() < 0  # entry/exit cost shows up on a flat price


def test_equal_subperiods_cover_range_without_overlap():
    subs = z.equal_subperiods(pd.Timestamp("2018-11-09"), pd.Timestamp("2025-12-31"))
    assert subs[0][0] == "2018-11-09" and subs[-1][1] == "2025-12-31"
    for (_, b), (a, _) in zip(subs, subs[1:]):
        assert pd.Timestamp(a) == pd.Timestamp(b) + pd.Timedelta(days=1)


def test_buy_hold_with_entry_charges_cost_once():
    r = z.buy_hold_with_entry(pd.Series([100.0, 101.0, 102.0]), 0.001)
    assert r.iloc[0] == -0.001 and abs(r.iloc[1] - 0.01) < 1e-12


def test_prior_trials_list_has_eleven_entries():
    assert len(z.prior_daily_sharpes()) == 11
