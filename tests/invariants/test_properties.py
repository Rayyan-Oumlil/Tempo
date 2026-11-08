"""The order door's safety rules under random orders (hypothesis). Unit tests check the cases we thought of; these
check that no combination of side, size, price, position, resting orders and account state gets past a rule."""
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS

import pytest
from fakes import CLOSED_NOW, OPEN_NOW, SPY, FakeIB, FakeTrade
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from ib_async import LimitOrder, MarketOrder

from tempo.journal import Journal
from tempo.orders import Limits, OrderRefused, _committed, is_exit, place
from tempo.state import set_mode

LIMITS = Limits(max_position_pct=50.0)
EQUITY = 100_000.0
REF = 100.0
PROFILE = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])

sides = st.sampled_from(["BUY", "SELL"])
quantities = st.integers(min_value=1, max_value=2_000)
positions = st.integers(min_value=-1_000, max_value=1_000)
limit_prices = st.one_of(st.none(), st.floats(min_value=1.0, max_value=300.0, allow_nan=False))
in_band_limits = st.one_of(st.none(), st.floats(min_value=91.0, max_value=109.0, allow_nan=False))
resting = st.lists(st.tuples(sides, st.integers(min_value=1, max_value=500), st.sampled_from(["", "g1", "g2"])), max_size=4)


def make_order(side, qty, limit):
    return MarketOrder(side, qty) if limit is None else LimitOrder(side, qty, round(limit, 2))


def fake_with(held, rest=()):
    ib = FakeIB(positions={"SPY": held} if held else {}, fill=False)
    for side, qty, group in rest:
        order = MarketOrder(side, qty)
        order.ocaGroup, order.ocaType = group, 1 if group else 0
        ib.trades.append(FakeTrade(SPY, order, "Submitted"))
    return ib


def run_place(ib, order, *, equity=EQUITY, ref=REF, now=OPEN_NOW, mode=None, limits=LIMITS):
    with tempfile.TemporaryDirectory() as tmp:
        journal, state = Journal(Path(tmp) / "j.jsonl"), Path(tmp) / "state.json"
        if mode:
            set_mode(mode, "property test", state)
        place(ib, SPY, order, reason="property", journal=journal, limits=limits, equity_usd=equity, ref_price=ref,
              now=now, state_path=state)
        return journal.records()


@PROFILE
@given(side=sides, qty=quantities, limit=limit_prices, held=positions, rest=resting)
def test_nothing_sent_is_ever_an_oversize_entry(side, qty, limit, held, rest):
    ib, order = fake_with(held, rest), None
    order = make_order(side, qty, limit)
    exit_like = is_exit(ib, SPY, order)
    try:
        run_place(ib, order)
    except OrderRefused:
        assert ib.placed == []                                   # refused means nothing reached the broker
        return
    if not exit_like:
        worst = max(p for p in (REF, order.lmtPrice if limit is not None else 0) if p)
        assert qty * worst <= EQUITY * LIMITS.max_position_pct / 100   # an entry stayed under the cap
    assert len(ib.placed) == 1


@PROFILE
@given(side=sides, qty=quantities, held=positions, rest=resting)
def test_an_exit_never_flips_or_grows_the_position(side, qty, held, rest):
    ib = fake_with(held, rest)
    order = MarketOrder(side, qty)
    if not is_exit(ib, SPY, order):
        return
    committed = _committed(ib.reqAllOpenOrders(), SPY, side)
    if side == "SELL":
        assert held > 0 and qty <= held - committed       # long: sells fit in what resting orders left unclaimed
    else:
        assert held < 0 and qty <= -held - committed
    flat = FakeIB(positions={"SPY": held}, fill=True)       # and when it fills, the account ends on the same side or flat
    run_place(flat, make_order(side, qty, None))
    after = flat.held.get("SPY", 0)
    assert after == 0 or (after > 0) == (held > 0)
    assert abs(after) <= abs(held)


BAD_STATES = st.sampled_from(["no_equity", "zero_equity", "no_price", "negative_price", "closed", "reduce_only", "live_account"])


@PROFILE
@given(bad=BAD_STATES, side=sides, qty=st.integers(min_value=1, max_value=50), limit=limit_prices)
def test_an_entry_in_any_bad_state_is_refused_and_nothing_is_sent(bad, side, qty, limit):
    ib = FakeIB(account="U7654321" if bad == "live_account" else "DU1234567", fill=False)   # flat: every order is an entry
    kwargs = {"no_equity": dict(equity=None), "zero_equity": dict(equity=0), "no_price": dict(ref=None),
              "negative_price": dict(ref=-5.0), "closed": dict(now=CLOSED_NOW), "reduce_only": dict(mode="reduce_only"),
              "live_account": {}}[bad]
    with pytest.raises((OrderRefused, RuntimeError)):
        run_place(ib, make_order(side, qty, limit), **kwargs)
    assert ib.placed == []


@PROFILE
@given(bad=st.sampled_from(["no_equity", "no_price", "closed", "reduce_only"]), long_=st.booleans(),
       held=st.integers(min_value=1, max_value=500), data=st.data())
def test_a_real_exit_is_never_blocked_by_the_entry_rules(bad, long_, held, data):
    qty = data.draw(st.integers(min_value=1, max_value=held))
    position = held if long_ else -held
    ib = FakeIB(positions={"SPY": position}, fill=True)
    kwargs = {"no_equity": dict(equity=None), "no_price": dict(ref=None), "closed": dict(now=CLOSED_NOW),
              "reduce_only": dict(mode="reduce_only")}[bad]
    run_place(ib, MarketOrder("SELL" if long_ else "BUY", qty), **kwargs)
    assert len(ib.placed) == 1


@PROFILE
@given(side=sides, qty=st.integers(min_value=1, max_value=50), limit=in_band_limits)
def test_the_intent_is_journaled_before_the_broker_sees_the_order(side, qty, limit):
    ib = FakeIB(fill=False)
    seen = []
    with tempfile.TemporaryDirectory() as tmp:
        journal = Journal(Path(tmp) / "j.jsonl")
        real = ib.placeOrder

        def spy(contract, order):
            seen.append([r["kind"] for r in journal.records() if r.get("ref") == order.orderRef])
            return real(contract, order)

        ib.placeOrder = spy
        place(ib, SPY, make_order(side, qty, limit), reason="property", journal=journal, limits=LIMITS,
              equity_usd=EQUITY, ref_price=REF, now=OPEN_NOW, state_path=Path(tmp) / "state.json")
    assert seen == [["intent"]]


@PROFILE
@given(side=sides, qty=st.integers(min_value=1, max_value=50), limit=in_band_limits)
def test_the_same_order_twice_in_the_window_is_sent_once(side, qty, limit):
    ib = FakeIB(fill=False)
    with tempfile.TemporaryDirectory() as tmp:
        journal, state = Journal(Path(tmp) / "j.jsonl"), Path(tmp) / "state.json"
        send = lambda: place(ib, SPY, make_order(side, qty, limit), reason="property", journal=journal,  # noqa: E731
                             limits=LIMITS, equity_usd=EQUITY, ref_price=REF, now=OPEN_NOW, state_path=state)
        send()
        with pytest.raises(OrderRefused, match="duplicate"):
            send()
    assert len(ib.placed) == 1


@PROFILE
@given(held=positions, rest=resting, qty=quantities)
def test_two_sells_that_could_both_fill_never_both_count_as_exits(held, rest, qty):
    """The flip scenario: if SELL a and SELL b are both exits against the same resting book, a + b + committed <= held."""
    ib = fake_with(held, rest)
    committed = _committed(ib.reqAllOpenOrders(), SPY, "SELL")
    if not is_exit(ib, SPY, MarketOrder("SELL", qty)):
        return
    ib.trades.append(FakeTrade(SPY, MarketOrder("SELL", qty), "Submitted"))
    second = NS(totalQuantity=held - committed - qty + 1)       # one share more than what is still free
    assert not is_exit(ib, SPY, MarketOrder("SELL", second.totalQuantity))


@PROFILE
@given(side=sides, qty=st.integers(min_value=1, max_value=50), off=st.floats(min_value=0.5, max_value=100.0, allow_nan=False))
def test_an_entry_limit_far_on_the_wrong_side_of_the_price_is_always_refused(side, qty, off):
    ib = FakeIB(fill=False)                                    # flat: an entry
    wrong_side = REF * (1 + (10.0 + off) / 100) if side == "BUY" else REF * (1 - min(10.0 + off, 99.0) / 100)
    with pytest.raises(OrderRefused, match="reference price"):
        run_place(ib, LimitOrder(side, qty, round(wrong_side, 2)))
    assert ib.placed == []


def oracle_is_exit(held, rest, side, qty):
    """The documented rule, re-derived without the code under test: resting orders on this side claim size, but an
    OCA group (one fill cancels the rest) only ever fills one leg, so it claims its largest leg."""
    loose = sum(q for s, q, group in rest if s == side and not group)
    groups = {}
    for s, q, group in rest:
        if s == side and group:
            groups[group] = max(groups.get(group, 0), q)
    free = (held if side == "SELL" else -held) - loose - sum(groups.values())
    return (held > 0 if side == "SELL" else held < 0) and qty <= free


@PROFILE
@given(side=sides, qty=quantities, held=positions, rest=resting)
def test_exit_decision_matches_the_documented_rule(side, qty, held, rest):
    assert is_exit(fake_with(held, rest), SPY, MarketOrder(side, qty)) == oracle_is_exit(held, rest, side, qty)


@PROFILE
@given(side=sides, held=st.integers(min_value=1, max_value=1_000), rest=resting)
def test_the_exit_boundary_is_exact_free_size_allowed_one_more_refused(side, held, rest):
    position = held if side == "SELL" else -held
    claimed = {s: 0 for s in ("BUY", "SELL")}
    for s, q, group in rest:
        if s == side and not group:
            claimed[s] += q
    grouped = {}
    for s, q, group in rest:
        if s == side and group:
            grouped[group] = max(grouped.get(group, 0), q)
    free = held - claimed[side] - sum(grouped.values())
    ib = fake_with(position, rest)
    if free >= 1:
        assert is_exit(ib, SPY, MarketOrder(side, free))
    assert not is_exit(ib, SPY, MarketOrder(side, max(free + 1, 1)))
