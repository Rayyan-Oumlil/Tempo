"""A small fake IB for tests: positions, open orders, fills, cancels. No network."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace as NS

from ib_async import Stock

SPY = Stock("SPY", "SMART", "USD", conId=756733)
DONE = {"Filled", "Cancelled", "ApiCancelled", "Inactive"}
# Tuesday 2026-11-03 11:00 ET, regular hours
OPEN_NOW = datetime(2026, 11, 3, 16, 0, tzinfo=timezone.utc)
# Tuesday 2026-11-03 20:00 ET, closed
CLOSED_NOW = datetime(2026, 11, 4, 1, 0, tzinfo=timezone.utc)


class FakeTrade:
    def __init__(self, contract, order, status):
        self.contract = contract
        self.order = order
        self.orderStatus = NS(status=status, filled=0.0, avgFillPrice=0.0)
        self.fills = []

    def isDone(self):
        return self.orderStatus.status in DONE


class FakeIB:
    """fill=True: orders fill at once at `price`. fill=False: they rest as Submitted."""

    def __init__(self, account="DU1234567", fill=True, price=100.0, positions=None, fill_seq=None):
        self.account = account
        self.fill = fill
        self.fill_seq = list(fill_seq or [])  # per-order fill decisions, then falls back to `fill`
        self.cash = {"CAD": 1000.0}
        self.price = price
        self.held = dict(positions or {})  # symbol -> signed quantity
        self.trades = []
        self.placed = []
        self.global_cancels = 0
        self.positions_raise = False
        self._ids = iter(range(1000, 2000))
        self.client = NS(getReqId=lambda: next(self._ids))

    def sleep(self, _):
        pass

    def managedAccounts(self):
        return [self.account]

    def qualifyContracts(self, *contracts):
        return list(contracts)

    def positions(self):
        if self.positions_raise:
            raise RuntimeError("positions unavailable")
        return [NS(contract=Stock(s, "SMART", "USD", conId=756733 if s == "SPY" else 1), position=q, avgCost=self.price)
                for s, q in self.held.items() if q]

    def placeOrder(self, contract, order):
        self.placed.append(order)
        trade = FakeTrade(contract, order, "Submitted")
        if self.fill_seq.pop(0) if self.fill_seq else self.fill:
            sign = 1 if order.action == "BUY" else -1
            self.held[contract.symbol] = self.held.get(contract.symbol, 0) + sign * order.totalQuantity
            trade.orderStatus = NS(status="Filled", filled=order.totalQuantity, avgFillPrice=self.price)
            trade.fills = [NS(commissionReport=NS(commission=1.0))]
        self.trades.append(trade)
        return trade

    def openTrades(self):
        return [t for t in self.trades if not t.isDone()]

    def reqAllOpenOrders(self):
        return self.openTrades()

    def cancelOrder(self, order):
        for t in self.trades:
            if t.order is order and not t.isDone():
                t.orderStatus.status = "Cancelled"

    def reqGlobalCancel(self):
        self.global_cancels += 1
        for t in self.trades:
            if not t.isDone():
                t.orderStatus.status = "Cancelled"

    def reqExecutions(self):
        return [NS(execution=NS(orderRef=t.order.orderRef, shares=t.orderStatus.filled), commissionReport=None)
                for t in self.trades if t.orderStatus.filled]

    def accountValues(self):
        return [NS(tag="TotalCashValue", currency=c, value=str(v)) for c, v in self.cash.items()]
