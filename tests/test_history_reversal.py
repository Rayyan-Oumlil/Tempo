from datetime import date, timedelta

from tempo.history_core import Series
from tempo.history_reversal import reversal_trades, week_ends


def weekdays(start, n):
    d, out = date.fromisoformat(start), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def test_week_end_is_the_last_session_of_each_iso_week_and_never_the_final_date():
    cal = ["2024-01-02", "2024-01-03", "2024-01-05", "2024-01-08", "2024-01-09", "2024-01-12", "2024-01-15"]   # Thu 01-04 is a holiday here
    assert week_ends(cal) == ["2024-01-05", "2024-01-12"]


def world(n_days=140, n_stocks=50):
    """Every stock follows its own deterministic zig-zag; SPY a gentle one. All liquid (price 100, volume 1e6)."""
    dates = weekdays("2024-01-01", n_days)
    spy_close = [100.0 + 0.2 * ((i * 3) % 7) for i in range(n_days)]
    spy = Series(dates, spy_close, spy_close, [1e8] * n_days)
    universe = {}
    for s in range(n_stocks):
        close = [100.0 + ((i * (s + 2)) % 11) + 0.01 * s for i in range(n_days)]
        universe[f"S{s:02d}"] = Series(dates, close, close, [1e6] * n_days)
    return universe, spy


def test_each_week_goes_long_the_ten_biggest_losers_and_short_the_ten_biggest_winners():
    from tempo.weekly_reversal import pick, r5
    universe, spy = world()
    trades, counts = reversal_trades(universe, spy, first="2024-03-01", last="2024-05-31")
    assert counts["weeks"] > 5 and counts["scored"] == len(trades) and len(trades) > 0
    first_entry = min(t.day for t in trades)
    week_end = max(d for d in week_ends(spy.dates) if spy.dates[spy.pos[d] + 1] == first_entry)
    moves = {s: r5(b, spy, week_end) for s, b in universe.items()}
    longs, shorts = pick({s: m for s, m in moves.items() if m is not None})
    assert {t.symbol for t in trades if t.day == first_entry} <= set(longs) | set(shorts)


def test_a_week_with_too_few_liquid_stocks_is_skipped_not_traded():
    universe, spy = world(n_stocks=20)
    trades, counts = reversal_trades(universe, spy, first="2024-03-01", last="2024-05-31")
    assert trades == [] and counts["weeks_too_thin"] > 0 and counts["weeks"] == 0


def test_entries_before_first_or_after_the_cap_are_not_traded():
    universe, spy = world()
    trades, _ = reversal_trades(universe, spy, first="2024-04-01", last="2024-04-30")
    assert trades and all("2024-04-01" <= t.day <= "2024-04-30" for t in trades)
