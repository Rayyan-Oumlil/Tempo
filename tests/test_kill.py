import pytest
from fakes import CLOSED_NOW, OPEN_NOW, SPY, FakeIB
from ib_async import LimitOrder

from tempo.flatten import flatten_positions
from tempo.journal import Journal
from tempo.kill import kill
from tempo.orders import Limits
from tempo.state import get_mode

LIMITS = Limits(max_position_pct=50.0)


@pytest.fixture
def env(tmp_path):
    return {"journal": Journal(tmp_path / "j.jsonl"), "state_path": tmp_path / "state.json", "limits": LIMITS}


def ok(checks):
    return all(c.ok for c in checks)


def test_flatten_closes_longs_and_shorts(env):
    ib = FakeIB(positions={"SPY": 3, "QQQ": -2})
    checks = flatten_positions(ib, now=OPEN_NOW, **env)
    assert ok(checks) and ib.held["SPY"] == 0 and ib.held["QQQ"] == 0
    assert {o.action for o in ib.placed} == {"SELL", "BUY"}


def test_flatten_one_symbol_leaves_others(env):
    ib = FakeIB(positions={"SPY": 3, "QQQ": 2})
    flatten_positions(ib, symbol="SPY", now=OPEN_NOW, **env)
    assert ib.held["SPY"] == 0 and ib.held["QQQ"] == 2


def test_flatten_cancels_resting_orders_for_the_symbol_first(env):
    ib = FakeIB(positions={"SPY": 3}, fill=False)
    stop = ib.placeOrder(SPY, LimitOrder("SELL", 3, 150.0))  # a resting protective order
    ib.fill = True
    flatten_positions(ib, now=OPEN_NOW, **env)
    assert stop.orderStatus.status == "Cancelled" and ib.held["SPY"] == 0


def test_flatten_with_nothing_open_is_a_pass(env):
    assert ok(flatten_positions(FakeIB(), now=OPEN_NOW, **env))


def test_flatten_reports_failure_when_orders_never_fill(env):
    ib = FakeIB(positions={"SPY": 3}, fill=False)
    checks = flatten_positions(ib, now=OPEN_NOW, wait_seconds=1, **env)
    assert not ok(checks)


def test_kill_sets_reduce_only_cancels_all_and_flattens(env):
    ib = FakeIB(positions={"SPY": 3}, fill=False)
    resting = ib.placeOrder(SPY, LimitOrder("BUY", 1, 50.0))
    ib.fill = True
    checks = kill(ib, now=OPEN_NOW, **env)
    assert ok(checks)
    assert ib.global_cancels == 1 and resting.orderStatus.status == "Cancelled"
    assert ib.held["SPY"] == 0
    assert get_mode(env["state_path"]) == "reduce_only"


def test_kill_when_market_closed_cancels_but_reports_positions_remain(env):
    ib = FakeIB(positions={"SPY": 3})
    checks = kill(ib, now=CLOSED_NOW, **env)
    assert not ok(checks)
    assert any("market closed" in c.detail for c in checks if not c.ok)
    assert ib.held["SPY"] == 3 and ib.global_cancels == 1
    assert get_mode(env["state_path"]) == "reduce_only"


# --- review finding: if a cancel is not confirmed, say exactly why nothing was sold ---

def test_flatten_reports_the_exact_reason_when_a_cancel_is_not_confirmed(env):
    ib = FakeIB(positions={"SPY": 3}, fill=False)
    stop = ib.placeOrder(SPY, LimitOrder("SELL", 3, 150.0))   # a resting exit
    ib.cancelOrder = lambda order: None                        # the cancel never takes effect
    ib.fill = True
    checks = flatten_positions(ib, now=OPEN_NOW, **env)
    failed = [c for c in checks if not c.ok]
    assert failed and "cancel not confirmed" in failed[0].detail and "1 order" in failed[0].detail
    assert len(ib.placed) == 1 and ib.held["SPY"] == 3         # nothing was sold: it could have flipped the account short
    assert stop.orderStatus.status == "Submitted"


def test_kill_with_a_sticky_order_still_cancels_what_it_can_and_names_the_problem(env):
    ib = FakeIB(positions={"SPY": 3}, fill=False)
    ib.placeOrder(SPY, LimitOrder("SELL", 3, 150.0))
    ib.reqGlobalCancel = lambda: None
    ib.cancelOrder = lambda order: None
    ib.fill = True
    checks = kill(ib, now=OPEN_NOW, **env)
    assert not all(c.ok for c in checks)
    assert any("still open" in c.detail for c in checks if c.name == "cancel")
    assert any("cancel not confirmed" in c.detail for c in checks)
    assert ib.held["SPY"] == 3
