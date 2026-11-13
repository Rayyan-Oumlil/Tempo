import gzip
from datetime import date

import pytest

from tempo import events_scan as ev

FILLER = "\n".join(
    f"8-K              Filler {i} Corp                                               {1000 + i}     2024-01-0{1 + i % 9}  edgar/data/{1000 + i}/0000000000-24-{i:06d}.txt"
    for i in range(1200))
HEAD = "Form Type   Company Name                                                  CIK         Date Filed  File Name\n" + "-" * 120 + "\n"
TOI = "SC TO-I          A&Q Long/Short Strategies Fund LLC                            1186641     2024-03-22  edgar/data/1186641/0001104659-24-037891.txt         "
TOIA = "SC TO-I/A        A&Q Long/Short Strategies Fund LLC                            1186641     2024-03-25  edgar/data/1186641/0001104659-24-038000.txt         "
SPIN = "10-12B           Acme Spin Holdings Inc                                        1234567     2024-02-02  edgar/data/1234567/0001193125-24-000111.txt         "


def index(extra: str) -> str:
    return HEAD + FILLER + "\n" + extra + "\n"


def test_parse_keeps_original_filings_only_and_extracts_the_accession():
    rows = ev.parse_form_index(index(f"{TOI}\n{TOIA}\n{SPIN}"))
    assert [r["form"] for r in rows] == ["SC TO-I", "10-12B"]
    assert rows[0]["accession"] == "0001104659-24-037891" and rows[0]["cik"] == "1186641" and rows[0]["filed"] == "2024-03-22"
    assert rows[0]["fund_like"] is True and rows[1]["fund_like"] is False


@pytest.mark.parametrize("text", ["", "no header here\n" * 500, "x\n-----\nshort\n"], ids=["empty", "no-rule", "too-short"])
def test_parse_refuses_a_file_that_is_not_an_index(text):
    with pytest.raises(ev.FormIndexError):
        ev.parse_form_index(text)


def test_parse_refuses_a_changed_row_format():
    with pytest.raises(ev.FormIndexError):
        ev.parse_form_index(index("").replace("  edgar/", "|edgar/"))


def test_quarter_bookkeeping():
    qs = ev.quarters(2025, date(2026, 11, 13))
    assert qs[-1] == (2026, 4) and len(qs) == 8
    assert ev.quarter_complete(2026, 3, date(2026, 11, 13)) and not ev.quarter_complete(2026, 4, date(2026, 11, 13))
    assert ev.quarter_complete(2025, 4, date(2026, 1, 1)) and not ev.quarter_complete(2025, 4, date(2025, 12, 31))


def test_completed_quarters_are_fetched_once_and_the_running_one_always(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        return gzip.compress(index(TOI).encode())

    today = date(2026, 11, 13)
    first = ev.scan(2026, today, fetch, tmp_path)
    n = len(calls)
    assert n == 4 and len(first) == 1            # same accession in every quarter -> deduplicated
    ev.scan(2026, today, fetch, tmp_path)
    assert len(calls) == n + 1 and "QTR4" in calls[-1]


def test_a_non_gzip_download_fails_loudly_and_is_not_cached(tmp_path):
    with pytest.raises(ev.FormIndexError):
        ev.load_quarter(2024, 1, date(2026, 1, 1), lambda url: b"<html>blocked</html>", tmp_path)
    assert not list(tmp_path.iterdir())


def test_per_year_counts_and_csv(tmp_path):
    rows = ev.parse_form_index(index(f"{TOI}\n{SPIN}"))
    assert ev.per_year(rows)["SC TO-I"]["2024"] == 1
    ev.write_csv(rows, tmp_path / "e.csv")
    assert (tmp_path / "e.csv").read_text().splitlines()[0] == "form,filed,cik,company,accession,fund_like"


def test_enrich_fetches_once_retries_errors_and_marks_listed(tmp_path):
    import json as js
    calls = []

    def fetch(url):
        calls.append(url)
        if "0000000002" in url and calls.count(url) == 1:
            raise ev.edgar.EdgarError(url, "HTTP 503")
        return js.dumps({"sic": "7372", "sicDescription": "Software", "tickers": ["X"], "exchanges": ["Nasdaq"] if "0000000001" in url else [""], "entityType": "operating"})

    path = tmp_path / "m.json"
    meta = ev.enrich(["1", "2"], fetch, path)
    assert "error" in meta["2"] and ev.is_listed(meta["1"]) and not ev.is_listed(meta["2"])
    ev.enrich(["1", "2"], fetch, path)                       # only the failed one is asked again
    assert len(calls) == 3 and "sic" in js.loads(path.read_text())["2"]
    rows = [{"form": "SC TO-I", "filed": "2024-03-22", "cik": "1"}, {"form": "SC TO-I", "filed": "2024-05-01", "cik": "2"}]
    assert ev.listed_per_year(rows, js.loads(path.read_text()))["SC TO-I"]["2024"] == 1


def test_a_dropped_connection_becomes_an_edgar_error(monkeypatch):
    import http.client
    import urllib.request

    monkeypatch.setenv("SEC_USER_AGENT", "test agent")
    monkeypatch.setattr(ev.edgar, "load_dotenv", lambda: None)

    def boom(*a, **k):
        raise http.client.RemoteDisconnected("closed")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(ev.edgar.EdgarError):
        ev.edgar.fetch_bytes("https://data.sec.gov/x")
