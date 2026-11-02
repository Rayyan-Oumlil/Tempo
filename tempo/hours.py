"""US regular trading hours. Small on purpose: weekdays 09:30-16:00 ET, minus known holidays and early closes.

The holiday list needs a yearly update (see docs/market-hours.md). Dates after the list ends are treated as normal
days, so check it every December.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")
OPEN = time(9, 30)
CLOSE = time(16, 0)
EARLY_CLOSE = time(13, 0)

CLOSED_DAYS = frozenset({date(2026, 11, 26), date(2026, 12, 25), date(2027, 1, 1)})
EARLY_CLOSE_DAYS = frozenset({date(2026, 11, 27), date(2026, 12, 24)})


def is_regular_hours(now: datetime | None = None) -> bool:
    now = datetime.now(timezone.utc) if now is None else now
    local = now.astimezone(EASTERN)
    if local.weekday() >= 5 or local.date() in CLOSED_DAYS:
        return False
    close = EARLY_CLOSE if local.date() in EARLY_CLOSE_DAYS else CLOSE
    return OPEN <= local.time() < close
