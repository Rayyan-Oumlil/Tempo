"""How many shares would the risk rules allow? Read-only; uses the last daily close as the entry price.

Usage: python -m tempo.size SYMBOL STOP_PRICE      e.g. python -m tempo.size SPY 740
"""
from __future__ import annotations

import sys

from dotenv import load_dotenv
from ib_async import Stock

from tempo.account import equity_usd
from tempo.config import load_config
from tempo.ibkr import connect
from tempo.risk import load_rules, position_size


def main(symbol: str, stop: float) -> int:
    load_dotenv()
    rules = load_rules()
    ib = connect(load_config())
    ib.RequestTimeout = 15
    try:
        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        bars = ib.reqHistoricalData(contract, "", "5 D", "1 day", "TRADES", useRTH=True, formatDate=1)
        if not bars:
            raise RuntimeError(f"No daily bars for {symbol}")
        entry = bars[-1].close
        equity = equity_usd(ib)
    finally:
        ib.disconnect()
    result = position_size(equity, entry, stop, rules)
    print(f"Rules:     risk {rules.risk_per_trade_pct}% per trade, max position {rules.max_position_pct}%")
    print(f"Equity:    {equity:,.2f} USD")
    print(f"Entry:     {entry} (last close)   Stop: {stop}   Risk/share: {entry - stop:.2f}")
    print(f"Result:    {result.shares} shares = {result.notional:,.2f} USD, "
          f"risking {result.risk_amount:,.2f} USD (limited by {result.limited_by})")
    if result.shares == 0:
        print(f"Note: 0 shares. Even one share would break the {result.limited_by} limit at this equity.")
    return 0


if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            raise ValueError("usage: python -m tempo.size SYMBOL STOP_PRICE")
        raise SystemExit(main(sys.argv[1].upper(), float(sys.argv[2])))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
