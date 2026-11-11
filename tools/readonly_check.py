"""Read-only look at whatever account IB Gateway is logged into (paper or live). Sends nothing, ever.

Usage: python tools/readonly_check.py [PORT]      (4002 = Gateway paper, 4001 = Gateway live; default: tries 4001 then 4002)

Deliberately separate from tempo/ibkr.py, whose paper-only guard must stay as it is. Three layers keep this from
trading: (1) tick Read-Only API in Gateway (Configure > Settings > API); (2) this script never calls an order function
and replaces placeOrder with one that raises; (3) it prints only totals, never the account number.
"""
from __future__ import annotations

import sys

from ib_async import IB

CLIENT_ID = 84  # not Tempo's 21, so it cannot collide with the scheduled jobs


def _refuse(*_a, **_k):
    raise RuntimeError("readonly_check never places orders")


def main(argv: list[str]) -> int:
    ports = [int(argv[0])] if argv else [4001, 4002]
    ib = IB()
    ib.placeOrder = _refuse  # type: ignore[method-assign]
    ib.cancelOrder = _refuse  # type: ignore[method-assign]
    ib.reqGlobalCancel = _refuse  # type: ignore[method-assign]
    for port in ports:
        try:
            ib.connect("127.0.0.1", port, clientId=CLIENT_ID, timeout=20, readonly=True)
            break
        except (OSError, TimeoutError) as exc:
            print(f"port {port}: not reachable ({type(exc).__name__})")
    else:
        print("[FAIL] no Gateway reachable. Is it logged in, with the API socket enabled?")
        return 1
    try:
        accounts = ib.managedAccounts()
        paper = bool(accounts) and accounts[0].startswith(("DU", "DF"))
        print(f"port {port} | account type: {'PAPER' if paper else 'LIVE'} | accounts: {len(accounts)}")
        summary = {v.tag: (v.value, v.currency) for v in ib.accountSummary() if v.currency != "BASE"}
        for tag in ("AccountType", "NetLiquidation", "TotalCashValue", "AvailableFunds", "BuyingPower"):
            if tag in summary:
                value, cur = summary[tag]
                print(f"  {tag:<16} {value} {cur}".rstrip())
        portfolio = ib.portfolio()
        print(f"  positions        {len(portfolio)}")
        print(f"  open orders      {len(ib.reqAllOpenOrders())}")
        print(f"  server time      {ib.reqCurrentTime():%Y-%m-%d %H:%M:%S} UTC")
    finally:
        ib.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
