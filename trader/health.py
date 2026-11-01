"""Read-only account health check. NEVER places orders.

Usage: python -m trader.health
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone

from dotenv import load_dotenv

from trader.config import load_config
from trader.ibkr import PAPER_PREFIXES, connect

MAX_CLOCK_SKEW_SECONDS = 5.0
SUMMARY_TAGS = ("NetLiquidation", "TotalCashValue", "BuyingPower", "AvailableFunds")


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def run_health(ib) -> list[Check]:
    accounts = ib.managedAccounts()
    account_id = accounts[0] if accounts else ""
    checks = [Check("account", account_id.startswith(PAPER_PREFIXES), f"{account_id or 'none'} (paper expected)")]

    summary = {v.tag: v for v in ib.accountSummary() if v.tag in SUMMARY_TAGS}
    net = summary.get("NetLiquidation")
    if net is None:
        checks.append(Check("equity", False, "NetLiquidation missing from account summary"))
    else:
        checks.append(Check("equity", float(net.value) > 0, f"{float(net.value):,.2f} {net.currency}"))
    for tag in SUMMARY_TAGS[1:]:
        v = summary.get(tag)
        checks.append(Check(tag, v is not None, f"{float(v.value):,.2f} {v.currency}" if v else "missing"))

    skew = abs((datetime.now(timezone.utc) - ib.reqCurrentTime()).total_seconds())
    checks.append(Check("clock", skew <= MAX_CLOCK_SKEW_SECONDS, f"skew vs IB server {skew:.1f}s"))

    positions = [p for p in ib.positions() if p.position]
    checks.append(Check("positions", True, f"{len(positions)} open"))
    checks.append(Check("open orders", True, f"{len(ib.openTrades())} open"))
    return checks


def main() -> int:
    load_dotenv()
    ib = connect(load_config())
    try:
        checks = run_health(ib)
    finally:
        ib.disconnect()
    for c in checks:
        print(f"[{'OK' if c.ok else 'FAIL'}] {c.name:<15} {c.detail}")
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
