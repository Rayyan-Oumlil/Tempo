"""Trade the ledger's forward signals on the IBKR PAPER account through the order door (evidence/paper_run.json).

Usage (needs IB Gateway on the paper account with Read-Only API unticked, and IBKR_READONLY=0):
  python -m tempo.paper_run plan [YYYY-MM-DD]   show what is due on that date (default today); sends nothing
  python -m tempo.paper_run entries             09:35 ET or later: enter every signal whose entry day is today
  python -m tempo.paper_run exits               15:45 ET or later: exit every position whose exit day is today or past
  python -m tempo.paper_run status              every signal's state

Every order goes through tempo/orders.py (modes, daily loss limit, duplicate guard, journal). Signals of other
sources are never traded. Paper P&L never feeds a strategy verdict; it measures Tempo's plumbing and costs.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

from ib_async import MarketOrder, Stock

from tempo.hours import EASTERN, OPEN, add_trading_days, is_regular_hours, next_trading_day, session_close
from tempo.journal import Journal
from tempo.ledger import Ledger
from tempo.orders import OrderRefused, place, record_outcome
from tempo.state import STATE_FILE

HORIZONS = {"claude_earnings_v1": 5, "insider_cluster_v1": 21}
NOTIONAL_PCT = 0.5
ENTRY_DELAY_MINUTES = 5
EXIT_LEAD_MINUTES = 15
FILL_WAIT_SECONDS = 20.0
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


def load_state(paper: Journal) -> dict[str, dict]:
    """Where each traded signal stands, replayed from the paper journal: entered, exited, skipped or missed."""
    state: dict[str, dict] = {}
    for r in paper.records():
        sid = r.get("signal_id")
        if r["kind"] == "paper_entry":
            state[sid] = {**r, "status": "entered"}
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


def run_entries(*, ib, ledger: Ledger, paper: Journal, order_journal: Journal, limits, state_path: Path, price_fn, equity_fn,
                now: datetime, say=print) -> int:
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
            trade = place(ib, contract, order, reason=s["signal_id"], journal=order_journal, limits=limits, equity_usd=equity,
                          ref_price=ref, state_path=state_path, now=now)
        except OrderRefused as exc:
            _skip(paper, s, f"order door refused: {exc}", say)
            continue
        _wait(ib, trade)
        record_outcome(order_journal, trade)
        if trade.orderStatus.status != "Filled":
            ib.cancelOrder(trade.order)
            _skip(paper, s, f"not filled: {trade.orderStatus.status}", say)
            continue
        entry_day, exit_day = schedule(s["date_et"], HORIZONS[s["source"]])
        paper.append("paper_entry", signal_id=s["signal_id"], symbol=s["symbol"], direction=s["direction"], qty=qty, ref_price=ref,
                     fill_price=trade.orderStatus.avgFillPrice, entry_day=entry_day.isoformat(), exit_day=exit_day.isoformat(),
                     order_ref=trade.order.orderRef)
        say(f"  entered {s['symbol']} {order.action} {qty} @ {trade.orderStatus.avgFillPrice}")
        placed += 1
    return placed


def run_exits(*, ib, ledger: Ledger, paper: Journal, order_journal: Journal, limits, state_path: Path, price_fn, equity_fn,
              now: datetime, say=print) -> int:
    today = now.astimezone(EASTERN).date()
    done = 0
    for s, entry in due_actions(ledger.signals(), load_state(paper), today)["exit"]:
        contract = Stock(s["symbol"], "SMART", "USD")
        ib.qualifyContracts(contract)
        order = MarketOrder("SELL" if entry["direction"] == 1 else "BUY", entry["qty"], tif="DAY", orderRef=f"paper-exit-{s['source']}")
        try:
            trade = place(ib, contract, order, reason=f"exit {s['signal_id']}", journal=order_journal, limits=limits,
                          equity_usd=equity_fn(ib), ref_price=price_fn(ib, contract), state_path=state_path, now=now)
        except OrderRefused as exc:
            say(f"  exit of {s['symbol']} refused ({exc}); will retry next run")
            continue
        _wait(ib, trade)
        record_outcome(order_journal, trade)
        if trade.orderStatus.status != "Filled":
            say(f"  exit of {s['symbol']} not filled ({trade.orderStatus.status}); will retry next run")
            ib.cancelOrder(trade.order)
            continue
        paper.append("paper_exit", signal_id=s["signal_id"], symbol=s["symbol"], exit_fill_price=trade.orderStatus.avgFillPrice,
                     exit_order_ref=trade.order.orderRef)
        say(f"  exited {s['symbol']} {order.action} {entry['qty']} @ {trade.orderStatus.avgFillPrice}")
        done += 1
    return done


def _wait(ib, trade) -> None:
    from tempo.ibutil import wait_until
    wait_until(ib, trade.isDone, FILL_WAIT_SECONDS)


def main(argv: list[str]) -> int:
    from dotenv import load_dotenv

    from tempo.account import equity_usd, last_close
    from tempo.config import load_config
    from tempo.ibkr import connect
    from tempo.ibutil import default_journal, default_limits

    command = argv[0] if argv else "status"
    ledger, paper = Ledger(), Journal(PAPER_FILE)
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
        raise ValueError("usage: python -m tempo.paper_run plan|entries|exits|status")
    load_dotenv()
    cfg = load_config()
    if cfg.readonly:
        raise RuntimeError("paper_run needs IBKR_READONLY=0 (and Read-Only API unticked in Gateway)")
    now = datetime.now(timezone.utc)
    allowed = entries_allowed(now) if command == "entries" else exits_allowed(now)
    if not allowed:
        raise RuntimeError(f"{command} not allowed now ({now.astimezone(EASTERN):%Y-%m-%d %H:%M} ET): entries need 09:35 ET or later, exits 15 minutes before the close")
    ib = connect(cfg)
    ib.RequestTimeout = 30
    try:
        fn = run_entries if command == "entries" else run_exits
        n = fn(ib=ib, ledger=ledger, paper=paper, order_journal=default_journal(), limits=default_limits(), state_path=STATE_FILE,
               price_fn=last_close, equity_fn=equity_usd, now=now)
    finally:
        ib.disconnect()
    print(f"{command}: {n} order(s) completed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
