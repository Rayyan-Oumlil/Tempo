from datetime import datetime, timezone

from tempo import history_news as hn
from tempo.history_core import Series, Verdict

CAL = ["2022-03-03", "2022-03-04", "2022-03-07", "2022-03-08"]  # Thu, Fri, Mon, Tue


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def test_parse_utc_keeps_midnight_as_date_only_and_rejects_garbage():
    assert hn.parse_utc("2020-06-05 06:30:54 UTC") == utc("2020-06-05 06:30:54")
    midnight = hn.parse_utc("2012-05-29 00:00:00 UTC")
    assert midnight is not None and hn.is_date_only(midnight)
    assert not hn.is_date_only(utc("2012-05-29 00:00:01"))
    assert hn.parse_utc("not a date") is None


def test_date_only_headline_counts_for_that_session_or_the_next_one():
    assert hn.session_of(utc("2022-03-04 00:00:00"), CAL) == "2022-03-04"   # a trading day: same session, not shifted back by the ET conversion
    assert hn.session_of(utc("2022-03-05 00:00:00"), CAL) == "2022-03-07"   # Saturday -> Monday
    assert hn.session_of(utc("2022-03-09 00:00:00"), CAL) is None


def test_session_before_close_is_same_day():
    # 15:59 ET on Thursday 2022-03-03 = 20:59 UTC (EST)
    assert hn.session_of(utc("2022-03-03 20:59:00"), CAL) == "2022-03-03"


def test_session_after_close_is_next_session():
    # 16:00:01 ET Thursday = 21:00:01 UTC
    assert hn.session_of(utc("2022-03-03 21:00:01"), CAL) == "2022-03-04"
    assert hn.session_of(utc("2022-03-03 21:00:00"), CAL) == "2022-03-03"  # exactly 16:00 still belongs to that day


def test_session_weekend_goes_to_monday_and_end_of_calendar_is_none():
    assert hn.session_of(utc("2022-03-05 15:00:00"), CAL) == "2022-03-07"  # Saturday
    assert hn.session_of(utc("2022-03-08 22:00:00"), CAL) is None


def test_session_uses_daylight_time():
    # 2022-07-01 20:30 UTC = 16:30 EDT -> after the close
    cal = ["2022-07-01", "2022-07-05"]
    assert hn.session_of(utc("2022-07-01 20:30:00"), cal) == "2022-07-05"
    assert hn.session_of(utc("2022-07-01 19:30:00"), cal) == "2022-07-01"


def test_trial_membership():
    assert hn.trial_membership(frozenset({"roundup"}), 10) == ()
    assert hn.trial_membership(frozenset({"roundup"}), 60) == ("no_news_fade",)
    assert hn.trial_membership(frozenset(), 49) == ()
    assert hn.trial_membership(frozenset({"substantive", "analyst"}), 0) == ("news_any", "news_substantive", "news_analyst")
    assert hn.trial_membership(frozenset({"auto_move"}), 500) == ("no_news_fade",)


def test_dedupe_skips_within_30_days_per_symbol():
    ev = [("A", "2022-03-01"), ("A", "2022-03-30"), ("A", "2022-03-31"), ("B", "2022-03-02")]
    assert hn.dedupe(ev) == [("A", "2022-03-01"), ("B", "2022-03-02"), ("A", "2022-03-31")]


def _flat(n: int, close: float = 100.0, vol: float = 1_000_000.0) -> Series:
    dates = [f"2022-01-{d:02d}" for d in range(1, 29)][:n]
    return Series(dates, [close] * n, [close] * n, [vol] * n)


def test_moves_needs_five_percent_excess_and_liquidity():
    spy = _flat(28)
    closes = [100.0] * 28
    for i in range(25, 28):
        closes[i] = 107.0  # +7% on a flat SPY day, then it stays there
    stock = Series(spy.dates, closes[:], closes[:], [1_000_000.0] * 28)
    assert [d for d, _ in hn.moves(stock, spy)] == [spy.dates[25]]
    cheap = Series(spy.dates, [c / 100 for c in closes], [c / 100 for c in closes], [1_000_000.0] * 28)  # below 5 USD
    assert hn.moves(cheap, spy) == []
    thin = Series(spy.dates, closes[:], closes[:], [1.0] * 28)
    assert hn.moves(thin, spy) == []


def test_moves_subtracts_the_market_move():
    spy_close = [100.0] * 28
    spy_close[25] = 106.0
    spy = Series(_flat(28).dates, spy_close, spy_close, [0.0] * 28)
    closes = [100.0] * 28
    closes[25] = 106.0  # same move as SPY: no excess
    stock = Series(spy.dates, closes, closes, [1_000_000.0] * 28)
    assert hn.moves(stock, spy) == []


def test_earnings_days_marks_filing_session_and_next():
    filings = {"filings": {"recent": {"filingDate": ["2022-03-04", "2022-03-07"], "form": ["8-K", "8-K"], "items": ["2.02,9.01", "5.02"]}}}
    days, first = hn.earnings_days(filings, CAL)
    assert days == {"2022-03-04", "2022-03-07"}
    assert first == "2022-03-04"


def test_earnings_days_ignores_other_items_and_forms():
    filings = {"filings": {"recent": {"filingDate": ["2022-03-04"], "form": ["10-Q"], "items": ["2.02"]}}}
    assert hn.earnings_days(filings, CAL)[0] == set()
    assert hn.earnings_days({}, CAL) == (set(), None)


def test_to_trade_fade_flips_direction():
    from datetime import date as d_, timedelta
    n = 120
    dates = [(d_(2022, 1, 1) + timedelta(days=i)).isoformat() for i in range(n)]
    spy_close = [100.0 + (i % 2) for i in range(n)]
    spy = Series(dates, spy_close, spy_close, [0.0] * n)
    stock_close = [c * (1.02 if i >= 100 else 1.0) for i, c in enumerate(spy_close)]
    stock = Series(dates, stock_close, stock_close, [1e6] * n)
    day = dates[98]  # entry dates[99], exit dates[104], jump at index 100
    follow = hn.to_trade(stock, spy, day, 0.06, "news_any")
    fade = hn.to_trade(stock, spy, day, 0.06, "no_news_fade")
    assert follow is not None and fade is not None
    assert follow.gross > 0 > fade.gross
    assert abs(follow.gross + fade.gross) < 1e-12
    assert hn.to_trade(stock, spy, dates[-1], 0.06, "news_any") is None  # no next session


def test_bh_flags_picks_strong_trial_only():
    strong = Verdict(500, 200, 0.01, (0.005, 0.015), 5.0, {}, 0.009, "FORWARD", ())
    weak = Verdict(500, 200, 0.0, (-0.01, 0.01), 0.1, {}, -0.001, "KILL", ())
    none = Verdict(0, 0, None, None, None, {}, None, "NO VERDICT", ())
    flags = hn.bh_flags({"a": strong, "b": weak, "c": none})
    assert flags == {"a": True, "b": False, "c": False}


def test_moves_skips_zero_prices_instead_of_crashing():
    spy = _flat(28)
    closes = [100.0] * 28
    closes[25] = 0.0
    stock = Series(spy.dates, closes, closes, [1_000_000.0] * 28)
    assert hn.moves(stock, spy) == []
