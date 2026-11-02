"""Flatten: close open positions (longs with a market SELL, shorts with a market BUY) and report the fills.

Usage: IBKR_READONLY=0 python -m tempo.flatten [SYMBOL]      (default: all positions)

Regular trading hours only (market orders are rejected on the overnight venue, see docs/ibkr-gotchas.md).
Resting orders for a symbol are cancelled first, so a leftover stop cannot fire after the position is closed and
open a new one. Paper accounts only (tempo.orders.place refuses anything else).
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from ib_async import MarketOrder

from tempo.config import load_config
from tempo.health import Check
from tempo.ibkr import connect
from tempo.ibutil import default_journal, default_limits, wait_until
from tempo.journal import Journal
from tempo.orders import Limits, OrderRefused, place, record_outcome
from tempo.state import STATE_FILE

WAIT_SECONDS = 30.0
SETTLE_SECONDS = 10.0


def _open_positions(ib, symbol):
    return [p for p in ib.positions() if p.position and (symbol is None or p.contract.symbol == symbol)]


def cancel_symbol_orders(ib, symbol: str, timeout: float = SETTLE_SECONDS) -> tuple[int, int]:
    """Cancel every resting order for a symbol (all bracket legs together, never one).

    Returns (how many cancels were sent, how many orders are STILL resting afterwards). A non-zero second number
    means a cancel was not confirmed in time.
    """
    def resting():
        return [t for t in ib.reqAllOpenOrders() if t.contract.symbol == symbol]

    targets = resting()
    for t in targets:
        ib.cancelOrder(t.order)
    wait_until(ib, lambda: not resting(), timeout)
    return len(targets), len(resting())


def _close_one(ib, pos, *, journal, limits, state_path, now, wait_seconds) -> Check:
    contract = pos.contract
    symbol = contract.symbol
    cancelled, still_resting = cancel_symbol_orders(ib, symbol)
    action = "SELL" if pos.position > 0 else "BUY"
    if still_resting:
        # Selling now could double up with an exit that is still live and flip the account the other way.
        return Check(f"{action} {symbol}", False,
                     f"cancel not confirmed: {still_resting} order(s) still resting; NOT selling. "
                     "Check Gateway, then run flatten again")
    ib.qualifyContracts(contract)
    qty = abs(int(pos.position))
    try:
        trade = place(ib, contract, MarketOrder(action, qty, orderRef="tempo-flatten"), reason="flatten",
                      journal=journal, limits=limits, state_path=state_path, now=now)
    except OrderRefused as exc:
        return Check(f"{action} {symbol}", False, f"refused: {exc}")
    done = wait_until(ib, trade.isDone, wait_seconds)
    if not done:
        ib.cancelOrder(trade.order)
        wait_until(ib, trade.isDone, SETTLE_SECONDS)
    record_outcome(journal, trade)
    status = trade.orderStatus
    filled = status.status == "Filled"
    note = f", cancelled {cancelled} resting order(s) first" if cancelled else ""
    return Check(f"{action} {symbol}", filled,
                 f"{qty} @ {status.avgFillPrice} (avg cost {pos.avgCost:.2f}) status={status.status}{note}")


def flatten_positions(ib, *, journal: Journal, limits: Limits, state_path: Path = STATE_FILE,
                      symbol: str | None = None, now: datetime | None = None,
                      wait_seconds: float = WAIT_SECONDS) -> list[Check]:
    """Close positions once each, wait for the position feed to settle, then confirm flat.

    There is deliberately no retry: a lagging position feed plus a retry is how a flatten becomes a new short.
    If something is still open the result says so and you decide.
    """
    todo = _open_positions(ib, symbol)
    if not todo:
        return [Check("positions", True, "nothing to close")]
    checks = [_close_one(ib, pos, journal=journal, limits=limits, state_path=state_path, now=now,
                         wait_seconds=wait_seconds) for pos in todo]
    wait_until(ib, lambda: not _open_positions(ib, symbol), SETTLE_SECONDS)
    left = _open_positions(ib, symbol)
    checks.append(Check("flat", not left, "no positions left" if not left else
                        "still open: " + ", ".join(f"{p.contract.symbol} {p.position:+g}" for p in left)))
    return checks


def main(symbol: str | None) -> int:
    load_dotenv()
    cfg = load_config()
    if cfg.readonly:
        raise RuntimeError("Flatten needs IBKR_READONLY=0 (and Read-Only API unticked in Gateway)")
    ib = connect(cfg)
    ib.RequestTimeout = 15
    try:
        checks = flatten_positions(ib, journal=default_journal(), limits=default_limits(), symbol=symbol)
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
