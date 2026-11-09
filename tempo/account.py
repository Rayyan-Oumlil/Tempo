"""Account values that need IBKR-specific handling."""
from __future__ import annotations

import weakref

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
# Seen live 2026-11-09: the FIRST P&L answer on a fresh connection took 25.6s once and did not come within 45s three
# other times; once it has come, reads are instant. So whoever needs the P&L to decide something irreversible
# (the entries gate, preflight) waits this long once; the per-order check then finds it already known.
PNL_WARMUP_SECONDS = 60.0


def _known(value: float) -> bool:
    return value == value and abs(value) < PNL_UNSET  # not NaN, not the "unset" sentinel


_PNL_SUBSCRIPTIONS: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()  # one live P&L subscription per connection


def _live_pnl(ib, account: str, timeout: float):
    """The connection's live P&L object, subscribing (and waiting for it to settle) only the first time.

    Seen live 2026-11-09: subscribing and cancelling for every order got no answer within 10s in 14 of 15 tries
    (18 of 22 entries refused), while one long-lived subscription answered at once every time.
    """
    held = _PNL_SUBSCRIPTIONS.get(ib)
    if held is not None and held[0] == account:
        return held[1]
    pnl = ib.reqPnL(account)
    _PNL_SUBSCRIPTIONS[ib] = (account, pnl)
    _wait(ib, timeout, lambda waited: waited < PNL_SETTLE_SECONDS or not _known(pnl.dailyPnL))
    return pnl


def _wait(ib, timeout: float, keep_waiting) -> float:
    waited = 0.0
    while waited < timeout and keep_waiting(waited):
        ib.sleep(0.25)
        waited += 0.25
    return waited


def _drop_pnl(ib, account: str) -> None:
    _PNL_SUBSCRIPTIONS.pop(ib, None)
    ib.cancelPnL(account)


def daily_loss_pct(ib, timeout: float = 5.0) -> float:
    """How far the account is down today, as a % of start-of-day equity (negative = up). Raises if unknown.

    Uses IBKR's own daily P&L (realized + unrealized, base currency) rather than our own bookkeeping, and
    start-of-day equity = NetLiquidation - daily P&L. The subscription stays open for the life of the connection
    and is read live; the first read waits PNL_SETTLE_SECONDS (never trusts the first callback). If the value is
    not known, the subscription is cancelled so the next call starts a fresh one, and this raises.
    """
    net = next((v for v in ib.accountValues() if v.tag == "NetLiquidation" and v.currency != "BASE"), None)
    if net is None:
        raise RuntimeError("Account values lack NetLiquidation: cannot compute the daily loss")
    account = ib.managedAccounts()[0]
    pnl = _live_pnl(ib, account, timeout)
    _wait(ib, timeout, lambda _: not _known(pnl.dailyPnL))  # a held subscription gets the full timeout to recover
    daily = pnl.dailyPnL
    if not _known(daily):
        _drop_pnl(ib, account)
        raise RuntimeError(f"daily P&L not available from IBKR within {timeout:g}s")
    start = float(net.value) - daily
    if start <= 0:
        raise RuntimeError(f"start-of-day equity {start:,.2f} is not positive (NetLiquidation {net.value}, daily P&L {daily})")
    return -daily / start * 100
