import pytest

from tempo.portfolio_view import MIN_DAYS, blend, correlation, daily_returns, effective_bets, render, trading_days


def score(source, entry, exit_, net, sid=None):
    return {"signal_id": sid or f"{source}:{entry}", "source": source, "entry_date": entry, "exit_date": exit_, "net_excess": net}


def test_trading_days_skip_weekends_and_the_thanksgiving_holiday():
    assert trading_days("2026-11-20", "2026-11-30") == ["2026-11-20", "2026-11-23", "2026-11-24", "2026-11-25", "2026-11-27", "2026-11-30"]


def test_a_trade_is_spread_evenly_over_its_open_days_and_overlapping_trades_are_averaged():
    r = daily_returns([score("a", "2026-11-16", "2026-11-18", 0.03), score("a", "2026-11-17", "2026-11-18", 0.02, sid="a:2")])
    assert r["a"] == pytest.approx({"2026-11-16": 0.01, "2026-11-17": (0.01 + 0.01) / 2, "2026-11-18": (0.01 + 0.01) / 2})


def test_sources_are_kept_apart_and_idle_days_are_absent():
    r = daily_returns([score("a", "2026-11-16", "2026-11-16", 0.01), score("b", "2026-11-18", "2026-11-18", -0.02)])
    assert set(r) == {"a", "b"} and list(r["a"]) == ["2026-11-16"] and r["b"] == {"2026-11-18": -0.02}


def test_a_trade_with_no_trading_day_in_its_span_is_an_error():
    with pytest.raises(ValueError):
        daily_returns([score("a", "2026-11-21", "2026-11-22", 0.01)])          # a weekend


def series(values, start=0):
    return {f"d{n + start:03d}": v for n, v in enumerate(values)}


def test_correlation_is_plus_or_minus_one_for_a_line_and_none_without_overlap_or_variance():
    a = series([0.01 * n for n in range(20)])
    assert correlation(a, series([2 * v + 1 for v in a.values()])) == pytest.approx(1.0)
    assert correlation(a, series([-v for v in a.values()])) == pytest.approx(-1.0)
    assert correlation(a, series([0.1] * 20)) is None                            # no variance
    assert correlation(a, series([0.1, 0.2] * 10, start=15)) is None             # only 5 common days


def test_effective_bets_hand_worked_cases():
    names = ["a", "b", "c"]
    assert effective_bets({("a", "b"): 1.0, ("a", "c"): 1.0, ("b", "c"): 1.0}, names) == pytest.approx(1.0)
    assert effective_bets({("a", "b"): 0.0, ("a", "c"): 0.0, ("b", "c"): 0.0}, names) == pytest.approx(3.0)
    assert effective_bets({("a", "b"): 0.5, ("a", "c"): 0.5, ("b", "c"): 0.5}, names) == pytest.approx(2.0)     # 9 / (3 + 6 x 0.25)
    assert effective_bets({("a", "b"): -0.5, ("a", "c"): 0.5, ("b", "c"): 0.5}, names) == pytest.approx(2.0)     # sign does not matter
    assert effective_bets({("a", "b"): 0.5, ("a", "c"): None, ("b", "c"): 0.5}, names) is None                  # never assume zero
    assert effective_bets({}, ["a"]) is None


def test_blend_weights_are_inverse_volatility_and_a_flat_day_adds_nothing():
    quiet = series([0.01, -0.01] * 6)                       # sd 1%
    loud = series([0.02, -0.02] * 5, start=1)               # sd 2%, open one day later, one pair shorter
    weights, daily = blend({"quiet": quiet, "loud": loud, "new": series([0.01] * 3)})     # "new" has too few days: left out
    assert set(weights) == {"quiet", "loud"} and sum(weights.values()) == pytest.approx(1.0)
    assert weights["quiet"] == pytest.approx(2 / 3) and weights["loud"] == pytest.approx(1 / 3)
    assert daily["d000"] == pytest.approx(weights["quiet"] * 0.01)              # loud is flat that day
    assert daily["d001"] == pytest.approx(weights["quiet"] * -0.01 + weights["loud"] * 0.02)


def test_nothing_is_blended_below_the_minimum_number_of_days():
    assert blend({"a": series([0.01, 0.02, 0.03])}) == ({}, {})
    assert MIN_DAYS == 10 and "no blend" in render({"a": series([0.01, 0.02, 0.03])})


def test_render_shows_blend_correlation_and_effective_bets():
    a = series([0.01 * ((-1) ** n) for n in range(12)])
    b = series([0.02 * ((-1) ** n) for n in range(12)])
    text = render({"a": a, "b": b})
    assert "BLEND (equal risk)" in text and "a / b: +1.00" in text and "effective independent bets: 1.0 of 2" in text
