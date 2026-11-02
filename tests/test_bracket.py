import pytest
from fakes import CLOSED_NOW, OPEN_NOW, SPY, FakeIB

from tempo.bracket import confirm_bracket, place_bracket, plan_bracket
from tempo.journal import Journal
from tempo.orders import Limits, OrderRefused
from tempo.risk import RiskRules
from tempo.state import set_mode

RULES = RiskRules(risk_per_trade_pct=2.0, max_position_pct=50.0)
LIMITS = Limits(max_position_pct=50.0)


@pytest.fixture
def env(tmp_path):
    return dict(journal=Journal(tmp_path / "j.jsonl"), limits=LIMITS, equity_usd=100_000.0,
                state_path=tmp_path / "state.json", now=OPEN_NOW)


def test_plan_sizes_from_risk_rules():
    plan = plan_bracket(100_000.0, entry=100.0, stop=98.0, take_profit=106.0, rules=RULES)
    assert plan.qty == 500  # 2% of 100k = 2000 risk / 2 per share = 1000, capped at 50k / 100 = 500
    assert (plan.stop, plan.take_profit) == (98.0, 106.0)


def test_plan_qty_override_cannot_exceed_the_rules():
    assert plan_bracket(100_000.0, 100.0, 98.0, None, RULES, qty=3).qty == 3
    with pytest.raises(ValueError, match="exceeds"):
        plan_bracket(100_000.0, 100.0, 98.0, None, RULES, qty=501)


@pytest.mark.parametrize("stop,tp", [(100.0, None), (101.0, None), (0.0, None), (98.0, 100.0), (98.0, 99.0)])
def test_plan_rejects_bad_stop_or_take_profit(stop, tp):
    with pytest.raises(ValueError):
        plan_bracket(100_000.0, 100.0, stop, tp, RULES)


def test_plan_needs_a_stop():
    with pytest.raises(TypeError):
        plan_bracket(100_000.0, 100.0, take_profit=None, rules=RULES)


def test_place_bracket_sends_parent_then_oca_children_with_correct_flags(env):
    ib = FakeIB(fill_seq=[True, False, False])
    plan = plan_bracket(100_000.0, 100.0, 98.0, 106.0, RULES, qty=2)
    legs = place_bracket(ib, SPY, plan, **env)
    parent, tp, stop = ib.placed
    assert (parent.orderType, parent.action, parent.transmit) == ("MKT", "BUY", False)
    assert (tp.orderType, tp.action, tp.lmtPrice, tp.tif, tp.transmit) == ("LMT", "SELL", 106.0, "GTC", False)
    assert (stop.orderType, stop.action, stop.auxPrice, stop.tif, stop.transmit) == ("STP", "SELL", 98.0, "GTC", True)
    assert tp.parentId == stop.parentId == parent.orderId
    assert tp.ocaGroup == stop.ocaGroup != "" and tp.ocaType == stop.ocaType == 1
    assert len({parent.orderId, tp.orderId, stop.orderId}) == 3
    assert legs.parent.orderStatus.status == "Filled"


def test_bracket_without_take_profit_has_only_parent_and_stop(env):
    ib = FakeIB(fill_seq=[True, False])
    place_bracket(ib, SPY, plan_bracket(100_000.0, 100.0, 98.0, None, RULES, qty=1), **env)
    assert [o.orderType for o in ib.placed] == ["MKT", "STP"]
    assert ib.placed[1].transmit is True


def test_bracket_entry_obeys_reduce_only_and_market_hours(env):
    plan = plan_bracket(100_000.0, 100.0, 98.0, None, RULES, qty=1)
    set_mode("reduce_only", "t", env["state_path"])
    ib = FakeIB()
    with pytest.raises(OrderRefused):
        place_bracket(ib, SPY, plan, **env)
    set_mode("normal", "t", env["state_path"])
    with pytest.raises(OrderRefused, match="closed"):
        place_bracket(ib, SPY, plan, **{**env, "now": CLOSED_NOW})
    assert ib.placed == []


def test_failure_midway_cancels_every_leg_already_sent(env):
    ib = FakeIB(fill=False)
    real = ib.placeOrder
    calls = []

    def flaky(contract, order):
        calls.append(order)
        if len(calls) == 3:
            raise ConnectionError("dropped")
        return real(contract, order)

    ib.placeOrder = flaky
    with pytest.raises(ConnectionError):
        place_bracket(ib, SPY, plan_bracket(100_000.0, 100.0, 98.0, 106.0, RULES, qty=1), **env)
    assert [t.orderStatus.status for t in ib.trades] == ["Cancelled", "Cancelled"]


def placed(ib, env, **plan_kw):
    plan = plan_bracket(100_000.0, 100.0, 98.0, 106.0, RULES, qty=2)
    return place_bracket(ib, SPY, plan, **env)


def test_confirm_marks_resting_children_working_and_closes_the_journal(env):
    ib = FakeIB(fill_seq=[True, False, False])
    legs = placed(ib, env)
    checks = confirm_bracket(ib, legs, journal=env["journal"], limits=LIMITS, state_path=env["state_path"], now=OPEN_NOW)
    assert all(c.ok for c in checks) and [c.name for c in checks] == ["entry", "stop"]
    assert env["journal"].unresolved() == []


def test_confirm_cancels_every_leg_when_the_entry_does_not_fill(env):
    ib = FakeIB(fill=False)
    legs = placed(ib, env)
    checks = confirm_bracket(ib, legs, journal=env["journal"], limits=LIMITS, state_path=env["state_path"],
                             now=OPEN_NOW, wait_seconds=1)
    assert not checks[0].ok
    assert [t.orderStatus.status for t in ib.trades] == ["Cancelled"] * 3
    assert env["journal"].unresolved() == []


def test_confirm_flattens_when_the_stop_is_not_resting(env):
    ib = FakeIB(fill_seq=[True, False, False])
    legs = placed(ib, env)
    legs.stop.orderStatus.status = "Inactive"  # the stop was rejected after the entry filled
    checks = confirm_bracket(ib, legs, journal=env["journal"], limits=LIMITS, state_path=env["state_path"], now=OPEN_NOW)
    assert any("UNPROTECTED" in c.detail for c in checks)
    assert ib.held["SPY"] == 0  # the position was closed
