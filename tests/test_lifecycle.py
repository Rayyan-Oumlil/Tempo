import pytest
from fakes import CLOSED_NOW, OPEN_NOW, SPY, FakeIB

from tempo.journal import Journal
from tempo.lifecycle import cash_delta, round_trip_pnl, run_lifecycle
from tempo.orders import Limits

LIMITS = Limits(max_position_pct=50.0)


def test_round_trip_pnl_subtracts_both_commissions():
    pnl = round_trip_pnl(buy_price=760.64, sell_price=759.53, qty=1, commissions=2.04)
    assert pnl.gross == pytest.approx(-1.11)
    assert pnl.net == pytest.approx(-3.15)


def test_round_trip_pnl_scales_with_quantity():
    assert round_trip_pnl(100.0, 101.0, 10, 2.0).net == pytest.approx(8.0)


def test_round_trip_pnl_rejects_bad_quantity():
    with pytest.raises(ValueError):
        round_trip_pnl(100.0, 101.0, 0, 0.0)


def test_cash_delta_per_currency_including_new_and_removed():
    before = {"CAD": 1000.0, "USD": 0.0}
    after = {"CAD": 940.0, "USD": 5.0, "EUR": 1.0}
    assert cash_delta(before, after) == {"CAD": -60.0, "USD": 5.0, "EUR": 1.0}


@pytest.fixture
def env(tmp_path):
    return dict(journal=Journal(tmp_path / "j.jsonl"), limits=LIMITS, equity_usd=100_000.0, ref_price=100.0,
                state_path=tmp_path / "state.json", now=OPEN_NOW)


def test_happy_path_buys_then_sells_and_reports_pnl(env):
    ib = FakeIB()
    result = run_lifecycle(ib, SPY, 1, **env)
    assert [o.action for o in ib.placed] == ["BUY", "SELL"]
    assert result.pnl.net == pytest.approx(0.0 - 2.0)  # same fake price both ways, 1.00 commission per leg
    assert all(c.ok for c in result.checks)
    assert env["journal"].unresolved() == []  # every intent got an outcome


def test_unfilled_buy_is_cancelled_and_never_sells(env):
    ib = FakeIB(fill=False)
    result = run_lifecycle(ib, SPY, 1, **env)
    assert [o.action for o in ib.placed] == ["BUY"]
    assert ib.trades[0].orderStatus.status == "Cancelled"
    assert result.pnl is None and not all(c.ok for c in result.checks)


def test_unfilled_sell_is_cancelled_and_reported_as_still_long(env):
    ib = FakeIB(fill_seq=[True, False])
    result = run_lifecycle(ib, SPY, 1, **env)
    assert [o.action for o in ib.placed] == ["BUY", "SELL"]
    assert ib.trades[1].orderStatus.status == "Cancelled"
    assert result.pnl is None
    assert any("still long" in c.detail for c in result.checks if not c.ok)


def test_refused_buy_is_reported_not_raised(env):
    ib = FakeIB()
    result = run_lifecycle(ib, SPY, 1, **{**env, "now": CLOSED_NOW})
    assert ib.placed == []
    assert [c.ok for c in result.checks] == [False] and "refused" in result.checks[0].detail
