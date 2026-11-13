from datetime import datetime, timedelta, timezone

import pytest

from tempo.event_risk import append, classify, headline_key, held_rows, load_seen, scan, too_many_failed

NOW = datetime(2026, 11, 13, 21, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("text,cats", [
    ("{A:800015:L:en}The Price Tag on Jensen Huang's Resignation: $639 Billion", ["executive"]),
    ("Acme to acquire Beta for $2 billion", ["mna"]),
    ("SEC investigation into Acme accounting; shares halted", ["halt", "probe"]),
    ("Acme files for Chapter 11 bankruptcy protection", ["failure"]),
    ("Microsoft Outlook Has Us All in a Chokehold, Apparently", []),
    ("Acme CEO steps down", ["executive"]),
    ("Acme acquires Beta Corp", ["mna"]),
    ("CEO Brace Acquires 21,787 Of Skyworks Solutions Inc", []),          # an insider share purchase, not M&A
    ("SEC probe of Acme books widens", ["probe"]),
    ("Acme defaults on its notes", ["failure"]),
    ("Nvidia launches a new chip", []),
])
def test_classify(text, cats):
    assert classify(text) == cats


def test_whole_words_only_and_the_filter_is_blunt_on_purpose():
    assert classify("The firmware merges cleanly") == []
    assert classify("Bank mergers desk reshuffled") == [] and classify("Unfired employees") == []
    assert classify("He was fired up about the results") == ["executive"]          # a human reads the flag


def item(hours_ago, text, provider="DJ-RTG"):
    return NOW - timedelta(hours=hours_ago), provider, text


def held(*syms):
    return [{"signal_id": f"s:{s}:1", "symbol": s, "direction": -1} for s in syms]


def test_scan_flags_new_relevant_recent_headlines_once():
    feed = {"NVDA": [item(2, "Jensen Huang resigns as CEO"), item(1, "Nvidia launches a chip"), item(100, "Old CEO resigns")]}
    seen: set[str] = set()
    flags, failed = scan(held("NVDA"), feed.get, seen, NOW)
    assert failed == [] and [f["headline"] for f in flags] == ["Jensen Huang resigns as CEO"] and flags[0]["categories"] == ["executive"]
    assert scan(held("NVDA"), feed.get, seen, NOW)[0] == []                      # deduplicated


def test_the_same_headline_is_flagged_for_each_signal_that_holds_the_symbol():
    feed = {"AAA": [item(1, "AAA to acquire BBB")]}
    rows = [{"signal_id": "x:AAA:1", "symbol": "AAA", "direction": 1}, {"signal_id": "y:AAA:1", "symbol": "AAA", "direction": -1}]
    flags, _ = scan(rows, feed.get, set(), NOW)
    assert len(flags) == 2 and headline_key("x:AAA:1", "t") != headline_key("y:AAA:1", "t")


def test_a_symbol_without_news_is_reported_failed_not_silently_clean():
    flags, failed = scan(held("AAA", "BBB"), {"AAA": []}.get, set(), NOW)
    assert flags == [] and failed == ["BBB"]


def test_the_lookback_boundary():
    feed = {"AAA": [item(72, "AAA CEO resigns"), item(72.01, "AAA fraud")]}
    flags, _ = scan(held("AAA"), feed.get, set(), NOW)
    assert [f["headline"] for f in flags] == ["AAA CEO resigns"]


def test_log_round_trip_and_dedupe_across_runs(tmp_path):
    path = tmp_path / "e.jsonl"
    feed = {"AAA": [item(1, "AAA CEO resigns")]}
    flags, _ = scan(held("AAA"), feed.get, set(), NOW)
    append(flags, path)
    append([], path)
    assert load_seen(path) == {flags[0]["key"]} and load_seen(tmp_path / "none") == set()
    assert scan(held("AAA"), feed.get, load_seen(path), NOW)[0] == []


def test_only_entered_positions_are_held():
    state = {"a:X:1": {"status": "entered", "symbol": "X", "direction": 1}, "a:Y:1": {"status": "exited", "symbol": "Y", "direction": 1},
             "a:Z:1": {"status": "skipped", "symbol": "Z"}}
    assert held_rows(state) == [{"signal_id": "a:X:1", "symbol": "X", "direction": 1}]


def test_too_many_failed_symbols_is_a_failure_only_above_a_fifth():
    rows = held(*"ABCDE")
    assert not too_many_failed(["A"], rows) and too_many_failed(["A", "B"], rows) and not too_many_failed([], [])
