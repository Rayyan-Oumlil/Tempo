import json
from datetime import datetime, timezone

import pytest

from tempo.news_archive import (
    Item, append, coverage, fetch_with_retries, load_keys, month_file, new_items, run, to_utc_iso,
)
from tempo.news_labels import clean, label, roundup_texts

NOW = datetime(2026, 11, 17, 21, 0, tzinfo=timezone.utc)


def item(sym="TER", prov="DJ-N", aid="a1", t="2026-11-16T15:00:00+00:00", h="Teradyne wins deal"):
    return Item(sym, prov, aid, t, h)


def test_to_utc_iso_handles_naive_aware_and_strings():
    assert to_utc_iso(datetime(2026, 11, 16, 9, 30)) == "2026-11-16T09:30:00+00:00"
    assert to_utc_iso("2026-11-16 09:30:00.0") == "2026-11-16T09:30:00+00:00"
    from datetime import timedelta
    est = timezone(timedelta(hours=-5))
    assert to_utc_iso(datetime(2026, 11, 16, 9, 30, tzinfo=est)) == "2026-11-16T14:30:00+00:00"


def test_month_file_uses_the_item_month(tmp_path):
    assert month_file(tmp_path, "2026-11-16T15:00:00+00:00").name == "2026-11.jsonl"


def test_new_items_dedupes_per_symbol_not_across_symbols():
    a, b = item("TER"), item("MU")  # same article id on two symbols: both stay (the roundup label counts symbols)
    assert len(new_items([a, b], set())) == 2
    assert new_items([a, a], set()) == [a]
    assert new_items([a], {a.key}) == []


def test_append_and_reload_round_trip(tmp_path):
    n = append(tmp_path, [item(), item(aid="a2", t="2026-12-01T10:00:00+00:00")], NOW)
    assert n == 2 and {f.name for f in tmp_path.glob("*.jsonl")} == {"2026-11.jsonl", "2026-12.jsonl"}
    assert load_keys(tmp_path) == {("TER", "DJ-N", "a1"), ("TER", "DJ-N", "a2")}
    row = json.loads((tmp_path / "2026-11.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["headline"] == "Teradyne wins deal" and row["fetched_at"].startswith("2026-11-17")


def test_coverage_rejects_empty_and_computes_ratio():
    assert coverage(9, 10) == 0.9
    with pytest.raises(ValueError):
        coverage(0, 0)


def test_retries_then_gives_up_and_never_returns_empty_for_failure():
    calls, waits = [], []
    def always_none(s):
        calls.append(s)
        return None
    assert fetch_with_retries(always_none, "X", retries=3, sleep=waits.append, backoff=2) is None
    assert len(calls) == 3 and waits == [2, 4]


def test_retry_stops_at_first_success_and_empty_list_is_a_real_answer():
    seq = iter([None, []])
    assert fetch_with_retries(lambda s: next(seq), "X", sleep=lambda w: None) == []


def test_run_lists_unavailable_and_archives_new_only(tmp_path):
    data = {"A": [item("A", aid="1")], "B": None, "C": [item("C", aid="2")]}
    stats, bad = run(["A", "B", "C"], lambda s: data[s], tmp_path, NOW, sleep=lambda w: None)
    assert bad == ["B"] and stats == {"symbols": 3, "unavailable": 1, "coverage": 0.6667, "added": 2}
    stats2, _ = run(["A", "C"], lambda s: data[s], tmp_path, NOW, sleep=lambda w: None)
    assert stats2["added"] == 0  # idempotent: a second pull adds nothing


# --- labels -------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("{A:800015:L:en}Teradyne Inc. Stock Slips 7.1%, Underperforms Peers", "auto_move"),
    ("Nvidia, Sandisk, SpaceX and More Stocks That Explain Today's Market -- Barrons.com", "roundup"),
    ("Stocks to Watch: Nvidia, Intel, SpaceX -- WSJ", "roundup"),
    ("Dell Technologies Price Target Cut to $403.00/Share From $511.00 by Morgan Stanley", "analyst"),
    ("Dell Technologies Is Maintained at Buy by Citigroup", "analyst"),
    ("CEO Smith Registers 4,000 Of Teradyne Inc >TER", "filing"),
    ("* Soros Fund Management Increases Stake in Intel by 2,730,000 to 2,830,000 Shares -- 13F Filing", "filing"),
    ("Press Release: Teradyne to Present at the 2026 UBS Global Technology and AI Conference", "press_release"),
    ("Intel Sued by Investors After 29% Stock Plunge", "substantive"),
    ("Medicaid Work Requirement Delay Pushes Molina, Centene Stocks Higher -- Barrons.com", "substantive"),
])
def test_labels(text, expected):
    assert label(text) == expected


def test_repeated_text_across_many_symbols_is_a_roundup_even_without_keywords():
    rows = [(f"S{i}", "Quarterly note on markets") for i in range(10)] + [("S0", "Only one symbol")]
    r = roundup_texts(rows)
    assert r == frozenset({"Quarterly note on markets"}) and label("Quarterly note on markets", r) == "roundup"
    assert label("Only one symbol", r) == "substantive"
    assert roundup_texts(rows[:9]) == frozenset()  # nine symbols is under the bar


def test_clean_strips_only_the_leading_metadata_block():
    assert clean("{A:800015:L:en}Hello {x}") == "Hello {x}"
