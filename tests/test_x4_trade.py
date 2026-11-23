from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from tempo import x4_trade as t
from tempo.x4_signal import X4Signal

NOW = datetime(2026, 11, 24, 1, 30, tzinfo=timezone.utc)


def sig(weight=0.5, close=60_000.0, as_of="2026-11-23"):
    return X4Signal(as_of, close, 55_000.0, 0.5, weight > 0, weight, False)


def test_off_signal_with_position_sells_everything():
    p = t.plan_trade(sig(0.0), held_qty=0.05, sleeve_usd=10_000)
    assert (p.action, p.qty) == ("SELL", 0.05)


def test_off_signal_flat_does_nothing():
    assert t.plan_trade(sig(0.0), 0.0, 10_000).action == "HOLD"


def test_on_signal_buys_the_gap_to_target():
    p = t.plan_trade(sig(0.5), 0.0, 12_000)  # target 6,000 USD / 60,000 = 0.1 BTC
    assert (p.action, p.qty, p.target_qty) == ("BUY", 0.1, 0.1)


def test_small_difference_is_skipped():
    assert t.plan_trade(sig(0.5), 0.0999, 12_000).action == "HOLD"


def test_resize_down_sells_only_the_excess():
    p = t.plan_trade(sig(0.25), 0.1, 12_000)  # target 0.05
    assert (p.action, p.qty) == ("SELL", 0.05)


def test_limit_is_marketable_and_on_the_tick():
    assert t.limit_price("BUY", 60_000.0) == 60_300.0
    assert t.limit_price("SELL", 60_000.0) == 59_700.0
    assert (t.limit_price("BUY", 61_161.91) * 4) % 1 == 0


def test_stale_data_refuses():
    with pytest.raises(RuntimeError, match="stale"):
        t.require_fresh(sig(as_of="2026-11-20"), NOW)
    t.require_fresh(sig(as_of="2026-11-23"), NOW)


def test_live_without_sleeve_refuses_and_default_is_dry():
    with pytest.raises(RuntimeError, match="X4_SLEEVE_USD"):
        t.parse_env({"X4_LIVE": "1"})
    assert t.parse_env({"X4_SLEEVE_USD": "5000"}) == (False, 5000.0)
    assert t.parse_env({"X4_LIVE": "true", "X4_SLEEVE_USD": "5000"})[0] is False  # only the exact string "1" arms it


class FakeIB:
    def __init__(self, held):
        self._held = held

    def positions(self):
        return [SimpleNamespace(position=self._held, contract=SimpleNamespace(conId=7))]


def test_dry_run_never_calls_the_sender():
    calls = []
    rec = t.run_once(FakeIB(0.0), SimpleNamespace(conId=7), sig(0.5), 12_000, False, lambda *a, **k: calls.append(1), NOW)
    assert rec["plan"]["action"] == "BUY" and not rec["sent"] and not calls


def test_live_sends_one_ioc_limit_order_with_the_x4_ref():
    sent = []

    def sender(ib, contract, order, *, reason, close):
        sent.append(order)
        return SimpleNamespace(order=SimpleNamespace(orderId=99))

    rec = t.run_once(FakeIB(0.0), SimpleNamespace(conId=7), sig(0.5), 12_000, True, sender, NOW)
    assert rec["sent"] and rec["order_id"] == 99 and len(sent) == 1
    o = sent[0]
    assert (o.action, o.orderType, o.tif, o.orderRef, o.totalQuantity) == ("BUY", "LMT", "IOC", "tempo-x4", 0.1)


def test_live_hold_sends_nothing():
    sent = []
    rec = t.run_once(FakeIB(0.1), SimpleNamespace(conId=7), sig(0.5), 12_000, True, lambda *a, **k: sent.append(1), NOW)
    assert rec["plan"]["action"] == "HOLD" and not sent
