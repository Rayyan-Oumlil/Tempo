import math
from datetime import date

import pytest

from tempo.option_snapshot import good, pick_expiries, pick_strikes, realized_vol, valid_share

TODAY = date(2026, 11, 11)


def test_expiries_are_the_nearest_to_each_target_and_never_today_or_past():
    listed = ["20261111", "20261113", "20261116", "20261120", "20261211", "20261218", "20270116", "20270115"]
    assert pick_expiries(listed, TODAY) == ["20261116", "20261211", "20270115"]   # 5d, 30d, 65d: nearest to 7, 30, 60 days
    assert pick_expiries(["20261111", "20261110"], TODAY) == []                    # nothing in the future
    assert pick_expiries(["20261113"], TODAY) == ["20261113"]                       # one listing serves every target once


def test_strikes_are_the_listed_ones_nearest_to_minus5_atm_plus5_percent():
    strikes = [float(k) for k in range(700, 800)]
    assert pick_strikes(strikes, 757.1) == [720.0, 755.0, 795.0]   # 5-point strikes only
    assert pick_strikes([757.0], 757.1) == [757.0]                                  # a sparse chain collapses duplicates


def test_realized_vol_matches_a_hand_computation_and_needs_enough_history():
    closes = [100.0 * (1.01 if i % 2 else 1.0) for i in range(22)]                  # alternating +1%, -1% style moves
    rv = realized_vol(closes, 20)
    assert rv is not None and 0.15 < rv < 0.17   # daily moves of about 1% are about 16% a year
    assert realized_vol([100.0] * 25) == 0.0
    assert realized_vol([100.0] * 20, 20) is None
    r = [math.log(closes[i] / closes[i - 1]) for i in range(2, 22)]
    mean = sum(r) / 20
    assert rv == pytest.approx(math.sqrt(sum((x - mean) ** 2 for x in r) / 19) * math.sqrt(252))


@pytest.mark.parametrize("raw, expected", [(0.12, 0.12), (-1, None), (float("nan"), None), (None, None), ("x", None), (0, None)])
def test_good_filters_ibkr_non_values(raw, expected):
    assert good(raw) == expected


def test_valid_share_counts_contracts_with_an_implied_vol():
    assert valid_share([{"iv": 0.1}, {"iv": None}, {"iv": 0.2}, {"iv": 0.3}]) == 0.75
    assert valid_share([]) == 0.0
