"""Trade the ledger's forward signals on the IBKR PAPER account through the order door (evidence/paper_run.json).

Usage (needs IB Gateway on the paper account with Read-Only API unticked, and IBKR_READONLY=0):
  python -m tempo.paper_run plan [YYYY-MM-DD]   show what is due on that date (default today); sends nothing
  python -m tempo.paper_run preflight           connect and check everything that must be true before a live run; sends nothing
  python -m tempo.paper_run entries --dry-run [--as-of 'YYYY-MM-DD HH:MM']
                                                the real flow with the real broker and the order door's real checks,
                                                asking the broker what each order would cost, but sending and
                                                recording nothing (--as-of sets the ET clock, e.g. to rehearse a day)
  python -m tempo.paper_run entries             09:35 ET or later: enter every signal whose entry day is today
  python -m tempo.paper_run exits               15:45 ET or later: exit every position whose exit day is today or past
  python -m tempo.paper_run status              every signal's state

Every order goes through tempo/orders.py (modes, daily loss limit, duplicate guard, journal). Signals of other
sources are never traded. Paper P&L never feeds a strategy verdict; it measures Tempo's plumbing and costs.
"""
from __future__ import annotations

import copy
import shutil
import sys
import tempfile
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ib_async import MarketOrder, Stock

from tempo.account import daily_loss_pct
from tempo.health import Check, run_health
from tempo.hours import EASTERN, OPEN, add_trading_days, is_regular_hours, next_trading_day, session_close
from tempo.ibkr import assert_paper
from tempo.ibutil import wait_until
from tempo.journal import JOURNAL_FILE, Journal
from tempo.ledger import Ledger
from tempo.orders import OrderRefused, _check_entry, is_exit, place, record_outcome
from tempo.state import STATE_FILE, get_mode

HORIZONS = {"claude_earnings_v1": 5, "insider_cluster_v1": 21}
NOTIONAL_PCT = 0.5
ENTRY_DELAY_MINUTES = 5
EXIT_LEAD_MINUTES = 15
FILL_WAIT_SECONDS = 20.0
CANCEL_WAIT_SECONDS = 10.0
PAPER_FILE = Path(__file__).resolve().parents[1] / "journal" / "paper_run.jsonl"


def schedule(date_et: str, horizon: int) -> tuple[date, date]:
    """(entry day, exit day): enter on the first trading day after the signal date; exit on the horizon-th trading day
    counting the entry day as day 1 (the days the ledger enters at the open and exits at the close)."""
    entry = next_trading_day(date.fromisoformat(date_et))
    return entry, add_trading_days(entry, horizon - 1)


def position_size(equity_usd: float, price: float, pct: float = NOTIONAL_PCT) -> int:
    return int((equity_usd * pct / 100.0) // price)


def _minutes_into_session(now: datetime) -> float:
    local = now.astimezone(EASTERN)
    return (local.hour * 60 + local.minute + local.second / 60) - (OPEN.hour * 60 + OPEN.minute)


def entries_allowed(now: datetime) -> bool:
    return is_regular_hours(now) and _minutes_into_session(now) >= ENTRY_DELAY_MINUTES


def exits_allowed(now: datetime) -> bool:
    local = now.astimezone(EASTERN)
    close = session_close(local.date())
    close_min = close.hour * 60 + close.minute
    minute = local.hour * 60 + local.minute + local.second / 60
    return is_regular_hours(now) and minute >= close_min - EXIT_LEAD_MINUTES


SIGNAL_KINDS = frozenset({"paper_entry", "paper_reduce", "paper_exit", "paper_skip", "paper_missed"})


def load_state(paper: Journal) -> dict[str, dict]:
    """Where each traded signal stands, replayed from the paper journal: entered, exited, skipped or missed."""
    state: dict[str, dict] = {}
    for r in paper.records():
        if r["kind"] not in SIGNAL_KINDS:
            continue
        sid = r["signal_id"]  # a signal record without its id is corruption: fail loudly, never file it under None
        if r["kind"] == "paper_entry":
            state[sid] = {**r, "status": "entered"}
        elif r["kind"] == "paper_reduce":      # part of an exit filled: the rest is still held and still tracked
            state[sid] = {**state.get(sid, {}), "qty": r["qty"]}
        elif r["kind"] == "paper_exit":
            state[sid] = {**state.get(sid, {}), **r, "status": "exited"}
        elif r["kind"] in ("paper_skip", "paper_missed"):
            state[sid] = {**r, "status": "skipped" if r["kind"] == "paper_skip" else "missed"}
    return state


def due_actions(signals: list[dict], state: dict[str, dict], today: date) -> dict[str, list]:
    """What to do today. Entries only on the entry day itself (a missed day is recorded, never traded late)."""
    out: dict[str, list] = {"enter": [], "missed": [], "exit": []}
    for s in signals:
        horizon = HORIZONS.get(s["source"])
        if horizon is None:
            continue
        entry_day, exit_day = schedule(s["date_et"], horizon)
        known = state.get(s["signal_id"])
        if known is None:
            if entry_day == today:
                out["enter"].append(s)
            elif entry_day < today:
                out["missed"].append(s)
        elif known["status"] == "entered" and exit_day <= today:
            out["exit"].append((s, known))
    return out


def _skip(paper: Journal, signal: dict, reason: str, say) -> None:
    paper.append("paper_skip", signal_id=signal["signal_id"], symbol=signal["symbol"], reason=reason)
    say(f"  skip {signal['symbol']}: {reason}")


def dry_sender(ib, contract, order, *, reason, journal, limits, equity_usd, ref_price, state_path, now, say=print, **_):
    """Stands in for `place` in a dry run: runs the order door's own checks and asks the broker what the order would
    cost (whatIfOrder), but sends nothing. Returns a stub that looks like a filled trade so the rest of the flow runs."""
    accounts = ib.managedAccounts()
    assert_paper(accounts[0] if accounts else "none")
    exit_order = is_exit(ib, contract, order)
    if not exit_order:
        _check_entry(ib, order, journal=journal, state_path=state_path, limits=limits, equity_usd=equity_usd,
                     ref_price=ref_price, now=now)
    probe = copy.copy(order)
    probe.tif = "DAY"  # whatIfOrder returns nothing without an explicit tif (docs/ibkr-gotchas.md)
    state = ib.whatIfOrder(contract, probe)
    detail = f"commission {state.commission}, margin change {state.initMarginChange}" if state else "whatIf returned nothing"
    say(f"  WOULD SEND {order.action} {order.totalQuantity} {contract.symbol} ({'exit' if exit_order else 'entry'}): {detail}")
    status = SimpleNamespace(status="Filled", filled=order.totalQuantity, avgFillPrice=ref_price)
    return SimpleNamespace(order=order, orderStatus=status, fills=[], log=[], isDone=lambda: True, dry_run=True)


def preflight(ib, *, readonly: bool, ledger: Ledger, paper: Journal, order_journal: Journal, state_path: Path, now: datetime,
              loss_fn=daily_loss_pct) -> list[Check]:
    """Everything that must be true before the first live order, in one list. Sends nothing."""
    checks = run_health(ib, journal=order_journal, state_path=state_path)
    checks.append(Check("orders enabled", not readonly, "IBKR_READONLY=0" if not readonly else "set IBKR_READONLY=0 and untick Read-Only API in Gateway"))
    mode = get_mode(state_path)
    checks.append(Check("mode normal", mode == "normal", mode if mode == "normal" else f"{mode}: every entry would be refused"))
    try:
        checks.append(Check("daily P&L readable", True, f"{loss_fn(ib):.2f}% down today (entries are refused if this cannot be read)"))
    except Exception as exc:  # noqa: BLE001 - the point of the check is to surface whatever goes wrong
        checks.append(Check("daily P&L readable", False, f"{exc}"))
    due = due_actions(ledger.signals(), load_state(paper), now.astimezone(EASTERN).date())
    checks.append(Check("due today", True, f"enter {len(due['enter'])}, exit {len(due['exit'])}, missed {len(due['missed'])}"))
    checks.append(Check("time window", True, f"entries allowed now: {entries_allowed(now)}; exits allowed now: {exits_allowed(now)}"))
    return checks


def run_entries(*, ib, ledger: Ledger, paper: Journal, order_journal: Journal, limits, state_path: Path, price_fn, equity_fn,
                now: datetime, say=print, sender=place) -> int:
    today = now.astimezone(EASTERN).date()
    actions = due_actions(ledger.signals(), load_state(paper), today)
    for s in actions["missed"]:
        paper.append("paper_missed", signal_id=s["signal_id"], symbol=s["symbol"], reason=f"entry day passed without an entry (today {today})")
        say(f"  missed {s['symbol']}")
    if not actions["enter"]:
        return 0
    equity, placed = equity_fn(ib), 0
    for s in actions["enter"]:
        contract = Stock(s["symbol"], "SMART", "USD")
        if not ib.qualifyContracts(contract):
            _skip(paper, s, "broker cannot qualify this symbol", say)
            continue
        try:
            ref = price_fn(ib, contract)
        except Exception as exc:  # noqa: BLE001 - an unreadable price must skip the trade, never guess one
            _skip(paper, s, f"no price: {exc}", say)
            continue
        qty = position_size(equity, ref)
        if qty < 1:
            _skip(paper, s, f"position too small: {NOTIONAL_PCT}% of equity buys no share at {ref}", say)
            continue
        order = MarketOrder("BUY" if s["direction"] == 1 else "SELL", qty, tif="DAY", orderRef=f"paper-{s['source']}")
        try:
            trade = sender(ib, contract, order, reason=s["signal_id"], journal=order_journal, limits=limits, equity_usd=equity,
                           ref_price=ref, state_path=state_path, now=now)
        except OrderRefused as exc:
            _skip(paper, s, f"order door refused: {exc}", say)
            continue
        _settle(ib, trade, order_journal)
        filled = int(trade.orderStatus.filled)
        if filled < 1:
            _skip(paper, s, f"not filled: {trade.orderStatus.status}", say)
            continue
        partial = filled < qty
        entry_day, exit_day = schedule(s["date_et"], HORIZONS[s["source"]])
        # What filled is what is held, so that is what is tracked and later exited, even if the order only partly filled.
        paper.append("paper_entry", signal_id=s["signal_id"], symbol=s["symbol"], direction=s["direction"], qty=filled, partial=partial,
                     ref_price=ref, fill_price=trade.orderStatus.avgFillPrice, entry_day=entry_day.isoformat(),
                     exit_day=exit_day.isoformat(), order_ref=trade.order.orderRef)
        say(f"  entered {s['symbol']} {order.action} {filled}{f' (PARTIAL, {qty} asked)' if partial else ''} @ {trade.orderStatus.avgFillPrice}")
        placed += 1
    return placed


def run_exits(*, ib, ledger: Ledger, paper: Journal, order_journal: Journal, limits, state_path: Path, price_fn, equity_fn,
              now: datetime, say=print, sender=place) -> int:
    today = now.astimezone(EASTERN).date()
    done = 0
    for s, entry in due_actions(ledger.signals(), load_state(paper), today)["exit"]:
        contract = Stock(s["symbol"], "SMART", "USD")
        ib.qualifyContracts(contract)
        sign = 1 if entry["direction"] == 1 else -1
        # Never close more than the broker actually holds: selling more than a long position (or buying back more than a
        # short) would not be an exit, it would open the opposite position.
        qty = min(entry["qty"], int(sign * _held(ib, s["symbol"])))
        if qty < 1:
            paper.append("paper_exit", signal_id=s["signal_id"], symbol=s["symbol"], exit_fill_price=None, exit_order_ref=None,
                         note="no position at the broker; nothing to close")
            say(f"  {s['symbol']}: no position at the broker, nothing to close (tracking closed)")
            continue
        order = MarketOrder("SELL" if sign == 1 else "BUY", qty, tif="DAY", orderRef=f"paper-exit-{s['source']}")
        try:
            trade = sender(ib, contract, order, reason=f"exit {s['signal_id']}", journal=order_journal, limits=limits,
                           equity_usd=equity_fn(ib), ref_price=price_fn(ib, contract), state_path=state_path, now=now)
        except OrderRefused as exc:
            say(f"  exit of {s['symbol']} refused ({exc}); will retry next run")
            continue
        _settle(ib, trade, order_journal)
        filled = int(trade.orderStatus.filled)
        if filled < qty:
            if filled > 0:
                paper.append("paper_reduce", signal_id=s["signal_id"], symbol=s["symbol"], qty=entry["qty"] - filled, filled=filled,
                             fill_price=trade.orderStatus.avgFillPrice)
                say(f"  partial exit of {s['symbol']}: {filled} of {qty} filled; {entry['qty'] - filled} still tracked, retried next run")
            else:
                say(f"  exit of {s['symbol']} not filled ({trade.orderStatus.status}); will retry next run")
            continue
        paper.append("paper_exit", signal_id=s["signal_id"], symbol=s["symbol"], qty=filled, exit_fill_price=trade.orderStatus.avgFillPrice,
                     exit_order_ref=trade.order.orderRef)
        say(f"  exited {s['symbol']} {order.action} {filled} @ {trade.orderStatus.avgFillPrice}")
        done += 1
    return done


def _held(ib, symbol: str) -> float:
    return sum(p.position for p in ib.positions() if p.contract.symbol == symbol)


def _wait(ib, trade) -> None:
    wait_until(ib, trade.isDone, FILL_WAIT_SECONDS)


def _settle(ib, trade, order_journal: Journal) -> None:
    """Wait for the fill, cancel whatever is still working, wait for the cancel, then journal the FINAL state of the
    order (so a partly filled order is recorded as it ended, and its journal intent is closed)."""
    _wait(ib, trade)
    if getattr(trade, "dry_run", False):  # a dry run sent nothing: nothing to cancel, no outcome to record
        return
    if trade.orderStatus.status != "Filled":
        ib.cancelOrder(trade.order)
        wait_until(ib, trade.isDone, CANCEL_WAIT_SECONDS)
    record_outcome(order_journal, trade)


def main(argv: list[str]) -> int:
    from dotenv import load_dotenv

    from tempo.account import equity_usd, last_close
    from tempo.config import load_config
    from tempo.ibkr import connect
    from tempo.ibutil import default_journal, default_limits

    as_of = None
    if "--as-of" in argv:
        i = argv.index("--as-of")
        as_of = datetime.strptime(argv[i + 1], "%Y-%m-%d %H:%M").replace(tzinfo=EASTERN).astimezone(timezone.utc)
        argv = argv[:i] + argv[i + 2:]
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    if as_of is not None and not dry:
        raise ValueError("--as-of only works together with --dry-run (a real run always uses the real clock)")
    command = argv[0] if argv else "status"
    ledger, paper = Ledger(), Journal(PAPER_FILE)
    if command == "preflight":
        load_dotenv()
        cfg = load_config()
        ib = connect(cfg)
        ib.RequestTimeout = 30
        try:
            checks = preflight(ib, readonly=cfg.readonly, ledger=ledger, paper=paper, order_journal=default_journal(),
                               state_path=STATE_FILE, now=datetime.now(timezone.utc))
        finally:
            ib.disconnect()
        for c in checks:
            print(f"[{'OK' if c.ok else 'FAIL'}] {c.name:<18} {c.detail}")
        return 0 if all(c.ok for c in checks) else 1
    if command == "plan":
        day = date.fromisoformat(argv[1]) if len(argv) > 1 else datetime.now(EASTERN).date()
        a = due_actions(ledger.signals(), load_state(paper), day)
        print(f"{day}: enter {[s['symbol'] for s in a['enter']]}, exit {[s['symbol'] for s, _ in a['exit']]}, missed {[s['symbol'] for s in a['missed']]}")
        return 0
    if command == "status":
        for sid, r in load_state(paper).items():
            print(f"{sid:<40} {r['status']:<8} {r.get('reason', '')}")
        print(f"{len(load_state(paper))} signals tracked")
        return 0
    if command not in ("entries", "exits"):
        raise ValueError("usage: python -m tempo.paper_run plan|preflight|entries|exits|status [--dry-run [--as-of 'YYYY-MM-DD HH:MM']]")
    load_dotenv()
    cfg = load_config()
    now = as_of or datetime.now(timezone.utc)
    if not dry:
        if cfg.readonly:
            raise RuntimeError("paper_run needs IBKR_READONLY=0 (and Read-Only API unticked in Gateway)")
        allowed = entries_allowed(now) if command == "entries" else exits_allowed(now)
        if not allowed:
            raise RuntimeError(f"{command} not allowed now ({now.astimezone(EASTERN):%Y-%m-%d %H:%M} ET): entries need 09:35 ET or later, exits 15 minutes before the close")
    sender: Callable[..., Any]
    order_journal, sender = default_journal(), place
    if dry:  # scratch copies of both journals: a dry run asks the broker and the order door, and writes nothing real
        paper, order_journal, folder = _scratch_copies()
        sender = dry_sender
        print(f"DRY RUN at {now.astimezone(EASTERN):%Y-%m-%d %H:%M} ET (clock as given; the broker is real): nothing will be sent or recorded")
    ib = connect(cfg)
    ib.RequestTimeout = 30
    try:
        fn = run_entries if command == "entries" else run_exits
        n = fn(ib=ib, ledger=ledger, paper=paper, order_journal=order_journal, limits=default_limits(), state_path=STATE_FILE,
               price_fn=last_close, equity_fn=equity_usd, now=now, sender=sender)
    finally:
        ib.disconnect()
        if dry:
            shutil.rmtree(folder, ignore_errors=True)
    print(f"{command}: {n} order(s) {'that WOULD be sent' if dry else 'completed'}")
    return 0


def _scratch_copies() -> tuple[Journal, Journal, Path]:
    folder = Path(tempfile.mkdtemp(prefix="tempo-dryrun-"))
    for name, source in (("paper_run.jsonl", PAPER_FILE), ("journal.jsonl", JOURNAL_FILE)):
        if source.exists():
            shutil.copy(source, folder / name)
    return Journal(folder / "paper_run.jsonl"), Journal(folder / "journal.jsonl"), folder


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
