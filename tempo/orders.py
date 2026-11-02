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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tempo.hours import is_regular_hours
from tempo.ibkr import assert_paper
from tempo.journal import Journal
from tempo.state import STATE_FILE, get_mode


class OrderRefused(RuntimeError):
    """A Tempo rule stopped this order. Nothing was sent."""


@dataclass(frozen=True)
class Limits:
    max_position_pct: float  # largest entry, as % of equity
    duplicate_window_s: float = 5.0
    stale_intent_s: float = 60.0  # an unresolved intent older than this blocks entries until reconciled


def is_exit(ib, contract, order) -> bool:
    try:
        held = sum(p.position for p in ib.positions() if _same(p.contract, contract))
    except Exception:  # noqa: BLE001 - unreadable positions must not be treated as an exit
        return False
    qty = order.totalQuantity
    if order.action == "SELL":
        return held > 0 and qty <= held
    return held < 0 and qty <= -held


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


def _check_entry(order, *, journal: Journal, state_path: Path, limits: Limits, equity_usd, ref_price, now) -> None:
    if get_mode(state_path) != "normal":
        raise OrderRefused("mode is reduce_only: new entries are blocked (python -m tempo.state normal to resume)")
    stale = [r for r in journal.unresolved() if journal.now() - r["ts"] > limits.stale_intent_s]
    if stale:
        raise OrderRefused(f"{len(stale)} unresolved order(s) in the journal: run python -m tempo.reconcile first")
    if not order.outsideRth and not is_regular_hours(now):
        raise OrderRefused("market is closed (entries need regular hours or outsideRth=True)")
    if not equity_usd or equity_usd <= 0:
        raise OrderRefused("equity unknown: refusing a new entry")
    if not ref_price or ref_price <= 0:
        raise OrderRefused("reference price unknown: refusing a new entry")
    cap = equity_usd * limits.max_position_pct / 100
    if order.totalQuantity * ref_price > cap:
        raise OrderRefused(f"entry {order.totalQuantity * ref_price:,.0f} exceeds position cap {cap:,.0f} USD")


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
        trade = ib.placeOrder(contract, sendable)
    except Exception as exc:
        journal.append("outcome", ref=sendable.orderRef, status="error", error=repr(exc))
        raise
    journal.append("sent", ref=sendable.orderRef, order_id=sendable.orderId)
    return trade


def place(ib, contract, order, *, reason: str, journal: Journal, limits: Limits, equity_usd: float | None = None,
          ref_price: float | None = None, now: datetime | None = None, state_path: Path = STATE_FILE):
    accounts = ib.managedAccounts()
    assert_paper(accounts[0] if accounts else "none")
    exit_order = is_exit(ib, contract, order)
    if not exit_order:
        _check_entry(order, journal=journal, state_path=state_path, limits=limits,
                     equity_usd=equity_usd, ref_price=ref_price, now=now)
    return dispatch(ib, contract, order, reason=reason, journal=journal, limits=limits, exit_order=exit_order)


def record_outcome(journal: Journal, trade) -> dict:
    """Close the journal entry for a trade with its current state (call once it is done, or has been cancelled)."""
    status = trade.orderStatus
    return journal.append(
        "outcome", ref=trade.order.orderRef, status=status.status, filled=status.filled,
        avg_price=status.avgFillPrice, commission=sum(f.commissionReport.commission for f in trade.fills),
    )
