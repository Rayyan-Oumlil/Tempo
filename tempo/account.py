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
    """Latest daily-bar close, the reference price for the size cap and the price band (not a trading price).

    During regular hours the newest bar is TODAY's, so this is the latest trade (about 15 minutes delayed without a
    data subscription): checked 2026-11-02, SPY 754.84 vs a delayed quote of 755.07. Before the open, or on a day
    the market is closed, it is the previous close.
    """
    bars = ib.reqHistoricalData(contract, "", "5 D", "1 day", "TRADES", useRTH=True, formatDate=1)
    if not bars:
        raise RuntimeError(f"No daily bars for {contract.symbol}; cannot price an entry check")
    return float(bars[-1].close)


PNL_UNSET = 1e300  # ib_async uses about 1.8e308 for "not set"
# Seen live 2026-11-02: right after reqPnL the first callback can carry a STALE figure (-11 while the real daily P&L
# was -151), and the real one follows about a second later. So the value is only read after it has settled.
PNL_SETTLE_SECONDS = 2.0


def _known(value: float) -> bool:
    return value == value and abs(value) < PNL_UNSET  # not NaN, not the "unset" sentinel


def daily_loss_pct(ib, timeout: float = 5.0) -> float:
    """How far the account is down today, as a % of start-of-day equity (negative = up). Raises if unknown.

    Uses IBKR's own daily P&L (realized + unrealized, base currency) rather than our own bookkeeping, and
    start-of-day equity = NetLiquidation - daily P&L. The P&L subscription is always cancelled again.
    Always waits PNL_SETTLE_SECONDS first (never trusts the first callback); `timeout` bounds the total wait.
    """
    net = next((v for v in ib.accountValues() if v.tag == "NetLiquidation" and v.currency != "BASE"), None)
    if net is None:
        raise RuntimeError("Account values lack NetLiquidation: cannot compute the daily loss")
    account = ib.managedAccounts()[0]
    pnl = ib.reqPnL(account)
    try:
        waited = 0.0
        while waited < timeout and (waited < PNL_SETTLE_SECONDS or not _known(pnl.dailyPnL)):
            ib.sleep(0.25)
            waited += 0.25
        daily = pnl.dailyPnL
    finally:
        ib.cancelPnL(account)
    if not _known(daily):
        raise RuntimeError(f"daily P&L not available from IBKR within {timeout:g}s")
    start = float(net.value) - daily
    if start <= 0:
        raise RuntimeError(f"start-of-day equity {start:,.2f} is not positive (NetLiquidation {net.value}, daily P&L {daily})")
    return -daily / start * 100
