import math

import pytest
from hypothesis import given, strategies as st

from tempo.sizing import Sizing, SizingRules, size_position

R = SizingRules(target_risk_pct=0.3, floor_pct=4.0)          # at 20,000: risk 60 USD, floor 800 USD, cap 3,000 USD


def test_hand_worked_cases_at_20000():
    assert size_position(20_000, 50.0, 0.04, R) == Sizing(30, 1500.0, "sized")        # 60/0.04 = 1,500
    assert size_position(20_000, 50.0, 0.01, R) == Sizing(60, 3000.0, "capped")       # 60/0.01 = 6,000 -> cap 3,000
    assert size_position(20_000, 50.0, 0.20, R) == Sizing(0, 0.0, "skip_below_floor") # 60/0.20 = 300 < 800: skipped, not shrunk


def test_a_price_above_the_notional_gives_zero_shares_and_a_skip():
    assert size_position(20_000, 5_000.0, 0.04, R).status == "skip_below_floor"


def test_equal_risk_halves_the_position_when_volatility_doubles():
    a, b = size_position(20_000, 10.0, 0.03, R), size_position(20_000, 10.0, 0.06, R)
    assert (a.notional, b.notional) == (2000.0, 1000.0)


@pytest.mark.parametrize("bad", [0.0, -1.0, math.nan, math.inf])
def test_bad_inputs_skip_instead_of_guessing(bad):
    assert size_position(bad, 10.0, 0.02, R).status == "skip_bad_input"
    assert size_position(20_000, bad, 0.02, R).status == "skip_bad_input"
    assert size_position(20_000, 10.0, bad, R).status == "skip_bad_input"


def test_inconsistent_rules_are_refused():
    for kw in ({"target_risk_pct": 0.0, "floor_pct": 4.0}, {"target_risk_pct": 0.3, "floor_pct": 0.0}, {"target_risk_pct": 0.3, "floor_pct": 20.0}):
        with pytest.raises(ValueError):
            SizingRules(**kw)


@given(equity=st.floats(1_000, 1e7), price=st.floats(1, 2_000), sigma=st.floats(0.002, 0.5))
def test_size_never_exceeds_the_cap_and_never_sits_between_zero_and_the_floor(equity, price, sigma):
    out = size_position(equity, price, sigma, R)
    assert out.notional <= equity * R.max_name_pct / 100 + 1e-6
    assert out.shares == 0 or out.notional >= equity * R.floor_pct / 100 - 1e-6
    assert (out.shares == 0) == (out.status in ("skip_below_floor", "skip_bad_input"))
