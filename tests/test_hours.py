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


def test_calendar_stops_covering_after_its_last_year():
    from tempo.hours import calendar_covers
    assert calendar_covers(utc(2027, 12, 31, 16))
    assert not calendar_covers(utc(2028, 1, 4, 16))


def test_2027_full_closures_from_the_nyse_announcement():
    closed = [(1, 1), (1, 18), (2, 15), (3, 26), (5, 31), (6, 18), (7, 5), (9, 6), (11, 25), (12, 24)]
    for month, day in closed:
        assert not is_regular_hours(utc(2027, month, day, 16)), (month, day)


def test_2027_ordinary_days_next_to_closures_are_open_and_the_day_after_thanksgiving_closes_early():
    for month, day in [(1, 19), (6, 17), (7, 2), (11, 24), (12, 23)]:
        assert is_regular_hours(utc(2027, month, day, 16)), (month, day)   # 11:00 ET
    assert is_regular_hours(utc(2027, 11, 26, 17, 59))     # 12:59 ET
    assert not is_regular_hours(utc(2027, 11, 26, 18, 0))  # 13:00 ET


from datetime import date as _date

from tempo.hours import add_trading_days, is_trading_day, next_trading_day, session_close


def test_weekends_and_listed_holidays_are_not_trading_days():
    assert is_trading_day(_date(2026, 11, 3)) and not is_trading_day(_date(2026, 11, 7)) and not is_trading_day(_date(2026, 11, 26))


def test_next_trading_day_skips_weekends_and_holidays():
    assert next_trading_day(_date(2026, 11, 6)) == _date(2026, 11, 9)       # Friday -> Monday
    assert next_trading_day(_date(2026, 11, 25)) == _date(2026, 11, 27)     # Wednesday -> Friday (Thanksgiving closed)
    assert next_trading_day(_date(2026, 11, 3)) == _date(2026, 11, 4)


def test_add_trading_days_counts_only_open_days():
    assert add_trading_days(_date(2026, 11, 3), 0) == _date(2026, 11, 3)
    assert add_trading_days(_date(2026, 11, 3), 4) == _date(2026, 11, 9)    # 4, 5, 6, then Monday 9
    assert add_trading_days(_date(2026, 11, 25), 1) == _date(2026, 11, 27)


def test_session_close_is_earlier_on_early_close_days():
    from datetime import time
    assert session_close(_date(2026, 11, 3)) == time(16, 0)
    assert session_close(_date(2026, 11, 27)) == time(13, 0)
