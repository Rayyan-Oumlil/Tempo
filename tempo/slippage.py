"""A1 reconciliation: how far were the paper account's fills from the prices the ledger scores at (exec_v2)?

For every paper trade, the entry fill is compared with the ledger's entry price (open of the 09:40 ET bar) and the exit fill with
its exit price (open of the bar 15 minutes before the close). A positive gap is money lost against the ledger: a long paying
more, a short receiving less. This is the first-day lesson made permanent (paper vs ledger differed by -250 to +577 bps on day one).

Read-only. Usage: python -m tempo.slippage            (prints the per-source table and any alarm)
Alarm (plan A1): mean ABSOLUTE entry gap above ALARM_BPS over the last ALARM_MIN_TRADES entries of any one source.
A trade whose signal has no exec_v2 score at its horizon yet is counted as pending, never guessed.
"""
from __future__ import annotations

import sys
from collections import defaultdict

from tempo.ledger import Ledger
from tempo.paper_run import HORIZONS, PAPER_FILE, load_state

ALARM_BPS = 60.0
ALARM_MIN_TRADES = 20


def _bps(x: float) -> float:
    return x * 1e4


def trade_gaps(state: dict[str, dict], scores: list[dict]) -> tuple[list[dict], int, list[str]]:
    """(one row per scored paper trade, entered trades still waiting for a score, sources traded but missing from HORIZONS)."""
    by_signal = {(s["signal_id"], s["horizon"]): s for s in scores}
    rows, pending, unknown = [], 0, set()
    for sid, t in state.items():
        if t.get("status") not in ("entered", "exited") or not t.get("fill_price"):
            continue
        source = sid.split(":", 1)[0]
        if source not in HORIZONS:
            unknown.add(source)
            continue
        score = by_signal.get((sid, HORIZONS[source]))
        if score is None:
            pending += 1
            continue
        d = t["direction"]
        entry_gap = _bps(d * (t["fill_price"] - score["entry_px"]) / score["entry_px"])
        exit_fill = t.get("exit_fill_price")
        exit_gap = None if not exit_fill else _bps(-d * (exit_fill - score["exit_px"]) / score["exit_px"])
        rows.append({"signal_id": sid, "source": source, "symbol": t["symbol"], "entry_gap_bps": entry_gap, "exit_gap_bps": exit_gap,
                     "entry_day": score["entry_date"], "vs_reference_bps": _bps(d * (t["fill_price"] - t["ref_price"]) / t["ref_price"])})
    rows.sort(key=lambda r: (r["entry_day"], r["signal_id"]))
    return rows, pending, sorted(unknown)


def summarize(rows: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    by_source: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_source[r["source"]].append(r)
    for source, rs in sorted(by_source.items()):
        entry = [r["entry_gap_bps"] for r in rs]
        exits = [r["exit_gap_bps"] for r in rs if r["exit_gap_bps"] is not None]
        last = entry[-ALARM_MIN_TRADES:]
        out[source] = {"n": len(rs), "entry_mean": sum(entry) / len(entry), "entry_abs": sum(abs(x) for x in entry) / len(entry),
                       "exit_n": len(exits), "exit_mean": sum(exits) / len(exits) if exits else None,
                       "last_abs": sum(abs(x) for x in last) / len(last) if len(entry) >= ALARM_MIN_TRADES else None}
    return out


def alarms(summary: dict[str, dict]) -> list[str]:
    return [f"{src}: mean absolute entry gap {s['last_abs']:.0f} bps over the last {ALARM_MIN_TRADES} trades (limit {ALARM_BPS:.0f})"
            for src, s in summary.items() if s["last_abs"] is not None and s["last_abs"] > ALARM_BPS]


def render(rows: list[dict], pending: int, unknown: list[str] | None = None) -> tuple[str, list[str]]:
    summary = summarize(rows)
    lines = [f"{'source':22} {'n':>3} {'entry mean':>10} {'entry |gap|':>11} {'exits':>5} {'exit mean':>9}   (bps, positive = worse than the ledger)"]
    for src, s in summary.items():
        em = "-" if s["exit_mean"] is None else f"{s['exit_mean']:+.0f}"
        lines.append(f"{src:22} {s['n']:>3} {s['entry_mean']:>+10.0f} {s['entry_abs']:>11.0f} {s['exit_n']:>5} {em:>9}")
    if not summary:
        lines.append("no paper trade has an exec_v2 score yet")
    lines.append(f"{pending} entered trade(s) still waiting for a score; alarm needs {ALARM_MIN_TRADES} scored entries in one source")
    problems = alarms(summary) + [f"{s}: traded in the paper account but has no horizon in paper_run.HORIZONS, so its fills cannot be checked" for s in unknown or []]
    return "\n".join(lines), problems


def report() -> tuple[str, list[str]]:  # pragma: no cover - reads the live journals
    from tempo.journal import Journal
    rows, pending, unknown = trade_gaps(load_state(Journal(PAPER_FILE)), Ledger().scores())
    return render(rows, pending, unknown)


def main() -> int:  # pragma: no cover - entry point
    text, problems = report()
    print(text)
    for p in problems:
        print(f"ALARM {p}")
    return 1 if problems else 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
