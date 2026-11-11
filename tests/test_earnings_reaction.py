from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from tempo.earnings_reaction import (SOURCE, DayBars, decide, events_for, measure, parse_feed, reaction_day, record_signals,
                                     ready_to_record)
from tempo.ledger import Ledger

ET = ZoneInfo("America/New_York")


def entry(cik="0000000555", acc="0000000555-26-000001", items=("2.02", "9.01"), updated="2026-11-09T16:30:00-05:00", form="8-K",
          role="Filer"):
    item_html = "".join(f"&lt;br&gt;Item {i}: Something" for i in items)
    return (f"<entry><title>{form} - ACME CORP ({cik}) ({role})</title><summary type=\"html\"> &lt;b&gt;Filed:&lt;/b&gt; 2026-11-09 "
            f"&lt;b&gt;AccNo:&lt;/b&gt; {acc} &lt;b&gt;Size:&lt;/b&gt; 1 MB {item_html} </summary><updated>{updated}</updated>"
            f"<category scheme=\"https://www.sec.gov/\" label=\"form type\" term=\"{form}\"/></entry>")


def feed(*entries):
    return "<feed>" + "".join(entries) + "</feed>"


def et(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=ET)


# --- the SEC feed ---

def test_the_feed_gives_cik_accession_items_and_acceptance_time():
    (e,) = parse_feed(feed(entry()))
    assert (e.cik, e.accession, e.items) == ("555", "0000000555-26-000001", ("2.02", "9.01"))
    assert e.accepted == et(2026, 11, 9, 16, 30)


def test_amendments_and_subject_lines_are_dropped_and_duplicates_merged():
    rows = parse_feed(feed(entry(form="8-K/A", acc="X1"), entry(role="Subject", acc="X2"), entry(acc="X3"), entry(acc="X3")))
    assert [e.accession for e in rows] == ["X3"]


# --- which day reacts ---

def test_reaction_day_is_the_first_session_opening_after_acceptance_and_intraday_filings_are_excluded():
    assert reaction_day(et(2026, 11, 9, 16, 30)) == date(2026, 11, 10)     # Monday after close -> Tuesday
    assert reaction_day(et(2026, 11, 10, 7, 0)) == date(2026, 11, 10)      # before the open -> same day
    assert reaction_day(et(2026, 11, 10, 9, 30)) is None                   # at or after the open, before the close: excluded
    assert reaction_day(et(2026, 11, 10, 15, 59)) is None
    assert reaction_day(et(2026, 11, 10, 16, 0)) == date(2026, 11, 11)     # at the close counts as after
    assert reaction_day(et(2026, 11, 7, 12, 0)) == date(2026, 11, 9)       # Saturday -> Monday
    assert reaction_day(et(2026, 11, 25, 17, 0)) == date(2026, 11, 27)     # Thanksgiving (26th) skipped


def test_events_for_keeps_only_earnings_8ks_reacting_that_day():
    rows = parse_feed(feed(entry(acc="A", updated="2026-11-09T16:30:00-05:00"),
                           entry(acc="B", updated="2026-11-10T07:00:00-05:00"),
                           entry(acc="C", updated="2026-11-10T11:00:00-05:00"),                  # intraday
                           entry(acc="D", updated="2026-11-10T07:00:00-05:00", items=("5.02",)),  # not earnings
                           entry(acc="E", updated="2026-11-08T16:30:00-05:00")))                 # Sunday -> reacts Monday
    assert [e.accession for e in events_for(rows, date(2026, 11, 10))] == ["A", "B"]


# --- the measure ---

def bars(closes, volumes=None, start=1):
    dates = [f"2026-10-{d:02d}" for d in range(start, start + len(closes))]
    return DayBars(dates, list(closes), list(volumes or [1_000_000] * len(closes)))


def test_measure_is_the_reaction_day_return_minus_spy_with_adv_over_the_20_days_before():
    stock = bars([10.0] * 20 + [10.0, 11.0])       # 22 days; reaction day is the last (+10%)
    spy = bars([100.0] * 21 + [101.0])              # SPY +1%
    m = measure(stock, spy, stock.dates[-1])
    assert m["reaction"] == pytest.approx(0.09)
    assert m["close"] == 11.0 and m["adv20"] == pytest.approx(10.0 * 1_000_000)   # the 20 days BEFORE the reaction day


def test_measure_needs_the_reaction_day_the_previous_close_and_20_prior_days():
    assert measure(bars([10.0] * 15 + [11.0]), bars([100.0] * 16), "2026-10-16")["status"] == "short_history"
    assert measure(bars([10.0] * 22), bars([100.0] * 22), "2026-11-30")["status"] == "no_bar"
    assert measure(bars([10.0] * 22), bars([100.0] * 21), "2026-10-22")["status"] == "no_bar"     # SPY lacks the day


@pytest.mark.parametrize("reaction, close, adv, expected", [
    (0.05, 10.0, 6e6, 1), (0.049, 10.0, 6e6, None), (-0.05, 10.0, 6e6, -1), (-0.2, 10.0, 6e6, -1),
    (0.10, 4.99, 6e6, None), (0.10, 10.0, 4.9e6, None),
])
def test_decide_applies_the_registered_thresholds(reaction, close, adv, expected):
    assert decide({"status": "ok", "reaction": reaction, "close": close, "adv20": adv}) == expected


# --- recording ---

def test_signals_are_recorded_only_after_the_close_on_the_reaction_day():
    day = date(2026, 11, 10)
    assert ready_to_record(et(2026, 11, 10, 16, 20), day) is True
    assert ready_to_record(et(2026, 11, 10, 16, 5), day) is False     # delayed bars: wait until 16:20
    assert ready_to_record(et(2026, 11, 11, 7, 0), day) is False      # next day: the ledger date would be wrong
    assert ready_to_record(et(2026, 11, 7, 18, 0), date(2026, 11, 7)) is False   # not a trading day


def ledger_at(tmp_path, when):
    return Ledger(tmp_path / "ledger.jsonl", clock=lambda: when.timestamp())


def test_record_long_and_short_with_cost_and_no_repeat_within_30_days(tmp_path):
    hits = [{"symbol": "ACME", "direction": 1, "day": "2026-11-10", "reaction": 0.07, "close": 11.0, "adv20": 6e6, "accession": "A"},
            {"symbol": "BETA", "direction": -1, "day": "2026-11-10", "reaction": -0.08, "close": 20.0, "adv20": 9e6, "accession": "B"}]
    recs = record_signals(hits, ledger_at(tmp_path, et(2026, 11, 10, 16, 30)))
    assert [(r["symbol"], r["direction"], r["event_id"]) for r in recs] == [("ACME", 1, "20261110"), ("BETA", -1, "20261110")]
    assert recs[0]["source"] == SOURCE and recs[0]["features"]["round_trip_cost"] == 0.002
    again = [{**hits[0], "day": "2026-11-20", "accession": "C"}]
    assert record_signals(again, ledger_at(tmp_path, et(2026, 11, 20, 16, 30))) == []
