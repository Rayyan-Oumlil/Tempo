import re
from pathlib import Path

import pytest
from fakes import OPEN_NOW, SPY, FakeIB
from ib_async import LimitOrder, MarketOrder

from tempo.bracket import place_bracket, plan_bracket
from tempo.flatten import flatten_positions
from tempo.journal import Journal
from tempo.kill import kill
from tempo.orders import Limits, is_exit, place
from tempo.risk import RiskRules

ROOT = Path(__file__).resolve().parents[2]
LIMITS = Limits(max_position_pct=50.0)


@pytest.fixture
def env(tmp_path):
    return {"journal": Journal(tmp_path / "j.jsonl"), "state_path": tmp_path / "state.json", "limits": LIMITS}


def test_1_only_orders_py_sends_orders_to_the_broker():
    offenders = []
    for path in (ROOT / "tempo").glob("*.py"):
        if path.name != "orders.py" and re.search(r"\.placeOrder\(", path.read_text(encoding="utf-8")):
            offenders.append(path.name)
    assert offenders == []


def test_2_the_intent_is_on_disk_before_the_broker_is_called(env):
    ib = FakeIB()
    seen_at_send = []
    real = ib.placeOrder

    def spy(contract, order):
        seen_at_send.append([r["kind"] for r in env["journal"].records() if r.get("ref") == order.orderRef])
        return real(contract, order)

    ib.placeOrder = spy
    place(ib, SPY, MarketOrder("BUY", 1), reason="t", equity_usd=100_000.0, ref_price=100.0, now=OPEN_NOW, **env)
    assert seen_at_send == [["intent"]]


def test_3_a_live_account_never_reaches_the_broker_through_any_tool(env):
    ib = FakeIB(account="U1234567", positions={"SPY": 3})
    ib.placeOrder = lambda *a: pytest.fail("a live account reached placeOrder")
    plan = plan_bracket(100_000.0, 100.0, 98.0, None, RiskRules(2.0, 50.0, 5.0), qty=1)
    with pytest.raises(RuntimeError, match="not a paper account"):
        place(ib, SPY, MarketOrder("BUY", 1), reason="t", equity_usd=1e5, ref_price=100.0, now=OPEN_NOW, **env)
    with pytest.raises(RuntimeError, match="not a paper account"):
        place_bracket(ib, SPY, plan, equity_usd=1e5, now=OPEN_NOW, **env)
    with pytest.raises(RuntimeError, match="not a paper account"):
        flatten_positions(ib, now=OPEN_NOW, **env)  # fails loudly instead of trading
    assert ib.held["SPY"] == 3


def test_4_a_bracket_cannot_be_built_without_a_stop():
    with pytest.raises(TypeError):
        plan_bracket(100_000.0, 100.0, take_profit=None, rules=RiskRules(2.0, 50.0, 5.0))
    for bad_stop in (0.0, -1.0, 100.0, 101.0):
        with pytest.raises(ValueError):
            plan_bracket(100_000.0, 100.0, bad_stop, None, RiskRules(2.0, 50.0, 5.0))


@pytest.mark.parametrize("held", [1, 2, 7, 100, -1, -5, -100])
def test_5_flatten_trades_the_opposite_side_for_exactly_the_held_size(env, held):
    ib = FakeIB(positions={"SPY": held})
    flatten_positions(ib, now=OPEN_NOW, **env)
    assert [(o.action, o.totalQuantity) for o in ib.placed] == [("SELL" if held > 0 else "BUY", abs(held))]
    assert ib.held["SPY"] == 0


def test_5b_kill_never_leaves_a_position_on_the_other_side(env):
    ib = FakeIB(positions={"SPY": 4, "QQQ": -3})
    kill(ib, now=OPEN_NOW, **env)
    assert all(q == 0 for q in ib.held.values())


@pytest.mark.parametrize("held", [-6, -1, 0, 1, 6])
@pytest.mark.parametrize("committed", [0, 2, 6])
@pytest.mark.parametrize("qty", [1, 2, 4, 6, 7])
@pytest.mark.parametrize("action", ["BUY", "SELL"])
def test_6_an_order_is_an_exit_only_if_it_fits_in_the_uncommitted_part_of_the_position(held, committed, qty, action):
    ib = FakeIB(positions={"SPY": held}, fill=False)
    if committed:
        ib.placeOrder(SPY, LimitOrder(action, committed, 1.0))  # resting order on the same side
    room = (held if action == "SELL" else -held) - committed
    assert is_exit(ib, SPY, MarketOrder(action, qty)) == (room > 0 and qty <= room)
