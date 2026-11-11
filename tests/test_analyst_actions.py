from datetime import date, datetime, timezone

import pytest

from tempo.analyst_actions import SOURCE, direction_for, fetch_news, parse_headline, window
from tempo.daybars import DayBars, liquid


@pytest.mark.parametrize("text, expected", [
    ("{A:800015:L:en}!Barclays upgraded Tesla (TSLA) to Overweight with target $450", ("TSLA", 1)),
    ("{A:800015:L:en}!DZ Bank downgraded Apple (AAPL) to Sell with target $300", ("AAPL", -1)),
    ("{A:800015:L:en}!Argus upgraded Boeing (BA) to Buy", ("BA", 1)),
    ("{A:800015:L:en:K:n/a:C:0.97}!Morgan Stanley downgraded Walt Disney (DIS) to Equal Weight", ("DIS", -1)),
    ("!Roth Capital downgraded Intel (INTC) to Neutral with target $70", ("INTC", -1)),
])
def test_upgrades_and_downgrades_are_parsed(text, expected):
    p = parse_headline(text)
    assert (p["symbol"], p["direction"]) == expected


@pytest.mark.parametrize("text", [
    "{A:800015:L:en}!Piper Sandler initiated NVIDIA (NVDA) coverage with Overweight and target $300",
    "{A:800015:L:en}!UBS reiterated Apple (AAPL) coverage with Neutral and target $287",
    "{A:800015:L:en}!Rosenblatt resumed Amazon (AMZN) coverage with Buy",
    "{A:800015:L:en}Boeing and 10 More Buys for the 'Modern-Day Industrial Revolution' -- Barrons.com",
    "",
])
def test_everything_else_is_ignored(text):
    assert parse_headline(text) is None


def utc(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


def test_the_window_runs_from_the_previous_close_to_this_close_in_et():
    start, end = window(date(2026, 11, 10))
    assert start == utc(2026, 11, 9, 21, 0) and end == utc(2026, 11, 10, 21, 0)       # 16:00 ET = 21:00 UTC in November
    start, end = window(date(2026, 11, 9))                                             # Monday: from Friday's close
    assert start == utc(2026, 11, 6, 21, 0)


def test_direction_needs_an_action_inside_the_window_and_no_conflict():
    day = date(2026, 11, 10)
    up = "!Barclays upgraded Tesla (TSLA) to Overweight"
    down = "!Citi downgraded Tesla (TSLA) to Sell"
    assert direction_for("TSLA", [(utc(2026, 11, 10, 12, 0), up)], day) == 1
    assert direction_for("TSLA", [(utc(2026, 11, 9, 20, 59), up)], day) is None          # before the previous close
    assert direction_for("TSLA", [(utc(2026, 11, 10, 21, 1), up)], day) is None          # after today's close: tomorrow's
    assert direction_for("TSLA", [(utc(2026, 11, 10, 12, 0), up), (utc(2026, 11, 10, 13, 0), down)], day) is None
    assert direction_for("TSLA", [(utc(2026, 11, 10, 12, 0), up), (utc(2026, 11, 10, 13, 0), up)], day) == 1
    other = "!Barclays upgraded Apple (AAPL) to Overweight"
    assert direction_for("TSLA", [(utc(2026, 11, 10, 12, 0), other)], day) is None       # a headline about another stock
    assert direction_for("TSLA", [("2026-11-10 12:00:00", up)], day) == 1                # naive strings are UTC


def test_liquidity_filter_uses_the_signal_day_close_and_the_20_days_before():
    bars = DayBars([f"2026-10-{d:02d}" for d in range(1, 23)], [10.0] * 22, [600_000.0] * 22)
    assert liquid(bars, "2026-10-22") == {"status": "ok", "close": 10.0, "adv20": 6_000_000.0}
    assert liquid(bars, "2026-11-30")["status"] == "no_bar"
    assert liquid(DayBars(bars.dates[:10], bars.close[:10], bars.volume[:10]), "2026-10-10")["status"] == "short_history"
    assert liquid(DayBars(bars.dates, [4.0] * 22, bars.volume), "2026-10-22")["status"] == "filtered"
    assert liquid(DayBars(bars.dates, [4.0] * 22, [2_000_000.0] * 22), "2026-10-22")["status"] == "filtered"   # cheap but liquid
    assert liquid(DayBars(bars.dates, [10.0] * 22, [100_000.0] * 22), "2026-10-22")["status"] == "filtered"   # priced but thin


def test_source_name_matches_the_registration():
    import json
    from pathlib import Path
    spec = json.loads((Path(__file__).parents[1] / "evidence" / "analyst_actions_forward.json").read_text(encoding="utf-8"))
    assert spec["source_name"] == SOURCE


class FakeIB:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def reqHistoricalNews(self, *args):
        if self.error:
            raise self.error
        return self.result


def test_a_timeout_is_a_failure_and_an_empty_answer_is_not():
    assert fetch_news(FakeIB(result=None), 1) is None          # ib_async's silent timeout
    assert fetch_news(FakeIB(error=RuntimeError("x")), 1) is None
    assert fetch_news(FakeIB(result=[]), 1) == []              # a stock with no news is a real answer
