from datetime import datetime, timezone

from tempo.hours import is_regular_hours


def utc(y, m, d, h, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc)


def test_open_and_close_edges_in_eastern_time():
    assert is_regular_hours(utc(2026, 11, 3, 14, 30))      # 09:30 ET Tuesday
    assert not is_regular_hours(utc(2026, 11, 3, 14, 29))  # 09:29 ET
    assert is_regular_hours(utc(2026, 11, 3, 20, 59))      # 15:59 ET
    assert not is_regular_hours(utc(2026, 11, 3, 21, 0))   # 16:00 ET


def test_weekend_and_holiday_closed():
    assert not is_regular_hours(utc(2026, 11, 7, 16))   # Saturday
    assert not is_regular_hours(utc(2026, 11, 26, 16))  # Thanksgiving


def test_early_close_day():
    assert is_regular_hours(utc(2026, 11, 27, 17, 59))      # 12:59 ET
    assert not is_regular_hours(utc(2026, 11, 27, 18, 0))   # 13:00 ET


def test_dst_changes_the_utc_offset():
    assert is_regular_hours(utc(2026, 7, 1, 13, 30))   # 09:30 EDT
    assert not is_regular_hours(utc(2026, 7, 1, 13, 29))
