"""US regular trading hours. Small on purpose: weekdays 09:30-16:00 ET, minus known holidays and early closes.

The holiday list needs a yearly update (see docs/market-hours.md). It is only valid through CALENDAR_THROUGH; after
that date `calendar_covers` is False and new entries are refused (fail closed) until someone updates this file.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")
OPEN = time(9, 30)
CLOSE = time(16, 0)
EARLY_CLOSE = time(13, 0)

# Source: NYSE Group, "2026, 2027 and 2028 Holiday and Early Closings Calendar" (ICE press release, 2025-12-23).
# Update from that page every year before CALENDAR_THROUGH. 2026 entries before November are past and omitted.
CALENDAR_THROUGH = date(2027, 12, 31)
CLOSED_DAYS = frozenset({
    date(2026, 11, 26), date(2026, 12, 25),                                   # Thanksgiving, Christmas
    date(2027, 1, 1), date(2027, 1, 18), date(2027, 2, 15), date(2027, 3, 26),  # New Year, MLK, Presidents, Good Friday
    date(2027, 5, 31), date(2027, 6, 18), date(2027, 7, 5), date(2027, 9, 6),   # Memorial, Juneteenth*, July 4*, Labor
    date(2027, 11, 25), date(2027, 12, 24),                                   # Thanksgiving, Christmas*  (* = observed date)
})
EARLY_CLOSE_DAYS = frozenset({date(2026, 11, 27), date(2026, 12, 24), date(2027, 11, 26)})


def calendar_covers(now: datetime | None = None) -> bool:
    now = datetime.now(timezone.utc) if now is None else now
    return now.astimezone(EASTERN).date() <= CALENDAR_THROUGH


def is_regular_hours(now: datetime | None = None) -> bool:
    now = datetime.now(timezone.utc) if now is None else now
    local = now.astimezone(EASTERN)
    if local.weekday() >= 5 or local.date() in CLOSED_DAYS:
        return False
    close = EARLY_CLOSE if local.date() in EARLY_CLOSE_DAYS else CLOSE
    return OPEN <= local.time() < close
