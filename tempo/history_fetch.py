"""Fetch what the fast-track history still lacks (Workstream F).

  python -m tempo.history_fetch sets   download the SEC Form sets 2020q1-2025q4 into data/insider_sets (no Gateway). It NEVER writes
                                       data/insider_routine.json: that file belongs to the live morning job.
  python -m tempo.history_fetch        fetch the daily bars (with open) the insider history still lacks.

Needs the Gateway (run it on the VPS). Reads data/history/missing_symbols.json (made by `python -m tempo.history_report plan`),
saves data/history/fast/bars/SYMBOL.csv, or SYMBOL.none when IBKR does not know the symbol (counted as survivorship in the report).
Resumable: files that exist are skipped, so a Gateway restart costs nothing but a rerun. Client id 96, no orders.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
BARS = DATA / "history" / "fast" / "bars"
MISSING = DATA / "history" / "missing_symbols.json"
DURATION = "5 Y"            # 2021-2026: covers the 60-session beta before the first 2023 entry and the exits up to 2025-12-31
CLIENT_ID = 96


def save(path: Path, rows: list[tuple[str, float, float, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(("date", "open", "close", "volume"))
        w.writerows(rows)
    tmp.replace(path)          # atomic: a restart mid-write never leaves a half file that looks complete


def fetch_sets() -> int:  # pragma: no cover - network
    from tempo.insider_history import _fetch_quarter
    quarters = [f"{y}q{q}" for y in range(2020, 2026) for q in (1, 2, 3, 4)]
    for q in quarters:
        print(f"  {q}...", flush=True)
        _fetch_quarter(q)
    print(f"{len(quarters)} quarterly Form sets present in data/insider_sets")
    return 0


def main() -> int:  # pragma: no cover - needs the Gateway
    import dataclasses

    from dotenv import load_dotenv
    from ib_async import Stock

    from tempo.config import load_config
    from tempo.ibkr import connect
    load_dotenv()
    symbols = json.loads(MISSING.read_text(encoding="utf-8"))
    todo = [s for s in symbols if not (BARS / f"{s}.csv").exists() and not (BARS / f"{s}.none").exists()]
    print(f"{len(symbols)} symbols wanted, {len(todo)} still to fetch", flush=True)
    ib = connect(dataclasses.replace(load_config(), client_id=CLIENT_ID))
    ib.RequestTimeout = 60
    done = none = 0
    try:
        for i, symbol in enumerate(todo, 1):
            contract = Stock(symbol, "SMART", "USD")
            if not ib.qualifyContracts(contract):
                BARS.mkdir(parents=True, exist_ok=True)
                (BARS / f"{symbol}.none").write_text("not qualified", encoding="utf-8")
                none += 1
                continue
            raw = ib.reqHistoricalData(contract, "", DURATION, "1 day", "TRADES", useRTH=True, formatDate=1)
            if not raw:
                (BARS / f"{symbol}.none").write_text("no bars", encoding="utf-8")
                none += 1
                continue
            save(BARS / f"{symbol}.csv", [(str(b.date), float(b.open), float(b.close), float(b.volume)) for b in raw])
            done += 1
            if i % 50 == 0:
                print(f"{i}/{len(todo)}: {done} fetched, {none} unknown to IBKR", flush=True)
            time.sleep(0.3)
    finally:
        ib.disconnect()
    print(f"fetched {done}, unknown {none}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(fetch_sets() if sys.argv[1:] == ["sets"] else main())
