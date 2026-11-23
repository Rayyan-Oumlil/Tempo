"""Read-only probe: which non-stock instruments can this paper account see? NEVER places an order.

Usage: python -m tempo.probe_assets [--only NAME ...]

Plan v3 step 5. For each candidate (spot gold, micro gold, spot BTC and ETH via Paxos, micro BTC future, a stock control)
it asks the Gateway to qualify the contract, return its details, give the earliest history date, ten daily bars and a
delayed snapshot, and prints OK or FAIL with every IB error code, because IB reports most problems as async messages
(200 no security definition, 10168 or 354 market-data subscription, 10197 competing session, 201 or 10311 permissions).
Run it with the Gateway on the paper account, Read-Only API ticked. Paste the output into docs/ibkr-gotchas.md.
"""

from __future__ import annotations

import math
import sys
from collections.abc import Callable

from dotenv import load_dotenv
from ib_async import IB, Commodity, Contract, Crypto, Future, Stock

from tempo.config import load_config
from tempo.ibkr import connect
from tempo.smoke import DELAYED_FROZEN, REQUEST_TIMEOUT_SECONDS, Result, run_test

CANDIDATES: dict[str, Callable[[], Contract]] = {
    "GLD (control: stock)": lambda: Stock("GLD", "SMART", "USD"),
    "XAUUSD spot gold": lambda: Commodity("XAUUSD", "SMART", "USD"),
    "MGC micro gold future": lambda: Future("MGC", "COMEX", currency="USD"),
    "BTC spot (Paxos)": lambda: Crypto("BTC", "PAXOS", "USD"),
    "ETH spot (Paxos)": lambda: Crypto("ETH", "PAXOS", "USD"),
    "MBT micro bitcoin future": lambda: Future("MBT", "CME", currency="USD"),
}


def _resolve(ib: IB, make: Callable[[], Contract]) -> Contract:
    contract = make()
    details = ib.reqContractDetails(contract)
    if not details:
        raise RuntimeError("no contract details returned (error 200 means no such instrument for this account or region)")
    return details[0].contract  # a futures request returns several expiries: the first is enough for a probe


def probe_one(ib: IB, name: str, make: Callable[[], Contract]) -> list[Result]:
    holder: dict[str, Contract] = {}

    def details(ib: IB, _: str) -> str:
        holder["c"] = _resolve(ib, make)
        c = holder["c"]
        d = ib.reqContractDetails(c)[0]
        return f"{c.symbol} {c.secType} {c.exchange} conId={c.conId} expiry={c.lastTradeDateOrContractMonth or '-'} minTick={d.minTick} sizeIncrement={getattr(d, 'sizeIncrement', '?')} tz={d.timeZoneId}"

    def head(ib: IB, _: str) -> str:
        return f"earliest data: {ib.reqHeadTimeStamp(holder['c'], whatToShow='MIDPOINT' if holder['c'].secType in ('CMDTY',) else 'TRADES', useRTH=False)}"

    def bars(ib: IB, _: str) -> str:
        what = "MIDPOINT" if holder["c"].secType in ("CMDTY",) else "TRADES"
        got = ib.reqHistoricalData(holder["c"], "", "10 D", "1 day", what, useRTH=False, formatDate=1)
        if not got:
            raise RuntimeError("no daily bars returned")
        return f"{len(got)} bars ({what}), last {got[-1].date} close={got[-1].close}"

    def snap(ib: IB, _: str) -> str:
        ib.reqMarketDataType(DELAYED_FROZEN)
        (t,) = ib.reqTickers(holder["c"])
        price = t.marketPrice()
        if math.isnan(price) or price <= 0:
            price = t.close
        if math.isnan(price) or price <= 0:
            raise RuntimeError("no price (10168 or 354 means a market-data subscription is missing)")
        return f"price={price} bid={t.bid} ask={t.ask}"

    out = [run_test(ib, "contract details", details, name)]
    if out[0].ok:
        out += [run_test(ib, label, fn, name) for label, fn in (("history start", head), ("daily bars (10D)", bars), ("delayed snapshot", snap))]
    return out


def main(only: list[str]) -> int:
    load_dotenv()
    cfg = load_config()
    ib = connect(cfg)
    ib.RequestTimeout = REQUEST_TIMEOUT_SECONDS
    failed = 0
    try:
        for name, make in CANDIDATES.items():
            if only and not any(o.lower() in name.lower() for o in only):
                continue
            print(f"\n== {name}", flush=True)
            for r in probe_one(ib, name, make):
                print(f"  [{'OK' if r.ok else 'FAIL'}] {r.name:<18} {r.detail}", flush=True)
                failed += 0 if r.ok else 1
    finally:
        ib.disconnect()
    print(f"\n{failed} failed test(s). Paste this output into docs/ibkr-gotchas.md; a FAIL with 200 or a permissions code is an answer, not a bug.")
    return 0


if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        only = args[args.index("--only") + 1 :] if "--only" in args else []
        raise SystemExit(main(only))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
