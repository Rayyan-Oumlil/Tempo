"""Kill switch: block new entries, cancel every order, close every position, confirm flat.

Usage: IBKR_READONLY=0 python -m tempo.kill

1. mode -> reduce_only (new entries are refused until you run: python -m tempo.state normal)
2. reqGlobalCancel (cancels the orders of EVERY client id, see docs/ibkr-gotchas.md), then confirm none remain
3. flatten longs and shorts (regular hours only; when the market is closed the orders are cancelled but the
   positions remain, and the result says so)
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from tempo.config import load_config
from tempo.flatten import SETTLE_SECONDS, flatten_positions
from tempo.health import Check
from tempo.hours import is_regular_hours
from tempo.ibkr import connect
from tempo.ibutil import default_journal, default_limits, wait_until
from tempo.journal import Journal
from tempo.orders import Limits
from tempo.state import STATE_FILE, set_mode


def kill(ib, *, journal: Journal, limits: Limits, state_path: Path = STATE_FILE, now: datetime | None = None,
         wait_seconds: float = 30.0) -> list[Check]:
    set_mode("reduce_only", "kill switch", state_path)
    checks = [Check("mode", True, "reduce_only: no new entries")]
    ib.reqGlobalCancel()
    cancelled = wait_until(ib, lambda: not ib.reqAllOpenOrders(), SETTLE_SECONDS)
    checks.append(Check("cancel", cancelled, "no open orders" if cancelled else f"{len(ib.reqAllOpenOrders())} still open"))
    open_positions = [p for p in ib.positions() if p.position]
    if open_positions and not is_regular_hours(now):
        checks.append(Check("flatten", False, f"market closed: {len(open_positions)} position(s) remain "
                            "(orders were cancelled; flatten when the market opens)"))
        return checks
    return checks + flatten_positions(ib, journal=journal, limits=limits, state_path=state_path, now=now,
                                      wait_seconds=wait_seconds)


def main() -> int:
    load_dotenv()
    cfg = load_config()
    if cfg.readonly:
        raise RuntimeError("Kill needs IBKR_READONLY=0 (and Read-Only API unticked in Gateway)")
    ib = connect(cfg)
    ib.RequestTimeout = 15
    try:
        checks = kill(ib, journal=default_journal(), limits=default_limits())
    finally:
        ib.disconnect()
    for c in checks:
        print(f"[{'OK' if c.ok else 'FAIL'}] {c.name:<12} {c.detail}", flush=True)
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
