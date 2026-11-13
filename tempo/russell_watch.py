"""Passive measurement of the December 2026 Russell reconstitution (effective after the close of Friday 2026-12-11). No orders.

Input: data/events/russell/lists.csv with columns `symbol,action` (action is `add` or `delete`), copied by hand from the FTSE Russell
preliminary lists (first published after the close on 2026-11-13, updates 11-20, 11-27, 12-04; final list is the last one). The
LSEG pages do not say where the lists live or in what format, so this file is the only manual step. Run once after 2026-12-14 and
before about 2027-02-01 (IBKR's 5-minute history window is two months): the bars are fetched after the fact.

For each name, excess returns against IWM (the small-cap benchmark) over four windows, all from IBKR bars:
  runup    close 2026-11-13 -> close of the day before the event       (the anticipation drift)
  day      open of the event day -> 15:55 ET bar open                   (trading before the close)
  last5    15:55 ET bar open -> official close of the event day         (the closing-auction pressure)
  reverse  close of the event day -> close of the next trading day      (what happens once the forced buying or selling is over)
`signed` multiplies by +1 for additions and -1 for deletions, so a positive number means the textbook direction paid.
A window with a missing bar is None, never filled in. One reconstitution is one sample: no verdict comes from it.

Usage: python -m tempo.russell_watch [EVENT_DAY]     (default 2026-12-11)
"""
from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

from tempo.data import Bars
from tempo.exec_score import Intraday

LISTS = Path("data/events/russell/lists.csv")
OUT = Path("data/events/russell/measure.csv")
BENCH = "IWM"
ANNOUNCE_DAY = "2026-11-13"
EVENT_DAY = "2026-12-11"
ACTIONS = {"add": 1, "delete": -1}
WINDOWS = ("runup", "day", "last5", "reverse")


class ListError(ValueError):
    pass


def load_list(path: Path = LISTS) -> dict[str, str]:
    """symbol -> action. Refuses a missing file, unknown actions, and a symbol listed as both add and delete."""
    if not path.exists():
        raise ListError(f"{path} does not exist: copy the FTSE Russell preliminary additions/deletions there as `symbol,action`")
    out: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for n, row in enumerate(csv.DictReader(f), 2):
            sym, action = (row.get("symbol") or "").strip().upper(), (row.get("action") or "").strip().lower()
            if not sym or action not in ACTIONS:
                raise ListError(f"{path} line {n}: need a symbol and action add|delete, got {row}")
            if out.get(sym, action) != action:
                raise ListError(f"{path} line {n}: {sym} is both an addition and a deletion")
            out[sym] = action
    if not out:
        raise ListError(f"{path} has no rows")
    return out


def _index(bars: Bars | None, day: str, field: str) -> float | None:
    if bars is None or day not in bars.dates:
        return None
    return float(getattr(bars, field)[bars.dates.index(day)])


def _prev_day(bars: Bars | None, day: str) -> str | None:
    if bars is None:
        return None
    earlier = [d for d in bars.dates if d < day]
    return earlier[-1] if earlier else None


def _next_day(bars: Bars | None, day: str) -> str | None:
    if bars is None:
        return None
    later = [d for d in bars.dates if d > day]
    return later[0] if later else None


def _ret(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None or a <= 0 else b / a - 1


def window_returns(daily: Bars | None, intra: Intraday | None, day: str, announce: str = ANNOUNCE_DAY) -> dict[str, float | None]:
    """The four raw returns for one instrument. Missing bars give None."""
    before, after = _prev_day(daily, day), _next_day(daily, day)
    close_eve = _index(daily, before, "close") if before else None
    last5_open = intra.open_at(day, "15:55") if intra else None
    return {"runup": _ret(_index(daily, announce, "close"), close_eve),
            "day": _ret(_index(daily, day, "open"), last5_open),
            "last5": _ret(last5_open, _index(daily, day, "close")),
            "reverse": _ret(_index(daily, day, "close"), _index(daily, after, "close") if after else None)}


def measure(action: str, stock: dict[str, float | None], bench: dict[str, float | None]) -> dict[str, float | None]:
    sign = ACTIONS[action]
    return {w: (None if stock[w] is None or bench[w] is None else sign * (stock[w] - bench[w])) for w in WINDOWS}  # type: ignore[operator]


def summarize(rows: list[dict]) -> dict[str, dict[str, tuple[int, float | None]]]:
    out: dict[str, dict[str, tuple[int, float | None]]] = {}
    for action in ACTIONS:
        out[action] = {}
        for w in WINDOWS:
            vals = [r[w] for r in rows if r["action"] == action and r[w] is not None]
            out[action][w] = (len(vals), mean(vals) if vals else None)
    return out


def render(summary: dict[str, dict[str, tuple[int, float | None]]]) -> str:
    lines = [f"{'':8} " + " ".join(f"{w:>16}" for w in WINDOWS), "signed excess vs IWM, mean (n); positive = the textbook direction paid"]
    for action, ws in summary.items():
        cells = [f"{'-':>16}" if m is None else f"{m:>+10.2%} ({n:>3})" for n, m in (ws[w] for w in WINDOWS)]
        lines.append(f"{action:8} " + " ".join(cells))
    return "\n".join(lines)


def write_csv(rows: list[dict], path: Path = OUT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ("symbol", "action", *WINDOWS))
        w.writeheader()
        w.writerows(rows)


def run(listing: dict[str, str], fetch_daily, fetch_intraday, day: str = EVENT_DAY) -> tuple[list[dict], list[str]]:
    """(one row per listed name that has data, symbols with no data at all). Fetchers take a symbol, return Bars / Intraday or None."""
    bench = window_returns(fetch_daily(BENCH), fetch_intraday(BENCH), day)
    rows, missing = [], []
    for sym, action in sorted(listing.items()):
        stock = window_returns(fetch_daily(sym), fetch_intraday(sym), day)
        if all(v is None for v in stock.values()):
            missing.append(sym)
            continue
        rows.append({"symbol": sym, "action": action, **measure(action, stock, bench)})
    return rows, missing


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - live glue
    from dotenv import load_dotenv

    from tempo.config import load_config
    from tempo.ibkr import connect
    from tempo.ledger_score import ibkr_bars, ibkr_intraday
    args = sys.argv[1:] if argv is None else argv
    day = args[0] if args else EVENT_DAY
    if date.fromisoformat(day) + timedelta(days=1) >= date.today():
        print(f"{day} is not over yet: run this after the next trading day has closed", file=sys.stderr)
        return 1
    listing = load_list()
    load_dotenv()
    ib = connect(load_config())
    ib.RequestTimeout = 60
    try:
        rows, missing = run(listing, lambda s: ibkr_bars(ib, s), lambda s: ibkr_intraday(ib, s), day)
    finally:
        ib.disconnect()
    write_csv(rows)
    print(render(summarize(rows)))
    print(f"{len(rows)} names measured -> {OUT}; no data for {len(missing)}: {', '.join(missing[:20])}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
