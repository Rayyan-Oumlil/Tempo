from types import SimpleNamespace as NS

import pytest
from fakes import SPY, FakeIB
from ib_async import LimitOrder

from tempo.health import run_health
from tempo.journal import Journal
from tempo.reconcile import reconcile
from tempo.state import set_mode
from test_health import fake_ib


@pytest.fixture
def journal(tmp_path):
    return Journal(tmp_path / "j.jsonl")


def test_nothing_unresolved_is_a_pass(journal):
    checks = reconcile(FakeIB(), journal)
    assert [c.ok for c in checks] == [True]


def test_intent_matched_to_a_fill_is_resolved_as_filled(journal):
    journal.append("intent", ref="r1", symbol="SPY")
    ib = FakeIB()
    ib.reqExecutions = lambda: [NS(execution=NS(orderRef="r1", shares=2.0, price=10.0, side="BUY", execId="e1"))]
    checks = reconcile(ib, journal)
    assert all(c.ok for c in checks) and journal.unresolved() == []
    assert [r["status"] for r in journal.records() if r["kind"] == "resolution"] == ["Filled"]


def test_partial_fill_counts_as_filled(journal):
    journal.append("intent", ref="r1", symbol="SPY")
    ib = FakeIB()
    ib.reqExecutions = lambda: [NS(execution=NS(orderRef="r1", shares=0.5, price=10.0, side="BUY", execId="e1"))]
    reconcile(ib, journal)
    assert [r["status"] for r in journal.records() if r["kind"] == "resolution"] == ["Filled"]


def test_intent_matched_to_a_working_order_is_resolved_as_working(journal):
    journal.append("intent", ref="r1", symbol="SPY")
    ib = FakeIB(fill=False)
    ib.placeOrder(SPY, LimitOrder("BUY", 1, 50.0, orderRef="r1"))
    checks = reconcile(ib, journal)
    assert journal.unresolved() == []
    assert journal.records()[-1]["status"] == "working" and "working" in checks[0].detail


def test_missing_intent_stays_blocked_unless_accepted(journal):
    journal.append("intent", ref="gone", symbol="SPY")
    checks = reconcile(FakeIB(), journal)
    assert not checks[0].ok and len(journal.unresolved()) == 1
    checks = reconcile(FakeIB(), journal, resolve_missing=True)
    assert all(c.ok for c in checks) and journal.unresolved() == []
    assert journal.records()[-1]["status"] == "accepted_missing"


def test_unreadable_broker_leaves_everything_unresolved(journal):
    journal.append("intent", ref="r1", symbol="SPY")
    ib = FakeIB()

    def boom():
        raise ConnectionError("down")

    ib.reqAllOpenOrders = boom
    checks = reconcile(ib, journal)
    assert not checks[0].ok and len(journal.unresolved()) == 1


def test_health_shows_mode_and_journal(journal, tmp_path):
    state = tmp_path / "state.json"
    set_mode("reduce_only", "t", state)
    journal.append("intent", ref="old", symbol="SPY")
    journal._clock = lambda: journal.records()[0]["ts"] + 3600
    by = {c.name: c for c in run_health(fake_ib(), journal=journal, state_path=state)}
    assert by["mode"].detail.startswith("reduce_only") and by["mode"].ok
    assert not by["journal"].ok and "1 unresolved" in by["journal"].detail


def test_health_without_journal_is_unchanged():
    assert "mode" not in {c.name for c in run_health(fake_ib())}


def execution(ref, exec_id, shares=1.0, price=10.0, side="SELL"):
    return NS(execution=NS(orderRef=ref, shares=shares, price=price, side=side, execId=exec_id))


def test_fill_of_an_already_resolved_order_is_still_journaled_once(journal):
    # a resting bracket stop was resolved as "working", then it fired later
    journal.append("intent", ref="stop1", symbol="SPY")
    journal.append("resolution", ref="stop1", status="working")
    ib = FakeIB()
    ib.reqExecutions = lambda: [execution("stop1", "e9", shares=2.0, price=98.5)]
    checks = reconcile(ib, journal)
    fills = [r for r in journal.records() if r["kind"] == "fill"]
    assert len(fills) == 1 and fills[0]["shares"] == 2.0 and fills[0]["price"] == 98.5 and fills[0]["exec_id"] == "e9"
    assert any("1 new fill" in c.detail for c in checks)
    reconcile(ib, journal)  # running again must not duplicate it
    assert len([r for r in journal.records() if r["kind"] == "fill"]) == 1


def test_executions_for_orders_not_in_the_journal_are_ignored(journal):
    journal.append("intent", ref="mine", symbol="SPY")
    journal.append("outcome", ref="mine", status="Filled")
    ib = FakeIB()
    ib.reqExecutions = lambda: [execution("someone-elses-order", "e1")]
    reconcile(ib, journal)
    assert [r for r in journal.records() if r["kind"] == "fill"] == []
