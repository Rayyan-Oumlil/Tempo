import pytest

from tempo.exposure import Hedge, beta_exposure, check_sector_cap, hedge_order, net_within_cap


def pos(sym, notional, beta=1.0, sector="tech"):
    return {"symbol": sym, "notional": notional, "beta": beta, "sector": sector}


def test_net_cap_is_ten_percent_of_equity_either_side():
    assert net_within_cap([pos("A", 1900), pos("B", -200)], 20_000)          # net 1,700
    assert net_within_cap([pos("A", 2000)], 20_000)                           # exactly 10%
    assert not net_within_cap([pos("A", 2001)], 20_000)
    assert not net_within_cap([pos("A", -3000), pos("B", 500)], 20_000)
    with pytest.raises(ValueError):
        net_within_cap([], 0)


def test_beta_exposure_weights_each_position():
    assert beta_exposure([pos("A", 1000, 1.5), pos("B", -500, 2.0)]) == pytest.approx(500.0)


def test_hedge_sells_spy_against_long_beta_and_buys_against_short_beta():
    assert hedge_order([pos("A", 3000, 1.2)], 20_000) == Hedge("SELL", pytest.approx(3600.0))
    assert hedge_order([pos("A", -3000, 1.0)], 20_000) == Hedge("BUY", pytest.approx(3000.0))


def test_a_tiny_residual_beta_gets_no_hedge_ticket():
    assert hedge_order([pos("A", 1000, 1.0), pos("B", -900, 1.0)], 20_000) is None      # 100 USD < 1% of equity
    assert hedge_order([pos("A", 1000, 1.0), pos("B", -800, 1.0)], 20_000) == Hedge("SELL", pytest.approx(200.0))


def test_after_the_hedge_the_beta_is_zero():
    book = [pos("A", 3000, 1.2), pos("B", -1000, 0.8), pos("C", 500, 2.0)]
    h = hedge_order(book, 20_000)
    assert h is not None
    spy = {"symbol": "SPY", "notional": -h.notional if h.side == "SELL" else h.notional, "beta": 1.0}
    assert beta_exposure(book + [spy]) == pytest.approx(0.0)


def test_missing_or_non_finite_inputs_are_errors_not_defaults():
    with pytest.raises(ValueError):
        beta_exposure([{"symbol": "A", "notional": 100.0, "beta": None}])
    with pytest.raises(ValueError):
        beta_exposure([pos("A", float("nan"))])
    with pytest.raises(ValueError):
        check_sector_cap([{"symbol": "A", "notional": 100.0, "beta": 1.0}])


def test_sector_cap_uses_gross_share_and_names_offenders():
    book = [pos("A", 1000, sector="tech"), pos("B", -1000, sector="tech"), pos("C", 1000, sector="energy"), pos("D", 5000, sector="bank"),
            pos("E", 2000, sector="health")]
    # gross 10,000: tech 20%, energy 10%, bank 50%, health 20%
    assert check_sector_cap(book) == ["bank 50%", "health 20%", "tech 20%"]
    assert check_sector_cap([pos("A", 150, sector="x"), pos("B", 850, sector="y")]) == ["y 85%"]
    assert check_sector_cap([]) == []
    equal = [pos(str(i), 100, sector=f"s{i}") for i in range(7)]                  # 1/7 = 14.3% each, under the cap
    assert check_sector_cap(equal) == []
