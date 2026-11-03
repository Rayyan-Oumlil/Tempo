import pytest
from fakes import CLOSED_NOW, OPEN_NOW, SPY, FakeIB
from ib_async import LimitOrder, MarketOrder, StopOrder

from tempo.journal import Journal
from tempo.orders import Limits, OrderRefused, broker_reason, place, record_outcome
from tempo.state import set_mode

LIMITS = Limits(max_position_pct=50.0)


@pytest.fixture
def env(tmp_path):
    return {"journal": Journal(tmp_path / "j.jsonl"), "state_path": tmp_path / "state.json"}


def entry(ib, env, order=None, **kw):
    kw = {"equity_usd": 100_000.0, "ref_price": 100.0, "limits": LIMITS, "now": OPEN_NOW, "reason": "test", **env, **kw}
    return place(ib, SPY, order or MarketOrder("BUY", 10), **kw)


def test_entry_sets_tif_unique_ref_and_journals_intent_then_sent(env):
    ib = FakeIB()
    original = MarketOrder("BUY", 10, orderRef="tempo-test")
    entry(ib, env, original)
    sent = ib.placed[0]
    assert sent.tif == "DAY" and sent.orderRef.startswith("tempo-test-") and sent.orderRef != "tempo-test-"
    assert original.tif == "" and original.orderRef == "tempo-test"  # caller's order is untouched
    assert [r["kind"] for r in env["journal"].records()] == ["intent", "sent"]
    assert env["journal"].records()[0]["ref"] == sent.orderRef


def test_live_account_refused_and_nothing_sent(env):
    ib = FakeIB(account="U1234567")
    with pytest.raises(RuntimeError, match="not a paper account"):
        entry(ib, env)
    assert ib.placed == [] and env["journal"].records() == []


def test_oversize_entry_refused(env):
    with pytest.raises(OrderRefused, match="position cap"):
        entry(FakeIB(), env, MarketOrder("BUY", 1000))  # 100,000 notional vs 50,000 cap


def test_entry_without_equity_or_price_fails_closed(env):
    with pytest.raises(OrderRefused, match="equity"):
        entry(FakeIB(), env, equity_usd=None)
    with pytest.raises(OrderRefused, match="price"):
        entry(FakeIB(), env, ref_price=None)


def test_entry_refused_when_market_closed(env):
    with pytest.raises(OrderRefused, match="market is closed"):
        entry(FakeIB(), env, now=CLOSED_NOW)


def test_entry_allowed_outside_rth_when_order_says_so(env):
    entry(FakeIB(), env, LimitOrder("BUY", 1, 99.0, outsideRth=True), now=CLOSED_NOW)


def test_reduce_only_refuses_entries_but_allows_exits(env):
    set_mode("reduce_only", "test", env["state_path"])
    with pytest.raises(OrderRefused, match="reduce_only"):
        entry(FakeIB(), env)
    ib = FakeIB(positions={"SPY": 10})
    place(ib, SPY, MarketOrder("SELL", 10), reason="exit", now=CLOSED_NOW, limits=LIMITS, **env)  # no equity, closed, still ok
    assert ib.held["SPY"] == 0


def test_cover_of_a_short_is_an_exit(env):
    set_mode("reduce_only", "test", env["state_path"])
    ib = FakeIB(positions={"SPY": -5})
    place(ib, SPY, MarketOrder("BUY", 5), reason="cover", limits=LIMITS, now=OPEN_NOW, **env)
    assert ib.held["SPY"] == 0


def test_oversized_sell_that_would_flip_the_position_is_an_entry(env):
    set_mode("reduce_only", "test", env["state_path"])
    with pytest.raises(OrderRefused):
        place(FakeIB(positions={"SPY": 5}), SPY, MarketOrder("SELL", 6), reason="x", limits=LIMITS, now=OPEN_NOW, **env)


def test_unreadable_positions_means_entry_not_exit(env):
    set_mode("reduce_only", "test", env["state_path"])
    ib = FakeIB(positions={"SPY": 10})
    ib.positions_raise = True
    with pytest.raises(OrderRefused):
        place(ib, SPY, MarketOrder("SELL", 10), reason="x", limits=LIMITS, now=OPEN_NOW, **env)


def test_duplicate_order_inside_window_refused(env):
    ib = FakeIB()
    entry(ib, env)
    with pytest.raises(OrderRefused, match="duplicate"):
        entry(ib, env)
    assert len(ib.placed) == 1


def test_stale_unresolved_intent_blocks_entries_not_exits(env):
    env["journal"].append("intent", ref="old", symbol="SPY")
    env["journal"]._clock = lambda: env["journal"].records()[0]["ts"] + 3600  # an hour later
    with pytest.raises(OrderRefused, match="reconcile"):
        entry(FakeIB(), env, MarketOrder("BUY", 1))
    ib = FakeIB(positions={"SPY": 3})
    place(ib, SPY, MarketOrder("SELL", 3), reason="exit", limits=LIMITS, now=OPEN_NOW, **env)


def test_broker_error_is_journaled_and_reraised(env):
    ib = FakeIB()

    def boom(*_):
        raise ConnectionError("down")

    ib.placeOrder = boom
    with pytest.raises(ConnectionError):
        entry(ib, env)
    kinds = [(r["kind"], r.get("status")) for r in env["journal"].records()]
    assert kinds == [("intent", None), ("outcome", "error")]


def test_record_outcome_closes_the_intent(env):
    ib = FakeIB()
    trade = entry(ib, env)
    record_outcome(env["journal"], trade)
    assert env["journal"].unresolved() == []
    out = env["journal"].records()[-1]
    assert out["status"] == "Filled" and out["filled"] == 10 and out["commission"] == 1.0


def broker_says(ib, trade, code, text="Order rejected - reason: because"):
    ib.errorEvent.emit(trade.order.orderId, code, text)


@pytest.mark.parametrize("code,kind", [(201, "rejected"), (110, "error"), (391, "error")])
def test_broker_reason_classifies_the_error_the_broker_sent(env, code, kind):
    ib = FakeIB(fill=False)
    trade = entry(ib, env)
    broker_says(ib, trade, code)
    assert broker_reason(trade) == {"reason_code": code, "reason_kind": kind, "reason_text": "Order rejected - reason: because"}


def test_no_error_means_no_reason(env):
    assert broker_reason(entry(FakeIB(fill=False), env)) == {}


def test_the_latest_error_wins(env):
    ib = FakeIB(fill=False)
    trade = entry(ib, env)
    broker_says(ib, trade, 110, "off tick")
    broker_says(ib, trade, 201, "rejected")
    assert broker_reason(trade)["reason_code"] == 201


@pytest.mark.parametrize("code", [202, 10349, 2104, 2106])
def test_notices_that_say_nothing_about_the_order_are_ignored(env, code):
    ib = FakeIB(fill=False)
    trade = entry(ib, env)
    broker_says(ib, trade, code, "notice")
    assert broker_reason(trade) == {}


def test_errors_without_an_order_id_are_ignored(env):
    ib = FakeIB(fill=False)
    trade = entry(ib, env)
    ib.errorEvent.emit(-1, 1100, "Connectivity between IB and TWS has been lost")
    assert broker_reason(trade) == {}


def test_errors_of_another_order_are_not_mixed_in(env):
    ib = FakeIB(fill=False)
    first, second = entry(ib, env), entry(ib, env, LimitOrder("BUY", 1, 90.0))
    broker_says(ib, second, 201)
    assert broker_reason(first) == {} and broker_reason(second)["reason_code"] == 201


def test_outcome_of_a_rejected_order_records_why(env):
    ib = FakeIB(fill=False)
    trade = entry(ib, env)
    trade.orderStatus.status = "Inactive"  # what IBKR does with a 201
    broker_says(ib, trade, 201, "Order rejected - reason:insufficient funds")
    record_outcome(env["journal"], trade)
    out = env["journal"].records()[-1]
    assert (out["status"], out["reason_code"], out["reason_kind"]) == ("Inactive", 201, "rejected")
    assert "insufficient funds" in out["reason_text"]


def test_outcome_of_a_filled_order_carries_no_reason_even_after_a_notice(env):
    ib = FakeIB()
    trade = entry(ib, env)  # fills at once
    broker_says(ib, trade, 399, "Order message: warning")
    record_outcome(env["journal"], trade)
    assert "reason_code" not in env["journal"].records()[-1]


def test_the_error_listener_is_attached_once_per_connection(env):
    ib = FakeIB(fill=False)
    entry(ib, env), entry(ib, env, LimitOrder("BUY", 1, 90.0))
    assert len(ib.errorEvent.handlers) == 1


def test_entry_refused_once_the_market_calendar_has_expired(env):
    from datetime import datetime, timezone
    later = datetime(2028, 1, 4, 16, 0, tzinfo=timezone.utc)
    with pytest.raises(OrderRefused, match="calendar"):
        entry(FakeIB(), env, now=later)
    entry(FakeIB(), env, LimitOrder("BUY", 1, 99.0, outsideRth=True), now=later)  # does not depend on the calendar


# --- the cap and the price check use the order's own price, not just the caller's reference price ---

def test_limit_far_above_the_reference_price_is_refused_as_a_fat_finger(env):
    with pytest.raises(OrderRefused, match="reference"):
        entry(FakeIB(), env, LimitOrder("BUY", 10, 500.0))  # reference is 100


def test_short_limit_far_below_the_reference_price_is_refused(env):
    with pytest.raises(OrderRefused, match="reference"):
        entry(FakeIB(), env, LimitOrder("SELL", 10, 80.0))


def test_limit_inside_the_band_and_a_far_passive_limit_are_allowed(env):
    entry(FakeIB(), env, LimitOrder("BUY", 10, 105.0))
    entry(FakeIB(), env, LimitOrder("BUY", 11, 50.0))   # far BELOW the market cannot fill at a bad price (roundtrip uses this)


def test_cap_is_checked_at_the_orders_own_limit_price(env):
    entry(FakeIB(), env, LimitOrder("BUY", 480, 100.0))                       # 48,000 <= 50,000
    with pytest.raises(OrderRefused, match="position cap"):
        entry(FakeIB(), env, LimitOrder("BUY", 481, 109.0))                   # 52,429 at its own price, 48,100 at the reference


def test_cap_is_checked_at_a_stop_orders_trigger_price(env):
    from ib_async import StopOrder
    with pytest.raises(OrderRefused, match="position cap"):
        entry(FakeIB(), env, StopOrder("BUY", 450, 120.0))                    # 54,000 at the stop, 45,000 at the reference


def test_place_refuses_and_sends_nothing_while_another_process_holds_the_journal(env):
    from tempo.journal import JournalLocked
    ib = FakeIB()
    other = Journal(env["journal"].path)
    with other.lock():
        with pytest.raises(JournalLocked):
            entry(ib, {**env, "journal": Journal(env["journal"].path, lock_timeout=0.2)})
    assert ib.placed == []


# --- an exit must fit in what is NOT already committed to other resting exits (found in the limitations review) ---

def test_a_second_resting_exit_that_would_flip_the_position_is_not_an_exit(env):
    set_mode("reduce_only", "t", env["state_path"])
    ib = FakeIB(positions={"SPY": 5}, fill=False)
    first = place(ib, SPY, LimitOrder("SELL", 5, 150.0), reason="exit", limits=LIMITS, now=OPEN_NOW, **env)  # rests
    assert not first.isDone()
    with pytest.raises(OrderRefused, match="reduce_only"):
        place(ib, SPY, LimitOrder("SELL", 1, 151.0), reason="exit", limits=LIMITS, now=OPEN_NOW, **env)
    assert len(ib.placed) == 1


def test_exits_that_fit_together_are_both_allowed_and_cancelling_frees_the_room(env):
    set_mode("reduce_only", "t", env["state_path"])
    ib = FakeIB(positions={"SPY": 5}, fill=False)
    first = place(ib, SPY, LimitOrder("SELL", 3, 150.0), reason="exit", limits=LIMITS, now=OPEN_NOW, **env)
    place(ib, SPY, LimitOrder("SELL", 2, 151.0), reason="exit", limits=LIMITS, now=OPEN_NOW, **env)   # 3 + 2 = 5 fits
    with pytest.raises(OrderRefused):
        place(ib, SPY, LimitOrder("SELL", 1, 152.0), reason="exit", limits=LIMITS, now=OPEN_NOW, **env)
    ib.cancelOrder(first.order)
    place(ib, SPY, LimitOrder("SELL", 3, 153.0), reason="exit", limits=LIMITS, now=OPEN_NOW, **env)   # room is back


def test_resting_orders_on_the_other_side_do_not_use_up_exit_room(env):
    set_mode("reduce_only", "t", env["state_path"])
    ib = FakeIB(positions={"SPY": 5}, fill=False)
    ib.placeOrder(SPY, LimitOrder("BUY", 100, 50.0))        # a resting BUY says nothing about selling
    place(ib, SPY, LimitOrder("SELL", 5, 150.0), reason="exit", limits=LIMITS, now=OPEN_NOW, **env)


def test_covering_a_short_is_limited_the_same_way(env):
    set_mode("reduce_only", "t", env["state_path"])
    ib = FakeIB(positions={"SPY": -4}, fill=False)
    place(ib, SPY, LimitOrder("BUY", 4, 50.0), reason="cover", limits=LIMITS, now=OPEN_NOW, **env)
    with pytest.raises(OrderRefused):
        place(ib, SPY, LimitOrder("BUY", 1, 49.0), reason="cover", limits=LIMITS, now=OPEN_NOW, **env)


def test_unreadable_open_orders_means_not_an_exit(env):
    set_mode("reduce_only", "t", env["state_path"])
    ib = FakeIB(positions={"SPY": 5})
    ib.reqAllOpenOrders = lambda: (_ for _ in ()).throw(RuntimeError("down"))
    with pytest.raises(OrderRefused):
        place(ib, SPY, MarketOrder("SELL", 5), reason="exit", limits=LIMITS, now=OPEN_NOW, **env)


# --- review finding: an OCA pair can fill only one leg, so it claims the larger leg, not the sum ---

def test_an_oca_pair_claims_its_larger_leg_not_both_legs(env):
    set_mode("reduce_only", "t", env["state_path"])
    ib = FakeIB(positions={"SPY": 10}, fill=False)
    ib.placeOrder(SPY, LimitOrder("SELL", 6, 150.0, ocaGroup="g1", ocaType=1))   # take-profit
    ib.placeOrder(SPY, StopOrder("SELL", 6, 90.0, ocaGroup="g1", ocaType=1))     # stop, same group
    place(ib, SPY, MarketOrder("SELL", 4), reason="scale out", limits=LIMITS, now=OPEN_NOW, **env)   # 10 - 6 = room for 4
    with pytest.raises(OrderRefused):   # the scale-out order now rests too, so the 10 are fully claimed
        place(ib, SPY, MarketOrder("SELL", 1), reason="x", limits=LIMITS, now=OPEN_NOW, **env)


def test_orders_in_different_groups_or_no_group_still_add_up(env):
    set_mode("reduce_only", "t", env["state_path"])
    ib = FakeIB(positions={"SPY": 10}, fill=False)
    ib.placeOrder(SPY, LimitOrder("SELL", 4, 150.0, ocaGroup="a", ocaType=1))
    ib.placeOrder(SPY, StopOrder("SELL", 4, 90.0, ocaGroup="b", ocaType=1))
    ib.placeOrder(SPY, LimitOrder("SELL", 1, 160.0))
    with pytest.raises(OrderRefused):   # 4 + 4 + 1 = 9 claimed, only 1 left
        place(ib, SPY, MarketOrder("SELL", 2), reason="x", limits=LIMITS, now=OPEN_NOW, **env)
    place(ib, SPY, MarketOrder("SELL", 1), reason="x", limits=LIMITS, now=OPEN_NOW, **env)
