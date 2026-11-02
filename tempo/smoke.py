"""Read-only IBKR API smoke tests: one per API capability. NEVER places an order.

Usage: python -m tempo.smoke [SYMBOL] [--what-if]      (default SPY)
--what-if adds a commission/margin what-if order (needs IBKR_READONLY=0; still places nothing).

Each test prints OK/FAIL plus any IB error codes it triggered (errorEvent), because
IB reports most problems as async error messages, not exceptions.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Callable

from dotenv import load_dotenv
from ib_async import IB, LimitOrder, Stock

from tempo.config import load_config
from tempo.ibkr import connect

DELAYED_FROZEN = 4  # works with no market-data subscription, also when the market is closed
REQUEST_TIMEOUT_SECONDS = 15
INFO_CODES = {2104, 2106, 2158, 2119}  # "data farm connection is OK" notices, not errors


@dataclass(frozen=True)
class Result:
    name: str
    ok: bool
    detail: str


def _stock(symbol: str) -> Stock:
    return Stock(symbol, "SMART", "USD")


def t_qualify(ib: IB, symbol: str) -> str:
    contract = _stock(symbol)
    if not ib.qualifyContracts(contract):
        raise RuntimeError(f"{symbol} could not be qualified")
    return f"conId={contract.conId} primaryExch={contract.primaryExchange} currency={contract.currency}"


def t_contract_details(ib: IB, symbol: str) -> str:
    details = ib.reqContractDetails(_stock(symbol))
    if not details:
        raise RuntimeError("no contract details returned")
    d = details[0]
    return f"{d.longName} | minTick={d.minTick} | tz={d.timeZoneId} | hours={d.tradingHours.split(';')[0]}"


def t_snapshot(ib: IB, symbol: str) -> str:
    ib.reqMarketDataType(DELAYED_FROZEN)
    contract = _stock(symbol)
    ib.qualifyContracts(contract)
    (ticker,) = ib.reqTickers(contract)
    price = ticker.marketPrice()
    if math.isnan(price) or price <= 0:
        price = ticker.close  # market closed or no live quote: fall back to the last close
    if math.isnan(price) or price <= 0:
        raise RuntimeError("no price returned (see error codes: 10089/10167/354 = market-data subscription issue)")
    return f"price={price} bid={ticker.bid} ask={ticker.ask} close={ticker.close} (type {DELAYED_FROZEN})"


def t_head_timestamp(ib: IB, symbol: str) -> str:
    contract = _stock(symbol)
    ib.qualifyContracts(contract)
    return f"earliest data: {ib.reqHeadTimeStamp(contract, whatToShow='TRADES', useRTH=True)}"


def t_daily_bars(ib: IB, symbol: str) -> str:
    contract = _stock(symbol)
    ib.qualifyContracts(contract)
    bars = ib.reqHistoricalData(contract, "", "10 D", "1 day", "TRADES", useRTH=True, formatDate=1)
    if not bars:
        raise RuntimeError("no bars returned")
    last = bars[-1]
    return f"{len(bars)} bars, last {last.date} O={last.open} H={last.high} L={last.low} C={last.close} V={last.volume}"


def t_what_if(ib: IB, symbol: str) -> str:
    """Asks IB for commission + margin impact of a 1-share buy. Nothing is sent to the market."""
    contract = _stock(symbol)
    ib.qualifyContracts(contract)
    state = ib.whatIfOrder(contract, LimitOrder("BUY", 1, 1.00))
    return f"commission={state.commission} {state.commissionCurrency} initMarginChange={state.initMarginChange}"


TESTS: tuple[tuple[str, Callable[[IB, str], str]], ...] = (
    ("qualify contract", t_qualify),
    ("contract details", t_contract_details),
    ("market data snapshot", t_snapshot),
    ("history start date", t_head_timestamp),
    ("daily bars (10D)", t_daily_bars),
)
# Gateway treats even a what-if as an order attempt: on a read-only API it pops a modal dialog and the
# request hangs. So it only runs on request, and only with IBKR_READONLY=0.
WHAT_IF_TEST = ("what-if order", t_what_if)


def run_test(ib: IB, name: str, fn: Callable[[IB, str], str], symbol: str) -> Result:
    codes: list[str] = []

    def on_error(req_id, code, msg, *_):
        if code not in INFO_CODES:
            codes.append(f"[{code}] {msg}")

    ib.errorEvent += on_error
    try:
        detail, ok = fn(ib, symbol), True
    except Exception as exc:  # noqa: BLE001 - a failed test must report, not crash the run
        detail, ok = f"{type(exc).__name__}: {exc}", False
    finally:
        ib.errorEvent -= on_error
    return Result(name, ok, detail + (f"  IB: {' | '.join(codes)}" if codes else ""))


def main(symbol: str, what_if: bool = False) -> int:
    load_dotenv()
    cfg = load_config()
    if what_if and cfg.readonly:
        raise RuntimeError("--what-if needs IBKR_READONLY=0 in .env (and Read-Only API unticked in Gateway)")
    tests = TESTS + ((WHAT_IF_TEST,) if what_if else ())
    ib = connect(cfg)
    ib.RequestTimeout = REQUEST_TIMEOUT_SECONDS  # default is no timeout: a silent subscription gap would hang forever
    results = []
    try:
        for name, fn in tests:
            r = run_test(ib, name, fn, symbol)
            print(f"[{'OK' if r.ok else 'FAIL'}] {r.name:<22} {r.detail}", flush=True)
            results.append(r)
    finally:
        ib.disconnect()
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    try:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        raise SystemExit(main(args[0].upper() if args else "SPY", what_if="--what-if" in sys.argv))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
