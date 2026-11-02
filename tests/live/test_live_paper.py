import dataclasses

import pytest
from dotenv import load_dotenv
from ib_async import LimitOrder, MarketOrder, Stock

from tempo.bracket import BracketPlan, confirm_bracket, place_bracket, plan_bracket
from tempo.config import load_config
from tempo.flatten import flatten_positions
from tempo.ibkr import connect
from tempo.ibutil import wait_until
from tempo.account import daily_loss_pct
from tempo.kill import kill
from tempo.lifecycle import run_lifecycle
from tempo.orders import Limits, OrderRefused, place
from tempo.reconcile import reconcile
from tempo.risk import RiskRules
from tempo.state import get_mode

pytestmark = pytest.mark.live


def positions(ib):
    return {p.contract.symbol: p.position for p in ib.positions() if p.position}


def test_lifecycle_buys_sells_and_leaves_nothing_unresolved(ib, spy, env, rth):
    result = run_lifecycle(ib, spy, 1, journal=env["journal"], limits=env["limits"], equity_usd=env["equity"],
                           ref_price=env["price"], state_path=env["state_path"])
    assert all(c.ok for c in result.checks), [c.detail for c in result.checks]
    assert env["journal"].unresolved() == [] and positions(ib) == {}


def test_bracket_stop_rests_at_the_broker_and_kill_clears_it(ib, spy, env, rth):
    plan = plan_bracket(env["equity"], env["price"], round(env["price"] * 0.95, 2), round(env["price"] * 1.05, 2),
                        RiskRules(2.0, 100.0, 5.0), qty=1)
    legs = place_bracket(ib, spy, plan, journal=env["journal"], limits=env["limits"], equity_usd=env["equity"],
                         state_path=env["state_path"])
    checks = confirm_bracket(ib, legs, journal=env["journal"], limits=env["limits"], state_path=env["state_path"])
    assert [c.name for c in checks] == ["entry", "stop"] and all(c.ok for c in checks)
    assert positions(ib) == {"SPY": 1.0} and len(ib.reqAllOpenOrders()) == 2  # stop and take-profit rest at IBKR

    results = kill(ib, journal=env["journal"], limits=env["limits"], state_path=env["state_path"])
    assert all(c.ok for c in results), [c.detail for c in results]
    assert positions(ib) == {} and ib.reqAllOpenOrders() == []
    assert get_mode(env["state_path"]) == "reduce_only"


def test_marketable_take_profit_closes_the_position_and_cancels_the_stop(ib, spy, env, rth):
    plan = BracketPlan(qty=1, entry=env["price"], stop=round(env["price"] * 0.9, 2), take_profit=round(env["price"] * 0.5, 2))
    legs = place_bracket(ib, spy, plan, journal=env["journal"], limits=env["limits"], equity_usd=env["equity"],
                         state_path=env["state_path"])
    checks = confirm_bracket(ib, legs, journal=env["journal"], limits=env["limits"], state_path=env["state_path"])
    assert [c.name for c in checks] == ["entry", "exit"] and all(c.ok for c in checks)
    ib.sleep(2)
    assert positions(ib) == {} and ib.reqAllOpenOrders() == []


def test_kill_closes_a_long_and_a_short_and_cancels_resting_orders(ib, spy, env, rth):
    qqq = Stock("QQQ", "SMART", "USD")
    ib.qualifyContracts(qqq)
    rules = dict(journal=env["journal"], limits=env["limits"], equity_usd=env["equity"], state_path=env["state_path"])
    long_trade = place(ib, spy, MarketOrder("BUY", 1), reason="live test", ref_price=env["price"], **rules)
    short_trade = place(ib, qqq, MarketOrder("SELL", 1), reason="live test", ref_price=env["price"], **rules)
    place(ib, spy, LimitOrder("BUY", 1, round(env["price"] * 0.5, 2)), reason="live test", ref_price=env["price"], **rules)
    wait_until(ib, lambda: long_trade.isDone() and short_trade.isDone(), 20)
    ib.sleep(2)
    assert positions(ib) == {"SPY": 1.0, "QQQ": -1.0}

    results = kill(ib, journal=env["journal"], limits=env["limits"], state_path=env["state_path"])
    assert all(c.ok for c in results), [c.detail for c in results]
    assert positions(ib) == {} and ib.reqAllOpenOrders() == []


def test_a_crashed_process_is_reconciled_from_a_fresh_connection(ib, spy, env, rth):
    """Three orders are sent but never recorded (a crash); a different client id then reconciles them."""
    rules = dict(journal=env["journal"], limits=env["limits"], equity_usd=env["equity"], state_path=env["state_path"])
    far = round(env["price"] * 0.5, 2)
    working = place(ib, spy, LimitOrder("BUY", 1, far, orderRef="crash-working"), reason="live test", ref_price=env["price"], **rules)
    filled = place(ib, spy, MarketOrder("BUY", 1, orderRef="crash-filled"), reason="live test", ref_price=env["price"], **rules)
    cancelled = place(ib, spy, LimitOrder("BUY", 1, far - 1, orderRef="crash-cancelled"), reason="live test", ref_price=env["price"], **rules)
    ib.sleep(3)
    ib.cancelOrder(cancelled.order)
    wait_until(ib, lambda: cancelled.isDone() and filled.isDone(), 20)
    assert len(env["journal"].unresolved()) == 3  # nothing was recorded

    load_dotenv()
    fresh = connect(dataclasses.replace(load_config(), client_id=25))  # a new "process"
    fresh.RequestTimeout = 15
    try:
        first = reconcile(fresh, env["journal"])
        resolved = [c for c in first if c.name == "resolved"]
        unresolved = [c for c in first if c.name == "unresolved"]
        assert len(resolved) == 2 and len(unresolved) == 1
        assert any("working" in c.detail for c in resolved) and any("filled" in c.detail for c in resolved)
        assert "crash-cancelled" in unresolved[0].detail
        second = reconcile(fresh, env["journal"], resolve_missing=True)
        assert all(c.ok for c in second) and env["journal"].unresolved() == []
        third = reconcile(fresh, env["journal"])  # idempotent: nothing new to record
        assert all(c.ok for c in third) and "fill" not in " ".join(c.name for c in third)
    finally:
        fresh.disconnect()


def test_daily_loss_limit_reads_the_real_pnl_and_blocks_entries(ib, spy, env):
    """Runs any time the Gateway is up: the entry is an after-hours limit order far below the market."""
    loss = daily_loss_pct(ib)
    assert -100 < loss < 100
    far = round(env["price"] * 0.5, 2)
    rules = dict(journal=env["journal"], state_path=env["state_path"], equity_usd=env["equity"], ref_price=env["price"])

    just_hit = Limits(max_position_pct=100.0, max_daily_loss_pct=loss - 0.001)   # the account is already past this
    with pytest.raises(OrderRefused, match="daily loss limit"):
        place(ib, spy, LimitOrder("BUY", 1, far, outsideRth=True), reason="live test", limits=just_hit, **rules)
    assert ib.reqAllOpenOrders() == []                                          # nothing reached the broker

    roomy = Limits(max_position_pct=100.0, max_daily_loss_pct=loss + 1.0)
    trade = place(ib, spy, LimitOrder("BUY", 1, far, outsideRth=True), reason="live test", limits=roomy, **rules)
    ib.sleep(2)
    assert trade.orderStatus.status in {"Submitted", "PreSubmitted"}
    ib.cancelOrder(trade.order)
    wait_until(ib, trade.isDone, 10)


def test_exits_still_work_when_the_daily_loss_limit_is_hit(ib, spy, env, rth):
    loss = daily_loss_pct(ib)
    rules = dict(journal=env["journal"], state_path=env["state_path"], equity_usd=env["equity"], ref_price=env["price"])
    roomy = Limits(max_position_pct=100.0, max_daily_loss_pct=loss + 1.0)
    bought = place(ib, spy, MarketOrder("BUY", 1), reason="live test", limits=roomy, **rules)
    wait_until(ib, bought.isDone, 20)
    ib.sleep(2)
    assert positions(ib) == {"SPY": 1.0}

    just_hit = Limits(max_position_pct=100.0, max_daily_loss_pct=loss - 0.001)
    with pytest.raises(OrderRefused, match="daily loss limit"):
        place(ib, spy, MarketOrder("BUY", 1), reason="live test", limits=just_hit, **rules)   # new risk: refused
    results = flatten_positions(ib, journal=env["journal"], limits=just_hit, state_path=env["state_path"])
    assert all(r.ok for r in results), [r.detail for r in results]                            # the exit goes through
    ib.sleep(2)
    assert positions(ib) == {}
