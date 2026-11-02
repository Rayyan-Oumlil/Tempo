from types import SimpleNamespace as NS

import pytest

from tempo.roundtrip import far_limit_price, run_roundtrip

DONE = {"Filled", "Cancelled", "ApiCancelled"}


class FakeTrade:
    def __init__(self, status):
        self.order = NS(orderId=7)
        self.orderStatus = NS(status=status, filled=0)

    def isDone(self):
        return self.orderStatus.status in DONE


class FakeIB:
    def __init__(self, status="Submitted", cancels_to="Cancelled", open_raises=False):
        self.trade = FakeTrade(status)
        self.cancel_to = cancels_to
        self.open_raises = open_raises
        self.cancel_calls = 0
        self.placed = []

    def sleep(self, _):
        pass

    def placeOrder(self, contract, order):
        self.placed.append(order)
        return self.trade

    def cancelOrder(self, order):
        self.cancel_calls += 1
        self.trade.orderStatus.status = self.cancel_to

    def openTrades(self):
        if self.open_raises:
            raise RuntimeError("boom")
        return [] if self.trade.isDone() else [self.trade]


CONTRACT = NS(symbol="SPY")


def test_far_limit_price_is_half_of_last_close():
    assert far_limit_price(755.72) == 377.86


def test_happy_path_places_far_limit_then_cancels():
    ib = FakeIB()
    checks = run_roundtrip(ib, CONTRACT, 755.72)
    assert [c.name for c in checks] == ["place", "visible", "cancel", "clean"]
    assert all(c.ok for c in checks)
    order = ib.placed[0]
    assert (order.action, order.totalQuantity, order.lmtPrice) == ("BUY", 1, 377.86)


def test_rejected_order_fails_place_without_needing_cancel():
    ib = FakeIB(status="Inactive")
    ib.trade.orderStatus.status = "Inactive"
    checks = {c.name: c for c in run_roundtrip(ib, CONTRACT, 100.0)}
    assert not checks["place"].ok


def test_order_is_cancelled_even_if_a_step_raises():
    ib = FakeIB(open_raises=True)
    with pytest.raises(RuntimeError):
        run_roundtrip(ib, CONTRACT, 100.0)
    assert ib.cancel_calls == 1 and ib.trade.isDone()
