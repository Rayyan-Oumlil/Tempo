"""Account values that need IBKR-specific handling."""
from __future__ import annotations

from ib_async import Forex


def _forex_usd_rate(ib, currency: str) -> float:
    """Units of `currency` per 1 USD, from the last daily USD.<currency> midpoint bar."""
    pair = Forex(f"USD{currency}")
    ib.qualifyContracts(pair)
    bars = ib.reqHistoricalData(pair, "", "5 D", "1 day", "MIDPOINT", useRTH=True, formatDate=1)
    if not bars:
        raise RuntimeError(f"No USD.{currency} rate available to convert equity to USD")
    return float(bars[-1].close)


def equity_usd(ib) -> float:
    """Net liquidation in USD. The base currency may be CAD but US stocks are priced in USD.

    IBKR only lists an ExchangeRate for currencies the account holds, so a CAD-only paper account has no
    USD rate; then the USD.CAD forex price is used instead.
    """
    values = ib.accountValues()
    net = next((v for v in values if v.tag == "NetLiquidation" and v.currency != "BASE"), None)
    if net is None:
        raise RuntimeError(f"Account values lack NetLiquidation ({len(values)} values received)")
    amount = float(net.value)
    if net.currency == "USD":
        return amount
    rates = {v.currency: float(v.value) for v in values if v.tag == "ExchangeRate"}  # base units per 1 currency
    if "USD" in rates:
        return amount * rates.get(net.currency, 1.0) / rates["USD"]
    return amount / _forex_usd_rate(ib, net.currency)


def last_close(ib, contract) -> float:
    """Last daily close, used as the reference price for position-size checks (not for trading decisions)."""
    bars = ib.reqHistoricalData(contract, "", "5 D", "1 day", "TRADES", useRTH=True, formatDate=1)
    if not bars:
        raise RuntimeError(f"No daily bars for {contract.symbol}; cannot price an entry check")
    return float(bars[-1].close)
