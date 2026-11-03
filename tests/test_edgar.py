import json

import pytest

from tempo.edgar import (EdgarError, Throttle, cik_for, html_to_text, pick_exhibit, select_earnings_filing)

SUBMISSIONS = {"filings": {"recent": {
    "accessionNumber": ["0001-26-000003", "0001-26-000002", "0001-26-000001"],
    "filingDate": ["2026-11-03", "2026-11-03", "2026-10-20"],
    "acceptanceDateTime": ["2026-11-03T16:05:11.000Z", "2026-11-03T08:00:00.000Z", "2026-10-20T09:00:00.000Z"],
    "form": ["8-K", "4", "8-K"],
    "items": ["2.02,9.01", "", "5.02"],
    "primaryDocument": ["a8k.htm", "form4.xml", "b8k.htm"],
}}}


def test_finds_the_earnings_8k_filed_on_the_date():
    found = select_earnings_filing(SUBMISSIONS, "2026-11-03")
    assert found == {"accession": "0001-26-000003", "filing_date": "2026-11-03", "accepted": "2026-11-03T16:05:11.000Z", "primary": "a8k.htm"}


def test_ignores_non_earnings_8ks_other_forms_and_other_dates():
    assert select_earnings_filing(SUBMISSIONS, "2026-10-20") is None   # an 8-K, but item 5.02
    assert select_earnings_filing(SUBMISSIONS, "2026-11-04") is None   # nothing that day
    assert select_earnings_filing({"filings": {"recent": {k: [] for k in SUBMISSIONS["filings"]["recent"]}}}, "2026-11-03") is None


def test_pick_exhibit_prefers_the_press_release_exhibit_over_the_main_document():
    index = {"directory": {"item": [{"name": "a8k.htm"}, {"name": "amd-20261103xex991.htm"}, {"name": "image.jpg"}, {"name": "a8k.xml"}]}}
    assert pick_exhibit(index, primary="a8k.htm") == "amd-20261103xex991.htm"


@pytest.mark.parametrize("name", ["d123dex991.htm", "ex99-1.htm", "ex-99.1.htm", "q3ex991pressrelease.htm", "EX99_1.HTM"])
def test_pick_exhibit_recognises_common_exhibit_names(name):
    assert pick_exhibit({"directory": {"item": [{"name": "main.htm"}, {"name": name}]}}, primary="main.htm") == name


def test_pick_exhibit_falls_back_to_the_primary_document_when_there_is_no_exhibit():
    assert pick_exhibit({"directory": {"item": [{"name": "main.htm"}, {"name": "logo.png"}]}}, primary="main.htm") == "main.htm"


def test_html_to_text_strips_markup_scripts_and_entities():
    html = "<html><head><style>p{color:red}</style><script>var x=1;</script></head><body><h1>Q3 &amp; Results</h1><p>Revenue&nbsp;up <b>45%</b></p><table><tr><td>A</td><td>1</td></tr></table></body></html>"
    text = html_to_text(html)
    assert "Q3 & Results" in text and "Revenue up 45%" in text and "color:red" not in text and "var x" not in text
    assert "<" not in text and "  " not in text


def test_cik_lookup_pads_to_ten_digits_and_is_case_insensitive():
    mapping = {"0": {"cik_str": 2488, "ticker": "AMD", "title": "ADVANCED MICRO DEVICES INC"}, "1": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA"}}
    assert cik_for("amd", mapping) == "0000002488"
    assert cik_for("NVDA", mapping) == "0001045810"
    assert cik_for("ZZZZ", mapping) is None


def test_throttle_spaces_requests_at_least_the_minimum_interval_apart():
    now = [100.0]
    sleeps = []

    def sleep(s):
        sleeps.append(s)
        now[0] += s

    t = Throttle(min_interval=0.2, clock=lambda: now[0], sleep=sleep)
    t.wait()            # first call: no wait
    now[0] += 0.05
    t.wait()            # 0.05 s later: must wait about 0.15 s
    now[0] += 1.0
    t.wait()            # long after: no wait
    assert sleeps == [pytest.approx(0.15)]


def test_edgar_error_carries_the_url():
    err = EdgarError("https://x", "HTTP 403")
    assert "https://x" in str(err) and "403" in str(err)
