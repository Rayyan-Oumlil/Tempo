"""Flatten: close every long position with a market SELL and report the fills.

Usage: IBKR_READONLY=0 python -m tempo.flatten [SYMBOL]      (default: all positions)

Regular trading hours only (market orders are rejected on the overnight venue, see docs/ibkr-gotchas.md).
Paper accounts only (tempo.ibkr.connect refuses anything else).
"""
from __future__ import annotations

import sys

from dotenv import load_dotenv
from ib_async import IB, MarketOrder

from tempo.config import load_config
from tempo.health import Check
from tempo.ibkr import connect

ORDER_REF = "tempo-flatten"
WAIT_SECONDS = 30.0
POLL_SECONDS = 0.5


def _wait(ib, predicate, timeout: float = WAIT_SECONDS) -> bool:
    waited = 0.0
    while waited < timeout and not predicate():
        ib.sleep(POLL_SECONDS)
        waited += POLL_SECONDS
    return predicate()


def flatten(ib: IB, symbol: str | None = None) -> list[Check]:
    positions = [p for p in ib.positions() if p.position > 0 and (symbol is None or p.contract.symbol == symbol)]
    if not positions:
        return [Check("positions", True, "nothing to close")]
    checks: list[Check] = []
    for pos in positions:
        contract = pos.contract
        ib.qualifyContracts(contract)
        qty = int(pos.position)
        trade = ib.placeOrder(contract, MarketOrder("SELL", qty, tif="DAY", orderRef=ORDER_REF))
        done = _wait(ib, trade.isDone)
        status = trade.orderStatus.status
        fill = trade.orderStatus.avgFillPrice
        commission = sum(f.commissionReport.commission for f in trade.fills)
        checks.append(Check(f"sell {contract.symbol}", done and status == "Filled",
                            f"{qty} @ {fill} (avg cost {pos.avgCost:.2f}) status={status} commission={commission:.2f}"))
        if not done:
            ib.cancelOrder(trade.order)
    return checks


def main(symbol: str | None) -> int:
    load_dotenv()
    cfg = load_config()
    if cfg.readonly:
        raise RuntimeError("Flatten needs IBKR_READONLY=0 (and Read-Only API unticked in Gateway)")
    ib = connect(cfg)
    ib.RequestTimeout = 15
    try:
        checks = flatten(ib, symbol)
    finally:
        ib.disconnect()
    for c in checks:
        print(f"[{'OK' if c.ok else 'FAIL'}] {c.name:<12} {c.detail}", flush=True)
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1].upper() if len(sys.argv) > 1 else None))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
