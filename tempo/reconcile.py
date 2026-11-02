"""Reconcile the journal with the broker: find out what happened to orders whose outcome was never recorded.

Usage: python -m tempo.reconcile [--accept-missing]      (read-only; works with IBKR_READONLY=1)

For every unresolved intent (matched by its unique orderRef):
  * seen in today's executions  -> resolved as Filled (a partial fill counts as filled: money moved)
  * seen among open orders      -> resolved as "working" (it is alive; cancel it yourself if unwanted)
  * not found anywhere          -> stays unresolved and blocks new entries. It may have been cancelled, rejected,
                                   or filled on an earlier day (executions only cover today). Check by hand, then
                                   run with --accept-missing to clear it.
If the broker cannot be read, nothing is resolved.

It also journals each execution of our orders once (kind `fill`, keyed by execId), including fills of orders
that were already resolved, such as a bracket stop or take-profit that fires later. Commission is not recorded:
IBKR reports it as 0.0 at first and fills it in later.

Verified live 2026-11-02 from a fresh client id: a working order, a filled order and a cancelled order, all
matched (or flagged) by orderRef. reqCompletedOrders returns an EMPTY orderRef, so cancelled orders cannot be
matched automatically and need --accept-missing.
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
    refs = {r["ref"] for r in journal.records() if r.get("kind") == "intent"}
    if not refs:
        return [Check("journal", True, "no unresolved orders")]
    pending = journal.unresolved()
    try:
        working = {t.order.orderRef for t in ib.reqAllOpenOrders()}
        executions = list(ib.reqExecutions())
    except Exception as exc:  # noqa: BLE001 - any failure to read the broker means we cannot decide
        return [Check("journal", False, f"{len(pending)} unresolved; could not read the broker ({exc!r})")]
    shares: dict[str, float] = {}
    for f in executions:
        shares[f.execution.orderRef] = shares.get(f.execution.orderRef, 0.0) + f.execution.shares

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
    new_fills = _record_new_fills(journal, executions, refs)
    if new_fills:
        checks.append(Check("fills", True, f"{new_fills} new fill(s) recorded in the journal"))
    return checks or [Check("journal", True, "no unresolved orders")]


def _record_new_fills(journal: Journal, executions, refs: set[str]) -> int:
    """Journal every broker execution of one of our orders exactly once (keyed by exec_id)."""
    seen = {r["exec_id"] for r in journal.records() if r.get("kind") == "fill"}
    added = 0
    for f in executions:
        e = f.execution
        if e.orderRef in refs and e.execId not in seen:
            journal.append("fill", ref=e.orderRef, exec_id=e.execId, shares=e.shares, price=e.price, side=e.side)
            seen.add(e.execId)
            added += 1
    return added


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
