"""Reconcile the journal with the broker: find out what happened to orders whose outcome was never recorded.

Usage: python -m tempo.reconcile [--accept-missing]      (read-only; works with IBKR_READONLY=1)

For every unresolved intent (matched by its unique orderRef):
  * seen in today's executions  -> resolved as Filled (a partial fill counts as filled: money moved)
  * seen among open orders      -> resolved as "working" (it is alive; cancel it yourself if unwanted)
  * not found anywhere          -> stays unresolved and blocks new entries. It may have been cancelled, rejected,
                                   or filled on an earlier day (executions only cover today). Check by hand, then
                                   run with --accept-missing to clear it.
If the broker cannot be read, nothing is resolved.
"""
from __future__ import annotations

import sys

from dotenv import load_dotenv

from tempo.config import load_config
from tempo.health import Check
from tempo.ibkr import connect
from tempo.ibutil import default_journal
from tempo.journal import Journal


def reconcile(ib, journal: Journal, *, resolve_missing: bool = False) -> list[Check]:
    pending = journal.unresolved()
    if not pending:
        return [Check("journal", True, "no unresolved orders")]
    try:
        working = {t.order.orderRef for t in ib.reqAllOpenOrders()}
        shares: dict[str, float] = {}
        for f in ib.reqExecutions():
            shares[f.execution.orderRef] = shares.get(f.execution.orderRef, 0.0) + f.execution.shares
    except Exception as exc:  # noqa: BLE001 - any failure to read the broker means we cannot decide
        return [Check("journal", False, f"{len(pending)} unresolved; could not read the broker ({exc!r})")]

    checks = []
    for intent in pending:
        ref = intent["ref"]
        label = f"{intent.get('action')} {intent.get('qty')} {intent.get('symbol')} ({ref})"
        if shares.get(ref, 0) > 0:
            journal.append("resolution", ref=ref, status="Filled", filled=shares[ref])
            checks.append(Check("resolved", True, f"{label}: filled {shares[ref]:g}"))
        elif ref in working:
            journal.append("resolution", ref=ref, status="working")
            checks.append(Check("resolved", True, f"{label}: still working at the broker"))
        elif resolve_missing:
            journal.append("resolution", ref=ref, status="accepted_missing")
            checks.append(Check("resolved", True, f"{label}: not found, accepted as not filled"))
        else:
            checks.append(Check("unresolved", False, f"{label}: not found at the broker; verify, then --accept-missing"))
    return checks


def main(accept_missing: bool) -> int:
    load_dotenv()
    ib = connect(load_config())
    ib.RequestTimeout = 15
    try:
        checks = reconcile(ib, default_journal(), resolve_missing=accept_missing)
    finally:
        ib.disconnect()
    for c in checks:
        print(f"[{'OK' if c.ok else 'FAIL'}] {c.name:<11} {c.detail}")
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main("--accept-missing" in sys.argv[1:]))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
