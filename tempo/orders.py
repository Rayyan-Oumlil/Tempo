"""The one door for orders. Every Tempo order goes through `place`; nothing else calls `ib.placeOrder`.

Rules (a script cannot skip them, because they live here):
  * paper accounts only
  * tif is always explicit and every order gets a unique orderRef (so reconcile can find it later)
  * an identical order inside a short window is refused
  * the intent is journaled BEFORE the order is sent
  * ENTRIES (orders that add exposure) additionally need: mode `normal`, no stale unresolved intents, regular
    hours (unless outsideRth), a known equity and price, and a size under the position cap. If an input is
    missing the entry is refused (fail closed).
  * EXITS (orders that reduce a live position) are never refused by those limits. "Exit" is decided from the
    live broker position, never from the caller's say-so; if positions cannot be read, it counts as an entry.
"""
from __future__ import annotations

import copy
import uuid
import weakref
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tempo.account import daily_loss_pct
from tempo.hours import CALENDAR_THROUGH, calendar_covers, is_regular_hours
from tempo.ibkr import assert_paper
from tempo.journal import STALE_INTENT_SECONDS, Journal
from tempo.state import STATE_FILE, get_mode


class OrderRefused(RuntimeError):
    """A Tempo rule stopped this order. Nothing was sent."""


@dataclass(frozen=True)
class Limits:
    max_position_pct: float  # largest entry, as % of equity
    duplicate_window_s: float = 5.0
    max_daily_loss_pct: float | None = None  # None switches the check off (offline tests only; rules.json always sets it)
    price_band_pct: float = 10.0  # a limit that could fill this far on the wrong side of the reference price is refused
    stale_intent_s: float = STALE_INTENT_SECONDS  # an unresolved intent older than this blocks entries until reconciled


def is_exit(ib, contract, order) -> bool:
    """True only if the order reduces a live position AND fits in what other resting orders have not already claimed.

    Example: long 5 with a resting SELL 5. A second SELL 1 is not an exit, because both could fill and flip the
    account short. Orders from every client id count (reqAllOpenOrders). If positions or open orders cannot be
    read, the answer is False (treated as an entry, which is the stricter path).
    """
    try:
        held = sum(p.position for p in ib.positions() if _same(p.contract, contract))
        committed = _committed(ib.reqAllOpenOrders(), contract, order.action)
    except Exception:  # noqa: BLE001 - unreadable state must not be treated as an exit
        return False
    qty = order.totalQuantity
    if order.action == "SELL":
        return held > 0 and qty <= held - committed
    return held < 0 and qty <= -held - committed


def _committed(open_trades, contract, action: str) -> float:
    """Size already claimed by resting orders on this side. An OCA group (ocaType 1: one fill cancels the rest)
    can only ever fill one leg, so it claims its largest leg, not the sum; everything else adds up."""
    loose = 0.0
    groups: dict[str, float] = {}
    for t in open_trades:
        if not (_same(t.contract, contract) and t.order.action == action):
            continue
        remaining = t.order.totalQuantity - t.orderStatus.filled
        if t.order.ocaGroup and t.order.ocaType == 1:
            groups[t.order.ocaGroup] = max(groups.get(t.order.ocaGroup, 0.0), remaining)
        else:
            loose += remaining
    return loose + sum(groups.values())


def _same(a, b) -> bool:
    if getattr(a, "conId", 0) and getattr(b, "conId", 0):
        return a.conId == b.conId
    return a.symbol == b.symbol and a.secType == b.secType


def _price(value) -> float | None:
    """ib_async uses a huge float (about 1.8e308) for 'not set'; store that as None."""
    return None if value is None or value >= 1e300 else value


def _fingerprint(contract, order) -> tuple:
    return (contract.symbol, order.action, order.orderType, order.totalQuantity,
            _price(order.lmtPrice) or 0, _price(order.auxPrice) or 0)


def _check_entry(ib, order, *, journal: Journal, state_path: Path, limits: Limits, equity_usd, ref_price, now) -> None:
    if get_mode(state_path) != "normal":
        raise OrderRefused("mode is reduce_only: new entries are blocked (python -m tempo.state normal to resume)")
    stale = [r for r in journal.unresolved() if journal.now() - r["ts"] > limits.stale_intent_s]
    if stale:
        raise OrderRefused(f"{len(stale)} unresolved order(s) in the journal: run python -m tempo.reconcile first")
    if not order.outsideRth:
        if not calendar_covers(now):
            raise OrderRefused(f"market calendar only covers through {CALENDAR_THROUGH}: update tempo/hours.py")
        if not is_regular_hours(now):
            raise OrderRefused("market is closed (entries need regular hours or outsideRth=True)")
    if not equity_usd or equity_usd <= 0:
        raise OrderRefused("equity unknown: refusing a new entry")
    if not ref_price or ref_price <= 0:
        raise OrderRefused("reference price unknown: refusing a new entry")
    limit = _price(order.lmtPrice)
    band = limits.price_band_pct / 100
    if limit and order.action == "BUY" and limit > ref_price * (1 + band):
        raise OrderRefused(f"buy limit {limit} is more than {limits.price_band_pct:g}% above the reference price {ref_price}")
    if limit and order.action == "SELL" and limit < ref_price * (1 - band):
        raise OrderRefused(f"sell limit {limit} is more than {limits.price_band_pct:g}% below the reference price {ref_price}")
    stop = _price(order.auxPrice) if order.orderType in ("STP", "STP LMT") else None
    worst_price = max(p for p in (ref_price, limit, stop) if p)  # size the cap at the highest price the order could pay
    cap = equity_usd * limits.max_position_pct / 100
    if order.totalQuantity * worst_price > cap:
        raise OrderRefused(f"entry {order.totalQuantity * worst_price:,.0f} exceeds position cap {cap:,.0f} USD")
    if limits.max_daily_loss_pct is not None:  # last, because it asks the broker
        try:
            loss = daily_loss_pct(ib)
        except Exception as exc:  # noqa: BLE001 - an unknown P&L must block new risk
            raise OrderRefused(f"daily P&L unknown ({exc}): refusing a new entry") from exc
        if loss >= limits.max_daily_loss_pct:
            raise OrderRefused(f"daily loss limit hit: down {loss:.2f}% today (limit {limits.max_daily_loss_pct:.1f}%); "
                               "exits are still allowed")


def _check_duplicate(contract, order, journal: Journal, window_s: float) -> None:
    fp = _fingerprint(contract, order)
    for r in journal.records():
        if r.get("kind") == "intent" and journal.now() - r["ts"] <= window_s and tuple(r.get("fp", ())) == fp:
            raise OrderRefused(f"duplicate of an order sent {journal.now() - r['ts']:.1f}s ago")


def dispatch(ib, contract, order, *, reason: str, journal: Journal, limits: Limits, exit_order: bool):
    """Journal the intent, send, journal `sent`. Callers must have run the rules first (see `place`)."""
    _check_duplicate(contract, order, journal, limits.duplicate_window_s)
    sendable = copy.copy(order)
    sendable.tif = order.tif or "DAY"
    sendable.orderRef = f"{order.orderRef or 'tempo'}-{uuid.uuid4().hex[:10]}"
    journal.append("intent", ref=sendable.orderRef, symbol=contract.symbol, action=order.action,
                   qty=order.totalQuantity, order_type=order.orderType, lmt=_price(order.lmtPrice), aux=_price(order.auxPrice),
                   reason=reason, exit=exit_order, fp=list(_fingerprint(contract, order)))
    try:
        trades = watch_order_errors(ib)
        trade = ib.placeOrder(contract, sendable)
        trades[trade.order.orderId] = trade
    except Exception as exc:
        journal.append("outcome", ref=sendable.orderRef, status="error", error=repr(exc))
        raise
    journal.append("sent", ref=sendable.orderRef, order_id=sendable.orderId)
    return trade


def place(ib, contract, order, *, reason: str, journal: Journal, limits: Limits, equity_usd: float | None = None,
          ref_price: float | None = None, now: datetime | None = None, state_path: Path = STATE_FILE):
    accounts = ib.managedAccounts()
    assert_paper(accounts[0] if accounts else "none")
    with journal.lock():  # the checks and the send are one step: no other Tempo process can slip in between
        exit_order = is_exit(ib, contract, order)
        if not exit_order:
            _check_entry(ib, order, journal=journal, state_path=state_path, limits=limits,
                         equity_usd=equity_usd, ref_price=ref_price, now=now)
        return dispatch(ib, contract, order, reason=reason, journal=journal, limits=limits, exit_order=exit_order)


REJECTED_CODE = 201  # "Order rejected - reason: ..." (arrives as status Inactive, and ONLY through errorEvent)
# Notices that say nothing about why an order failed: 202 is IBKR's "Order Canceled - reason:" with a blank reason
# (sent for our own cancels too, so it cannot tell who cancelled), 10349 is "TIF set to DAY", 21xx are data-farm status.
IGNORED_CODES = frozenset({202, 10349})

_TRADES_BY_ID: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()  # connection -> {orderId: trade}


def watch_order_errors(ib) -> dict:
    """Start storing, on each trade, the last error IBKR sends for its order id. Once per connection.

    Verified live (2026-11-03): a real 201 rejection leaves `trade.log` without any error code, so the only place
    to learn why an order was refused is `ib.errorEvent`. The same holds for 110 and 391. Hence this listener.
    Returns the connection's {orderId: trade} map; `dispatch` adds each new trade to it.
    """
    trades = _TRADES_BY_ID.get(ib)
    if trades is not None:
        return trades
    trades = _TRADES_BY_ID[ib] = {}

    def on_error(req_id, code, text, *_):
        trade = trades.get(req_id)
        if trade is not None and code not in IGNORED_CODES and not 2100 <= code < 2200:
            trade.broker_error = (code, text)

    ib.errorEvent += on_error
    return trades


def broker_reason(trade) -> dict:
    """Why IBKR says this order failed, as journal fields, or {} if it sent no error for the order.

    The error can arrive after the status, so ask once the order is done. Cancels made by us or by IBKR both
    produce the same blank 202 notice, so a plain cancel has no reason here.
    """
    found = getattr(trade, "broker_error", None)  # set only by the listener, when IBKR sent an error
    if found is None:
        return {}
    code, text = found
    return {"reason_code": code, "reason_kind": "rejected" if code == REJECTED_CODE else "error", "reason_text": text}


def record_outcome(journal: Journal, trade) -> dict:
    """Close the journal entry for a trade with its current state (call once it is done, or has been cancelled).

    An order that did not fully fill also records why the broker says so. A filled order does not: harmless notices
    (such as 10349, "TIF set to DAY") sit in the log of orders that went fine.
    """
    status = trade.orderStatus
    reason = {} if status.status == "Filled" else broker_reason(trade)
    return journal.append(
        "outcome", ref=trade.order.orderRef, status=status.status, filled=status.filled,
        avg_price=status.avgFillPrice, commission=sum(f.commissionReport.commission for f in trade.fills), **reason,
    )
