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


from functools import partial

from tempo.paper_run import dry_sender, preflight


def test_a_dry_run_sends_nothing_and_records_nothing(tmp_path):
    e = env(tmp_path)
    lines = []
    sender = partial(dry_sender, say=lines.append)
    assert run_entries(now=et(2026, 11, 3, 9, 40), sender=sender, **e) == 3
    assert e["ib"].placed == []                                          # nothing reached the broker
    assert len(lines) == 3 and all("WOULD SEND" in line for line in lines)
    assert e["ib"].whatif_calls == [("AAA", "BUY", 5, "DAY"), ("BBB", "SELL", 5, "DAY"), ("CCC", "BUY", 5, "DAY")]
    assert e["order_journal"].records() == []                            # the real order journal was not touched by the door


def test_a_dry_run_applies_the_order_doors_real_checks(tmp_path):
    from tempo.state import set_mode
    e = env(tmp_path)
    set_mode("reduce_only", "test", e["state_path"])
    lines = []
    assert run_entries(now=et(2026, 11, 3, 9, 40), sender=partial(dry_sender, say=lines.append), **e) == 0
    assert e["ib"].placed == [] and not any("WOULD SEND" in line for line in lines)
    assert all("reduce_only" in v["reason"] for v in load_state(e["paper"]).values())   # the scratch journal shows why


def test_a_dry_run_refuses_a_non_paper_account(tmp_path):
    e = env(tmp_path, ib=FakeIB(account="U1234567"))
    with pytest.raises(Exception, match="(?i)paper|live|account"):
        run_entries(now=et(2026, 11, 3, 9, 40), sender=partial(dry_sender, say=lambda *_: None), **e)


def test_a_dry_run_of_exits_shows_what_would_close(tmp_path):
    e = env(tmp_path)
    run_entries(now=et(2026, 11, 3, 9, 40), **e)        # a real (fake-broker) entry first
    lines = []
    n = run_exits(now=et(2026, 11, 9, 15, 50), sender=partial(dry_sender, say=lines.append), **e)
    assert n == 2 and sum("(exit)" in line for line in lines) == 2
    assert len(e["ib"].placed) == 3                     # only the three entries; the dry exits sent nothing


def make_preflight_env(tmp_path, **ib_over):
    e = env(tmp_path, ib=FakeIB(**ib_over))
    return e


def run_preflight(e, now, readonly=False, loss_fn=lambda ib: 0.3):
    return preflight(e["ib"], readonly=readonly, ledger=e["ledger"], paper=e["paper"], order_journal=e["order_journal"],
                     state_path=e["state_path"], now=now, loss_fn=loss_fn)


def names(checks):
    return {c.name: c for c in checks}


def test_preflight_all_ok_on_a_healthy_paper_account(tmp_path):
    checks = names(run_preflight(make_preflight_env(tmp_path), et(2026, 11, 3, 9, 40)))
    assert all(c.ok for c in checks.values()), {n: c.detail for n, c in checks.items() if not c.ok}
    assert "enter 3" in checks["due today"].detail
    assert "entries allowed now: True" in checks["time window"].detail


def test_preflight_fails_when_orders_are_disabled_the_mode_is_not_normal_or_pnl_is_unreadable(tmp_path):
    from tempo.state import set_mode
    e = make_preflight_env(tmp_path)
    assert not names(run_preflight(e, et(2026, 11, 3, 9, 40), readonly=True))["orders enabled"].ok

    def broken(ib):
        raise RuntimeError("daily P&L not available")

    c = names(run_preflight(e, et(2026, 11, 3, 9, 40), loss_fn=broken))
    assert not c["daily P&L readable"].ok and "not available" in c["daily P&L readable"].detail
    set_mode("reduce_only", "test", e["state_path"])
    assert not names(run_preflight(e, et(2026, 11, 3, 9, 40)))["mode normal"].ok


def test_preflight_fails_on_a_non_paper_account(tmp_path):
    assert not names(run_preflight(make_preflight_env(tmp_path, account="U1234567"), et(2026, 11, 3, 9, 40)))["account"].ok


def test_preflight_reports_closed_windows_without_failing(tmp_path):
    c = names(run_preflight(make_preflight_env(tmp_path), et(2026, 11, 3, 20, 0)))
    assert c["time window"].ok and "entries allowed now: False" in c["time window"].detail


def test_the_dry_run_gives_the_what_if_an_explicit_tif_even_if_the_order_has_none(tmp_path):
    """Without tif='DAY', IBKR's whatIfOrder returns nothing (docs/ibkr-gotchas.md)."""
    from ib_async import MarketOrder, Stock

    e = env(tmp_path)
    order = MarketOrder("BUY", 1)
    assert order.tif == ""
    dry_sender(e["ib"], Stock("AAA", "SMART", "USD"), order, reason="t", journal=e["order_journal"], limits=LIMITS, equity_usd=100_000.0,
               ref_price=100.0, state_path=e["state_path"], now=et(2026, 11, 3, 9, 40), say=lambda *_: None)
    assert e["ib"].whatif_calls[-1][3] == "DAY" and order.tif == ""    # the probe copy carries it; the real order is untouched


class PartialFillIB(FakeIB):
    """Fills `partial` shares of each order and leaves the rest working, until the order is cancelled."""

    def __init__(self, **kw):
        super().__init__(fill=True, **kw)
        self.partial = None

    def placeOrder(self, contract, order):
        if self.partial is None:
            return super().placeOrder(contract, order)
        self.fill = False
        try:
            trade = super().placeOrder(contract, order)
        finally:
            self.fill = True
        trade.orderStatus.filled = float(self.partial)
        trade.orderStatus.avgFillPrice = self.price
        self.held[contract.symbol] = self.held.get(contract.symbol, 0) + (1 if order.action == "BUY" else -1) * self.partial
        return trade


def test_a_partly_filled_entry_is_tracked_at_the_quantity_that_filled(tmp_path):
    ib = PartialFillIB()
    ib.partial = 2
    e = env(tmp_path, ib=ib)
    assert run_entries(now=et(2026, 11, 3, 9, 40), **e) == 3
    state = load_state(e["paper"])["claude_earnings_v1:AAA:e1"]
    assert state["status"] == "entered" and state["qty"] == 2 and state["partial"] is True    # the 2 shares that filled are not forgotten
    assert all(o.orderRef for o in ib.placed) and ib.held["AAA"] == 2
    assert e["order_journal"].unresolved() == []                                              # the cancelled order has its outcome recorded


def test_an_entry_with_no_fill_at_all_is_skipped_and_cancelled(tmp_path):
    ib = FakeIB(fill=False)
    e = env(tmp_path, ib=ib)
    assert run_entries(now=et(2026, 11, 3, 9, 40), **e) == 0
    assert all(v["status"] == "skipped" and "not filled" in v["reason"] for v in load_state(e["paper"]).values())
    assert all(t.isDone() for t in ib.trades)                                                 # nothing is left working at the broker


def test_a_partly_filled_exit_keeps_the_remainder_tracked_and_finishes_next_time(tmp_path):
    ib = PartialFillIB()
    e = env(tmp_path, ib=ib)
    run_entries(now=et(2026, 11, 3, 9, 40), **e)
    ib.partial = 2
    assert run_exits(now=et(2026, 11, 9, 15, 50), **e) == 0                                   # nothing fully closed yet
    aaa = load_state(e["paper"])["claude_earnings_v1:AAA:e1"]
    assert aaa["status"] == "entered" and aaa["qty"] == 3 and ib.held["AAA"] == 3             # 5 - 2 filled, still tracked
    ib.partial = None
    assert run_exits(now=et(2026, 11, 9, 15, 55), **e) == 2
    assert load_state(e["paper"])["claude_earnings_v1:AAA:e1"]["status"] == "exited" and ib.held["AAA"] == 0
    assert sorted(o.totalQuantity for o in ib.placed[-2:]) == [3, 3]                          # only the remainder was sent


def test_an_exit_never_sells_more_than_the_broker_actually_holds(tmp_path):
    ib = FakeIB()
    e = env(tmp_path, ib=ib)
    run_entries(now=et(2026, 11, 3, 9, 40), **e)
    ib.held["AAA"] = 3                                                                        # someone closed 2 of the 5 by hand
    run_exits(now=et(2026, 11, 9, 15, 50), **e)
    aaa_exit = next(o for o in ib.placed[3:] if o.action == "SELL")
    assert aaa_exit.totalQuantity == 3                                                        # not 5: that would have opened a short
    assert ib.held["AAA"] == 0


def test_an_exit_with_nothing_held_sends_no_order_and_closes_the_tracking(tmp_path):
    ib = FakeIB()
    e = env(tmp_path, ib=ib)
    run_entries(now=et(2026, 11, 3, 9, 40), **e)
    ib.held["AAA"] = 0
    ib.held["BBB"] = 0                                                                        # both already flat at the broker
    lines = []
    assert run_exits(now=et(2026, 11, 9, 15, 50), **{**e, "say": lines.append}) == 0
    assert len(ib.placed) == 3                                                                # still only the entries
    for sid in ("claude_earnings_v1:AAA:e1", "claude_earnings_v1:BBB:e1"):
        assert load_state(e["paper"])[sid]["status"] == "exited" and "no position" in load_state(e["paper"])[sid]["note"]
    assert any("no position" in line for line in lines)


def test_a_short_exit_is_also_capped_by_the_broker_position(tmp_path):
    ib = FakeIB()
    e = env(tmp_path, ib=ib)
    run_entries(now=et(2026, 11, 3, 9, 40), **e)
    ib.held["BBB"] = -2                                                                       # the short was partly covered by hand
    run_exits(now=et(2026, 11, 9, 15, 50), **e)
    bbb_exit = next(o for o in ib.placed[3:] if o.action == "BUY")
    assert bbb_exit.totalQuantity == 2                                                        # buy back 2, not 5 (that would open a long)


def test_an_exit_does_nothing_if_the_broker_is_on_the_opposite_side_of_what_was_recorded(tmp_path):
    ib = FakeIB()
    e = env(tmp_path, ib=ib)
    run_entries(now=et(2026, 11, 3, 9, 40), **e)
    ib.held["AAA"] = -3          # recorded long, but the account is actually SHORT 3: selling more would deepen the short
    ib.held["BBB"] = 4           # recorded short, but the account is actually LONG 4: buying would deepen the long
    assert run_exits(now=et(2026, 11, 9, 15, 50), **e) == 0
    assert len(ib.placed) == 3 and ib.held["AAA"] == -3 and ib.held["BBB"] == 4        # no order was sent
    assert load_state(e["paper"])["claude_earnings_v1:AAA:e1"]["status"] == "exited"    # tracking closed, with a note
