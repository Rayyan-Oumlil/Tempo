from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from tempo.journal import Journal
from tempo.ledger import Ledger
from tempo.orders import Limits
from tempo.paper_run import (HORIZONS, NOTIONAL_PCT, due_actions, entries_allowed, exits_allowed, load_state, position_size,
                             run_entries, run_exits, schedule)
from tests.fakes import FakeIB

ET = ZoneInfo("America/New_York")
LIMITS = Limits(max_position_pct=50.0)


def et(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=ET).astimezone(timezone.utc)


def make_ledger(tmp_path, signal_day=date(2026, 11, 2)):
    ledger = Ledger(tmp_path / "ledger.jsonl", clock=lambda: datetime(signal_day.year, signal_day.month, signal_day.day, 20, 0, tzinfo=ET).timestamp())
    ledger.record_signal(source="claude_earnings_v1", symbol="AAA", direction=1, event_id="e1")
    ledger.record_signal(source="claude_earnings_v1", symbol="BBB", direction=-1, event_id="e1")
    ledger.record_signal(source="insider_cluster_v1", symbol="CCC", direction=1, event_id="e1")
    ledger.record_signal(source="other_v1", symbol="DDD", direction=1, event_id="e1")  # not a traded source
    return ledger


def env(tmp_path, ib=None, price=100.0, equity=100_000.0):
    return dict(ib=ib or FakeIB(), ledger=make_ledger(tmp_path), paper=Journal(tmp_path / "paper.jsonl"), order_journal=Journal(tmp_path / "orders.jsonl"),
                limits=LIMITS, state_path=tmp_path / "state.json", price_fn=lambda ib, c: price, equity_fn=lambda ib: equity, say=lambda *_: None)


def test_schedule_enters_the_next_trading_day_and_exits_on_the_horizon_th_day():
    assert schedule("2026-11-02", 5) == (date(2026, 11, 3), date(2026, 11, 9))     # days 1..5 = Tue, Wed, Thu, Fri, Mon
    assert schedule("2026-11-06", 1) == (date(2026, 11, 9), date(2026, 11, 9))     # Friday signal enters Monday; 1-day exits same day
    assert schedule("2026-11-24", 5) == (date(2026, 11, 25), date(2026, 12, 2))    # Thanksgiving (26th) is skipped


def test_position_size_is_a_fraction_of_equity_in_whole_shares():
    assert position_size(100_000.0, 100.0, 0.5) == 5
    assert position_size(100_000.0, 333.0, 0.5) == 1
    assert position_size(100_000.0, 600.0, 0.5) == 0
    assert NOTIONAL_PCT == 0.5


def test_only_the_registered_sources_and_horizons_are_traded():
    assert HORIZONS == {"claude_earnings_v1": 5, "insider_cluster_v1": 21}


def test_entries_are_due_on_the_entry_day_and_not_before_or_after(tmp_path):
    e = env(tmp_path)
    assert [s["symbol"] for s in due_actions(e["ledger"].signals(), {}, date(2026, 11, 3))["enter"]] == ["AAA", "BBB", "CCC"]
    assert due_actions(e["ledger"].signals(), {}, date(2026, 11, 2))["enter"] == []          # entry day not yet reached
    later = due_actions(e["ledger"].signals(), {}, date(2026, 11, 4))
    assert later["enter"] == [] and [s["symbol"] for s in later["missed"]] == ["AAA", "BBB", "CCC"]   # never entered late


def test_run_entries_places_longs_and_shorts_and_records_them(tmp_path):
    e = env(tmp_path)
    placed = run_entries(now=et(2026, 11, 3, 9, 40), **e)
    assert placed == 3
    orders = e["ib"].placed
    assert [(o.action, o.totalQuantity) for o in orders] == [("BUY", 5), ("SELL", 5), ("BUY", 5)]   # 0.5% of 100,000 at 100
    assert all(o.orderType == "MKT" for o in orders)
    state = load_state(e["paper"])
    assert state["claude_earnings_v1:AAA:e1"]["status"] == "entered" and state["claude_earnings_v1:BBB:e1"]["direction"] == -1
    assert "other_v1:DDD:e1" not in state


def test_running_entries_twice_does_not_trade_twice(tmp_path):
    e = env(tmp_path)
    run_entries(now=et(2026, 11, 3, 9, 40), **e)
    assert run_entries(now=et(2026, 11, 3, 9, 50), **e) == 0
    assert len(e["ib"].placed) == 3


def test_a_signal_the_broker_cannot_qualify_is_skipped_with_a_reason(tmp_path):
    class NoQualify(FakeIB):
        def qualifyContracts(self, *contracts):
            return [] if contracts[0].symbol == "BBB" else list(contracts)

    e = env(tmp_path, ib=NoQualify())
    assert run_entries(now=et(2026, 11, 3, 9, 40), **e) == 2
    skipped = load_state(e["paper"])["claude_earnings_v1:BBB:e1"]
    assert skipped["status"] == "skipped" and "qualify" in skipped["reason"]


def test_a_refused_order_is_skipped_with_the_door_s_reason(tmp_path):
    from tempo.state import set_mode
    e = env(tmp_path)
    set_mode("reduce_only", "test", e["state_path"])
    assert run_entries(now=et(2026, 11, 3, 9, 40), **e) == 0
    state = load_state(e["paper"])
    assert all(v["status"] == "skipped" and "reduce_only" in v["reason"] for v in state.values()) and len(state) == 3


def test_a_stock_too_expensive_for_the_slice_is_skipped(tmp_path):
    e = env(tmp_path, price=1000.0)
    assert run_entries(now=et(2026, 11, 3, 9, 40), **e) == 0
    assert all("too small" in v["reason"] for v in load_state(e["paper"]).values())


def test_a_price_that_cannot_be_read_is_skipped_not_guessed(tmp_path):
    e = env(tmp_path)

    def broken(ib, contract):
        raise RuntimeError("no daily bars")

    e["price_fn"] = broken
    assert run_entries(now=et(2026, 11, 3, 9, 40), **e) == 0
    assert all("price" in v["reason"] for v in load_state(e["paper"]).values())


def test_exits_happen_on_the_exit_day_with_the_held_quantity_and_opposite_side(tmp_path):
    e = env(tmp_path)
    run_entries(now=et(2026, 11, 3, 9, 40), **e)
    assert run_exits(now=et(2026, 11, 6, 15, 50), **e) == 0                    # day 4 of 5: too early
    assert run_exits(now=et(2026, 11, 9, 15, 50), **e) == 2                    # day 5: the two 5-day signals (CCC is 21 days)
    exits = e["ib"].placed[3:]
    assert sorted((o.action, o.totalQuantity) for o in exits) == [("BUY", 5), ("SELL", 5)]
    assert load_state(e["paper"])["claude_earnings_v1:AAA:e1"]["status"] == "exited"
    assert load_state(e["paper"])["insider_cluster_v1:CCC:e1"]["status"] == "entered"
    assert run_exits(now=et(2026, 11, 9, 15, 55), **e) == 0                    # not twice


def test_the_21_day_signal_exits_on_its_own_day(tmp_path):
    e = env(tmp_path)
    run_entries(now=et(2026, 11, 3, 9, 40), **e)
    _, exit_day = schedule("2026-11-02", 21)
    assert run_exits(now=et(exit_day.year, exit_day.month, exit_day.day, 15, 50), **e) >= 1
    assert load_state(e["paper"])["insider_cluster_v1:CCC:e1"]["status"] == "exited"


def test_time_windows():
    assert not entries_allowed(et(2026, 11, 3, 9, 34)) and entries_allowed(et(2026, 11, 3, 9, 35)) and entries_allowed(et(2026, 11, 3, 15, 0))
    assert not entries_allowed(et(2026, 11, 7, 10, 0))                                   # Saturday
    assert not exits_allowed(et(2026, 11, 3, 15, 44)) and exits_allowed(et(2026, 11, 3, 15, 45)) and not exits_allowed(et(2026, 11, 3, 16, 0))
    assert exits_allowed(et(2026, 11, 27, 12, 45)) and not exits_allowed(et(2026, 11, 27, 12, 44))   # early close day


def test_an_exit_is_due_on_the_exit_day_and_not_a_calendar_day_earlier(tmp_path):
    ledger = make_ledger(tmp_path)
    entered = {s["signal_id"]: {"status": "entered", "qty": 5, "direction": s["direction"]} for s in ledger.signals("claude_earnings_v1")}
    assert due_actions(ledger.signals(), entered, date(2026, 11, 8))["exit"] == []          # the day before the exit day (a Sunday)
    assert len(due_actions(ledger.signals(), entered, date(2026, 11, 9))["exit"]) == 2      # the 5th trading day
    assert len(due_actions(ledger.signals(), entered, date(2026, 11, 10))["exit"]) == 2     # and any later day, until it is done
