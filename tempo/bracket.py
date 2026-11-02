"""Long bracket: a market BUY with a protective stop (required) and an optional take-profit.

The stop and take-profit are GTC orders linked to the parent and to each other by an OCA group, so they rest at
IBKR and keep protecting the position even if Tempo dies. Rule learned in the probe (docs/ibkr-gotchas.md):
cancelling ONE leg of an OCA pair cancels the other and leaves the position with no stop. So this module never
cancels a single leg; to get out, use tempo.flatten (cancels the symbol's orders together, then sells) or tempo.kill.
"""
from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from ib_async import LimitOrder, MarketOrder, Stock, StopOrder

from tempo.account import equity_usd as account_equity_usd, last_close
from tempo.config import load_config
from tempo.flatten import flatten_positions
from tempo.health import Check
from tempo.ibkr import assert_paper, connect
from tempo.ibutil import default_journal, default_limits, wait_until
from tempo.journal import Journal
from tempo.orders import Limits, _check_entry, dispatch, record_outcome
from tempo.risk import RiskRules, load_rules, position_size
from tempo.state import STATE_FILE

RESTING = {"Submitted", "PreSubmitted"}
WAIT_SECONDS = 30.0
SETTLE_SECONDS = 10.0


@dataclass(frozen=True)
class BracketPlan:
    qty: int
    entry: float  # reference price used for sizing and the position cap
    stop: float
    take_profit: float | None


@dataclass(frozen=True)
class BracketLegs:
    parent: object
    stop: object
    take_profit: object | None


def plan_bracket(equity_usd: float, entry: float, stop: float, take_profit: float | None, rules: RiskRules,
                 qty: int | None = None) -> BracketPlan:
    """Size a long bracket from the risk rules. `qty` can only lower the size, never raise it."""
    if not 0 < stop < entry:
        raise ValueError(f"stop must be below entry (and above 0), got entry={entry} stop={stop}")
    if take_profit is not None and take_profit <= entry:
        raise ValueError(f"take_profit must be above entry, got entry={entry} take_profit={take_profit}")
    allowed = position_size(equity_usd, entry, stop, rules).shares
    if allowed < 1:
        raise ValueError("the risk rules allow 0 shares at this equity, entry and stop")
    if qty is not None and not 1 <= qty <= allowed:
        raise ValueError(f"qty {qty} exceeds what the rules allow ({allowed}) or is below 1")
    return BracketPlan(qty=qty or allowed, entry=entry, stop=stop, take_profit=take_profit)


def place_bracket(ib, contract, plan: BracketPlan, *, journal: Journal, limits: Limits, equity_usd: float,
                  state_path: Path = STATE_FILE, now: datetime | None = None) -> BracketLegs:
    accounts = ib.managedAccounts()
    assert_paper(accounts[0] if accounts else "none")
    with journal.lock():
        parent = MarketOrder("BUY", plan.qty, orderRef="tempo-bracket", transmit=False)
        _check_entry(parent, journal=journal, state_path=state_path, limits=limits,
                     equity_usd=equity_usd, ref_price=plan.entry, now=now)

        oca = f"tempo-oca-{uuid.uuid4().hex[:10]}"
        parent.orderId = ib.client.getReqId()
        children = []
        if plan.take_profit is not None:
            children.append(LimitOrder("SELL", plan.qty, plan.take_profit, tif="GTC", orderRef="tempo-bracket-tp",
                                       parentId=parent.orderId, ocaGroup=oca, ocaType=1, transmit=False))
        children.append(StopOrder("SELL", plan.qty, plan.stop, tif="GTC", orderRef="tempo-bracket-stop",
                                  parentId=parent.orderId, ocaGroup=oca, ocaType=1, transmit=True))
        for child in children:
            child.orderId = ib.client.getReqId()

        sent = []
        try:
            for order, reason in [(parent, "bracket-entry")] + [(c, f"bracket-{c.orderRef.split('-')[-1]}") for c in children]:
                sent.append(dispatch(ib, contract, order, reason=reason, journal=journal, limits=limits, exit_order=False))
        except Exception:
            for trade in sent:  # nothing was transmitted until the last leg, so cancel the whole set together
                ib.cancelOrder(trade.order)
            raise
        return BracketLegs(parent=sent[0], stop=sent[-1], take_profit=sent[1] if plan.take_profit is not None else None)


def _exit_leg(legs: BracketLegs):
    """(name, trade) of a child leg that has already filled, which means the position is closed; else None."""
    if legs.take_profit is not None and legs.take_profit.orderStatus.status == "Filled":
        return "take-profit", legs.take_profit
    if legs.stop.orderStatus.status == "Filled":
        return "stop", legs.stop
    return None


def confirm_bracket(ib, legs: BracketLegs, *, journal: Journal, limits: Limits, state_path: Path = STATE_FILE,
                    now: datetime | None = None, wait_seconds: float = WAIT_SECONDS) -> list[Check]:
    """Wait for the entry, then prove the stop is resting at IBKR. Fails safe in both bad cases:
    entry never fills  -> cancel the whole set together (never one leg)
    filled but no stop -> close the position at once (an unprotected position is the one thing we refuse to hold)
    """
    all_legs = [t for t in (legs.parent, legs.take_profit, legs.stop) if t is not None]
    wait_until(ib, legs.parent.isDone, wait_seconds)
    symbol = legs.parent.contract.symbol
    if legs.parent.orderStatus.status != "Filled":
        for t in all_legs:
            if not t.isDone():
                ib.cancelOrder(t.order)
        wait_until(ib, lambda: all(t.isDone() for t in all_legs), SETTLE_SECONDS)
        for t in all_legs:
            record_outcome(journal, t)
        return [Check("entry", False, f"{symbol} entry did not fill ({legs.parent.orderStatus.status}); all legs cancelled")]

    record_outcome(journal, legs.parent)
    checks = [Check("entry", True, f"{legs.parent.order.totalQuantity:g} {symbol} @ {legs.parent.orderStatus.avgFillPrice}")]
    wait_until(ib, lambda: legs.stop.orderStatus.status in RESTING or _exit_leg(legs) is not None, SETTLE_SECONDS)
    closed_by = _exit_leg(legs)
    if closed_by is not None:  # seen live: a marketable take-profit fills at once and cancels the stop (OCA)
        wait_until(ib, lambda: all(t.isDone() for t in all_legs[1:]), SETTLE_SECONDS)
        for t in all_legs[1:]:
            record_outcome(journal, t)
        name, leg = closed_by
        return checks + [Check("exit", True, f"{name} already filled @ {leg.orderStatus.avgFillPrice}; position closed")]
    protected = legs.stop.orderStatus.status in RESTING
    if protected:
        for t in all_legs[1:]:  # resting GTC legs are known to the broker; their fate is read from executions later
            journal.append("resolution", ref=t.order.orderRef, status="working")
        checks.append(Check("stop", True, f"resting at {legs.stop.order.auxPrice} ({legs.stop.orderStatus.status})"))
        return checks
    for t in all_legs[1:]:
        record_outcome(journal, t)
    checks.append(Check("stop", False, f"UNPROTECTED: stop is {legs.stop.orderStatus.status}; closing the position"))
    return checks + flatten_positions(ib, journal=journal, limits=limits, state_path=state_path, symbol=symbol, now=now)


def main(symbol: str, stop: float, take_profit: float | None, qty: int | None) -> int:
    load_dotenv()
    cfg = load_config()
    if cfg.readonly:
        raise RuntimeError("Bracket needs IBKR_READONLY=0 (and Read-Only API unticked in Gateway)")
    ib = connect(cfg)
    ib.RequestTimeout = 15
    try:
        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        equity, entry = account_equity_usd(ib), last_close(ib, contract)
        plan = plan_bracket(equity, entry, stop, take_profit, load_rules(), qty)
        journal, limits = default_journal(), default_limits()
        legs = place_bracket(ib, contract, plan, journal=journal, limits=limits, equity_usd=equity)
        checks = [Check("plan", True, f"BUY {plan.qty} {symbol}, stop {plan.stop}, take-profit {plan.take_profit}, "
                                       f"reference price {entry}")]
        checks += confirm_bracket(ib, legs, journal=journal, limits=limits)
    finally:
        ib.disconnect()
    for c in checks:
        print(f"[{'OK' if c.ok else 'FAIL'}] {c.name:<12} {c.detail}", flush=True)
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            raise ValueError("usage: IBKR_READONLY=0 python -m tempo.bracket SYMBOL STOP [TAKE_PROFIT] [QTY]")
        args = sys.argv[1:]
        raise SystemExit(main(args[0].upper(), float(args[1]),
                              float(args[2]) if len(args) > 2 else None,
                              int(args[3]) if len(args) > 3 else None))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
