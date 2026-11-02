"""Paper order round trip: place a 1-share limit BUY far below market (it cannot fill), watch it, cancel it.

Usage: IBKR_READONLY=0 python -m tempo.roundtrip [SYMBOL]      (default SPY)

Needs 'Read-Only API' unticked in Gateway (Configure > Settings > API > Settings). Paper accounts only
(tempo.ibkr.connect refuses anything else). The order is always cancelled again, even if a step fails.
"""
from __future__ import annotations

import sys

from dotenv import load_dotenv
from ib_async import IB, Contract, LimitOrder, Stock

from tempo.config import load_config
from tempo.health import Check
from tempo.ibkr import connect

ORDER_REF = "tempo-roundtrip"
PRICE_FRACTION = 0.5  # limit at half the last close: far enough below the market to never fill
WAIT_SECONDS = 20.0
POLL_SECONDS = 0.5
ACTIVE = {"PreSubmitted", "Submitted"}
CANCELLED = {"Cancelled", "ApiCancelled"}


def far_limit_price(last_close: float) -> float:
    return round(last_close * PRICE_FRACTION, 2)


def _wait(ib, predicate, timeout: float = WAIT_SECONDS) -> bool:
    waited = 0.0
    while waited < timeout and not predicate():
        ib.sleep(POLL_SECONDS)
        waited += POLL_SECONDS
    return predicate()


def _is_open(ib, order_id: int) -> bool:
    return any(t.order.orderId == order_id for t in ib.openTrades())


def run_roundtrip(ib, contract: Contract, last_close: float) -> list[Check]:
    price = far_limit_price(last_close)
    order = LimitOrder("BUY", 1, price, tif="DAY", orderRef=ORDER_REF)
    checks: list[Check] = []
    trade = None
    try:
        trade = ib.placeOrder(contract, order)
        accepted = _wait(ib, lambda: trade.orderStatus.status in ACTIVE | CANCELLED | {"Inactive", "Filled"})
        status = trade.orderStatus.status
        checks.append(Check("place", accepted and status in ACTIVE, f"BUY 1 {contract.symbol} @ {price} -> {status}"))
        checks.append(Check("visible", _is_open(ib, trade.order.orderId), f"orderId={trade.order.orderId} in open orders"))
    finally:
        if trade is not None and not trade.isDone():
            ib.cancelOrder(trade.order)
    if trade is not None:
        cancelled = _wait(ib, trade.isDone)
        status = trade.orderStatus.status
        checks.append(Check("cancel", cancelled and status in CANCELLED, f"status -> {status}"))
        checks.append(Check("clean", not _is_open(ib, trade.order.orderId) and trade.orderStatus.filled == 0,
                            f"no open order left, filled={trade.orderStatus.filled}"))
    return checks


def main(symbol: str) -> int:
    load_dotenv()
    cfg = load_config()
    if cfg.readonly:
        raise RuntimeError("Round trip needs IBKR_READONLY=0 (and Read-Only API unticked in Gateway)")
    ib = connect(cfg)
    ib.RequestTimeout = 15
    try:
        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        bars = ib.reqHistoricalData(contract, "", "5 D", "1 day", "TRADES", useRTH=True, formatDate=1)
        if not bars:
            raise RuntimeError(f"No daily bars for {symbol}; cannot price a safe limit order")
        checks = run_roundtrip(ib, contract, bars[-1].close)
    finally:
        ib.disconnect()
    for c in checks:
        print(f"[{'OK' if c.ok else 'FAIL'}] {c.name:<8} {c.detail}", flush=True)
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1].upper() if len(sys.argv) > 1 else "SPY"))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
