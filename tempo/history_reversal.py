"""History of weekly_reversal_v1 (Workstream F): the live rule replayed on cached daily bars.

Nothing is re-implemented: the live `liquid` filter, `r5` move and `pick` of 10 losers (long) and 10 winners (short) are called as they
are. The signal is the last session of each ISO week; entry is the next session's open (live: 09:40), exit 5 sessions later.
Limits, stated in every report: the universe is today's S&P 500 that has cached bars with an open price (2017-11 onwards), so
survivors only; entries stop on 2025-12-23 so no 2026 price is used.
"""
from __future__ import annotations

from collections import Counter
from datetime import date

from tempo.daybars import liquid
from tempo.history_core import Series, Trade, trade_excess
from tempo.weekly_reversal import ROUND_TRIP_COST, pick, r5

SOURCE = "weekly_reversal_v1"
COST = ROUND_TRIP_COST
HORIZON = 5
LAST_ENTRY = "2025-12-23"


def week_ends(calendar: list[str]) -> list[str]:
    """The last session of each ISO week that is followed by a later session (the final date is never a week end: its week is unknown)."""
    out = []
    for a, b in zip(calendar, calendar[1:]):
        if date.fromisoformat(a).isocalendar()[:2] != date.fromisoformat(b).isocalendar()[:2]:
            out.append(a)
    return out


def reversal_trades(universe: dict[str, Series], spy: Series, first: str, last: str = LAST_ENTRY, horizon: int = HORIZON) -> tuple[list[Trade], Counter]:
    counts: Counter = Counter()
    trades: list[Trade] = []
    calendar = spy.dates
    for t in week_ends(calendar):
        entry = calendar[spy.pos[t] + 1]
        if entry < first or entry > last:
            continue
        moves: dict[str, float] = {}
        for symbol, bars in universe.items():
            if liquid(bars, t)["status"] != "ok":  # type: ignore[arg-type]  # duck-typed: dates, close, volume
                continue
            move = r5(bars, spy, t)  # type: ignore[arg-type]
            if move is not None:
                moves[symbol] = move
        longs, shorts = pick(moves)
        if not longs:
            counts["weeks_too_thin"] += 1
            continue
        counts["weeks"] += 1
        for symbol, direction in [(s, 1) for s in longs] + [(s, -1) for s in shorts]:
            gross = trade_excess(universe[symbol], spy, entry, direction, horizon)
            if gross is None:
                counts["unscored"] += 1
            else:
                counts["scored"] += 1
                trades.append(Trade(entry, symbol, gross))
    return trades, counts
