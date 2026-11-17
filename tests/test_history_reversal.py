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


def test_longs_are_the_losers_with_a_plus_sign_and_shorts_the_winners_with_a_minus_sign():
    from tempo.history_core import trade_excess
    from tempo.weekly_reversal import pick, r5
    universe, spy = world()
    trades, _ = reversal_trades(universe, spy, first="2024-04-01", last="2024-04-30")
    first_entry = min(t.day for t in trades)
    week_end = max(d for d in week_ends(spy.dates) if spy.dates[spy.pos[d] + 1] == first_entry)
    longs, shorts = pick({s: r5(b, spy, week_end) for s, b in universe.items()})
    got = {t.symbol: t.gross for t in trades if t.day == first_entry}
    assert got[longs[0]] == trade_excess(universe[longs[0]], spy, first_entry, 1, 5)
    assert got[shorts[0]] == trade_excess(universe[shorts[0]], spy, first_entry, -1, 5)


def test_an_illiquid_or_penny_stock_never_enters_the_ranking():
    universe, spy = world()
    penny = [3.0 + 0.01 * i for i in range(len(spy.dates))]                    # under the 5 USD floor: the biggest "loser" if allowed
    penny[-1] = 1.0
    penny = [p * (0.2 if 20 < i < 90 else 1.0) for i, p in enumerate(penny)]
    universe["PENNY"] = Series(spy.dates, penny, penny, [1e6] * len(penny))
    thin = [100.0 - 0.5 * (i % 9) for i in range(len(spy.dates))]
    universe["THIN"] = Series(spy.dates, thin, thin, [10.0] * len(thin))      # 1,000 USD a day: under the 5 million floor
    trades, _ = reversal_trades(universe, spy, first="2024-03-01", last="2024-05-31")
    assert trades and not {t.symbol for t in trades} & {"PENNY", "THIN"}


def test_trades_without_an_exit_bar_are_counted_as_unscored_not_traded():
    universe, spy = world()
    week_end = next(d for d in week_ends(spy.dates) if d >= "2024-04-01")
    cut = spy.pos[week_end] + 2                                          # bars end the day after the entry: no exit bar exists
    short = {s: Series(b.dates[:cut], b.open[:cut], b.close[:cut], b.volume[:cut]) for s, b in universe.items()}
    entry = spy.dates[spy.pos[week_end] + 1]
    trades, counts = reversal_trades(short, spy, first=entry, last=entry)
    assert trades == [] and counts["unscored"] == 20 and counts["scored"] == 0
