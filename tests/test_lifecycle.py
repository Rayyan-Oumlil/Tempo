from types import SimpleNamespace as NS

import pytest

from tempo.lifecycle import cash_delta, round_trip_pnl, run_lifecycle


def test_round_trip_pnl_subtracts_both_commissions():
    pnl = round_trip_pnl(buy_price=760.64, sell_price=759.53, qty=1, commissions=2.04)
    assert pnl.gross == pytest.approx(-1.11)
    assert pnl.net == pytest.approx(-3.15)


def test_round_trip_pnl_scales_with_quantity():
    assert round_trip_pnl(100.0, 101.0, 10, 2.0).net == pytest.approx(8.0)


def test_round_trip_pnl_rejects_bad_quantity():
    with pytest.raises(ValueError):
        round_trip_pnl(100.0, 101.0, 0, 0.0)


def test_cash_delta_per_currency_including_new_and_removed():
    before = {"CAD": 1000.0, "USD": 0.0}
    after = {"CAD": 940.0, "USD": 5.0, "EUR": 1.0}
    assert cash_delta(before, after) == {"CAD": -60.0, "USD": 5.0, "EUR": 1.0}


class FakeTrade:
    def __init__(self, action, fill_price, status="Filled"):
        self.order = NS(action=action)
        self.orderStatus = NS(status=status, avgFillPrice=fill_price, filled=1)
        self.fills = [NS(commissionReport=NS(commission=1.0))]

    def isDone(self):
        return self.orderStatus.status in {"Filled", "Cancelled", "ApiCancelled", "Inactive"}


class FakeIB:
    def __init__(self, buy_status="Filled", sell_status="Filled"):
        self.statuses = {"BUY": buy_status, "SELL": sell_status}
        self.prices = {"BUY": 100.0, "SELL": 101.0}
        self.placed = []
        self.cancelled = []
        self.cash = {"CAD": 1000.0}

    def sleep(self, _):
        pass

    def placeOrder(self, contract, order):
        self.placed.append(order.action)
        return FakeTrade(order.action, self.prices[order.action], self.statuses[order.action])

    def cancelOrder(self, order):
        self.cancelled.append(order.action)

    def accountValues(self):
        return [NS(tag="TotalCashBalance", currency=c, value=str(v)) for c, v in self.cash.items()]


CONTRACT = NS(symbol="SPY")


def test_happy_path_buys_then_sells_and_reports_pnl():
    ib = FakeIB()
    result = run_lifecycle(ib, CONTRACT, 1)
    assert ib.placed == ["BUY", "SELL"]
    assert result.pnl.net == pytest.approx(1.0 - 2.0)
    assert all(c.ok for c in result.checks)


def test_unfilled_buy_is_cancelled_and_never_sells():
    ib = FakeIB(buy_status="Submitted")
    result = run_lifecycle(ib, CONTRACT, 1)
    assert ib.placed == ["BUY"] and ib.cancelled == ["BUY"]
    assert result.pnl is None
    assert not all(c.ok for c in result.checks)


def test_unfilled_sell_is_reported_as_failure_with_open_position():
    ib = FakeIB(sell_status="Submitted")
    result = run_lifecycle(ib, CONTRACT, 1)
    assert ib.placed == ["BUY", "SELL"] and ib.cancelled == ["SELL"]
    assert result.pnl is None
    assert any("still long" in c.detail for c in result.checks if not c.ok)
