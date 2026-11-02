"""Trade lifecycle: market BUY, confirm the fill, market SELL, report P&L and cash by currency.

Usage: IBKR_READONLY=0 python -m tempo.lifecycle [SYMBOL] [QTY]      (default SPY 1)

Regular trading hours only (market orders are rejected on the overnight venue, see docs/ibkr-gotchas.md).
Paper accounts only (tempo.ibkr.connect refuses anything else). If the BUY does not fill it is cancelled and
nothing is sold; if the SELL does not fill it is cancelled and the result says you are still long.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from ib_async import MarketOrder, Stock

from tempo.config import load_config
from tempo.health import Check
from tempo.ibkr import connect

ORDER_REF = "tempo-lifecycle"
WAIT_SECONDS = 30.0
POLL_SECONDS = 0.5


@dataclass(frozen=True)
class Pnl:
    gross: float  # price difference only
    net: float  # after commissions


@dataclass(frozen=True)
class LifecycleResult:
    checks: list[Check]
    pnl: Pnl | None  # None unless both legs filled
    cash_change: dict[str, float]


def round_trip_pnl(buy_price: float, sell_price: float, qty: int, commissions: float) -> Pnl:
    if qty <= 0:
        raise ValueError(f"qty must be positive, got {qty}")
    gross = (sell_price - buy_price) * qty
    return Pnl(gross=gross, net=gross - commissions)


def cash_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    return {c: after.get(c, 0.0) - before.get(c, 0.0) for c in sorted(before.keys() | after.keys())}


def _cash_by_currency(ib) -> dict[str, float]:
    return {v.currency: float(v.value) for v in ib.accountValues() if v.tag == "TotalCashValue" and v.currency != "BASE"}


def _wait(ib, predicate, timeout: float = WAIT_SECONDS) -> bool:
    waited = 0.0
    while waited < timeout and not predicate():
        ib.sleep(POLL_SECONDS)
        waited += POLL_SECONDS
    return predicate()


def _commission(trade) -> float:
    return sum(f.commissionReport.commission for f in trade.fills)


def _leg(ib, contract, action: str, qty: int):
    trade = ib.placeOrder(contract, MarketOrder(action, qty, tif="DAY", orderRef=ORDER_REF))
    filled = _wait(ib, trade.isDone) and trade.orderStatus.status == "Filled"
    if not filled:
        ib.cancelOrder(trade.order)
    return trade, filled


def run_lifecycle(ib, contract, qty: int) -> LifecycleResult:
    cash_before = _cash_by_currency(ib)
    checks: list[Check] = []

    buy, bought = _leg(ib, contract, "BUY", qty)
    buy_price = buy.orderStatus.avgFillPrice
    checks.append(Check("buy", bought, f"{qty} {contract.symbol} @ {buy_price} status={buy.orderStatus.status}"))
    if not bought:
        return LifecycleResult(checks, None, {})

    sell, sold = _leg(ib, contract, "SELL", qty)
    sell_price = sell.orderStatus.avgFillPrice
    detail = f"{qty} {contract.symbol} @ {sell_price} status={sell.orderStatus.status}"
    checks.append(Check("sell", sold, detail if sold else f"{detail}; still long {qty}, run tempo.flatten"))
    if not sold:
        return LifecycleResult(checks, None, {})

    ib.sleep(2)  # account values lag the fill slightly
    pnl = round_trip_pnl(buy_price, sell_price, qty, _commission(buy) + _commission(sell))
    change = cash_delta(cash_before, _cash_by_currency(ib))
    checks.append(Check("pnl", True, f"gross {pnl.gross:+.2f} net {pnl.net:+.2f} USD (commissions {pnl.gross - pnl.net:.2f})"))
    checks.append(Check("cash", True, ", ".join(f"{c} {d:+,.2f}" for c, d in change.items())))
    return LifecycleResult(checks, pnl, change)


def main(symbol: str, qty: int) -> int:
    load_dotenv()
    cfg = load_config()
    if cfg.readonly:
        raise RuntimeError("Lifecycle needs IBKR_READONLY=0 (and Read-Only API unticked in Gateway)")
    ib = connect(cfg)
    ib.RequestTimeout = 15
    try:
        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        result = run_lifecycle(ib, contract, qty)
    finally:
        ib.disconnect()
    for c in result.checks:
        print(f"[{'OK' if c.ok else 'FAIL'}] {c.name:<6} {c.detail}", flush=True)
    return 0 if all(c.ok for c in result.checks) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1].upper() if len(sys.argv) > 1 else "SPY",
                              int(sys.argv[2]) if len(sys.argv) > 2 else 1))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
