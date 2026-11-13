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


def test_the_target_is_parsed_when_present():
    assert parse_headline("!Baird downgraded NVIDIA (NVDA) to Neutral with target $200")["target"] == 200.0
    assert parse_headline("!Argus upgraded Boeing (BA) to Buy")["target"] is None
    assert parse_headline("!X upgraded Y (YYY) to Buy with target $1,250.50")["target"] == 1250.5


def test_actions_in_window_keeps_every_action_with_its_detail_and_agrees_with_direction_for():
    from tempo.analyst_actions import actions_in_window
    day = date(2026, 11, 10)
    news = [(utc(2026, 11, 10, 12, 0), "!Baird downgraded NVIDIA (NVDA) to Neutral with target $200"),
            (utc(2026, 11, 10, 13, 0), "!Melius downgraded NVIDIA (NVDA) to Hold with target $185"),
            (utc(2026, 11, 10, 13, 5), "!Barclays upgraded Tesla (TSLA) to Overweight"),          # another stock
            (utc(2026, 11, 9, 12, 0), "!Old downgraded NVIDIA (NVDA) to Sell")]                   # outside the window
    got = actions_in_window("NVDA", news, day)
    assert [(a["firm"], a["rating"], a["target"]) for a in got] == [("Baird", "Neutral", 200.0), ("Melius", "Hold", 185.0)]
    assert direction_for("NVDA", news, day) == -1


def test_signal_features_record_breadth_and_target_versus_price():
    from tempo.analyst_actions import action_features
    acts = [{"firm": "Baird", "rating": "Neutral", "target": 200.0, "direction": -1},
            {"firm": "Melius", "rating": "Hold", "target": 185.0, "direction": -1},
            {"firm": "Argus", "rating": "Sell", "target": None, "direction": -1}]
    f = action_features(acts, close=173.73)
    assert f["n_actions"] == 3 and f["firms"] == ["Baird", "Melius", "Argus"] and f["ratings"] == ["Neutral", "Hold", "Sell"]
    assert f["targets"] == [200.0, 185.0, None]
    assert f["target_vs_price"] == pytest.approx(((200 / 173.73 - 1) + (185 / 173.73 - 1)) / 2)   # mean over the targets given
    assert action_features([{"firm": "A", "rating": "Buy", "target": None, "direction": 1}], close=10.0)["target_vs_price"] is None


def test_record_signals_stores_the_action_detail_without_changing_the_registered_fields(tmp_path):
    from tempo.analyst_actions import record_signals
    from tempo.ledger import Ledger
    ledger = Ledger(tmp_path / "l.jsonl")
    hit = {"symbol": "NVDA", "direction": -1, "day": "2026-11-11", "close": 173.73, "adv20": 1.7e10,
           "actions": [{"firm": "Baird", "rating": "Neutral", "target": 200.0, "direction": -1}]}
    rec = record_signals([hit], ledger)[0]
    assert rec["features"]["round_trip_cost"] == 0.002 and rec["features"]["adv20"] == 17000000000
    assert rec["features"]["firms"] == ["Baird"] and rec["features"]["target_vs_price"] == pytest.approx(200 / 173.73 - 1)
