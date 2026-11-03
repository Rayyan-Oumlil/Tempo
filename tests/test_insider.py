from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from tempo.insider import clusters, new_signals, parse_form4, parse_index
from tempo.ledger import Ledger

INDEX = """Description:           Master Index of EDGAR Dissemination Feed by Form Type
Last Data Received:    Nov 02, 2026

Form Type   Company Name                                                  CIK         Date Filed  File Name
---------------------------------------------------------------------------------------------------------------------------------------------
4           2018 Reed Dynasty Trust                                       1889614     20261102    edgar/data/1889614/0001889614-26-000011.txt
4           ACME CORP                                                     555         20261102    edgar/data/555/0001889614-26-000011.txt
4           3M CO                                                         66740       20261102    edgar/data/66740/0000066740-26-000314.txt
4/A         AMENDED INC                                                   777         20261102    edgar/data/777/0000000777-26-000001.txt
8-K         SOME OTHER CO                                                 888         20261102    edgar/data/888/0000000888-26-000002.txt
"""


def form4(owners=(("0001", "Alice A"),), symbol="ACME", txs=(("P", "A", 1000, 12.5, "2026-10-30"),), aff="0", issuer_cik="0000555"):
    owner_xml = "".join(f"<reportingOwner><reportingOwnerId><rptOwnerCik>{c}</rptOwnerCik><rptOwnerName>{n}</rptOwnerName></reportingOwnerId></reportingOwner>" for c, n in owners)
    tx_xml = "".join(
        f"<nonDerivativeTransaction><transactionDate><value>{d}</value></transactionDate><transactionCoding><transactionCode>{code}</transactionCode></transactionCoding>"
        f"<transactionAmounts><transactionShares><value>{sh}</value></transactionShares><transactionPricePerShare><value>{px}</value></transactionPricePerShare>"
        f"<transactionAcquiredDisposedCode><value>{ad}</value></transactionAcquiredDisposedCode></transactionAmounts></nonDerivativeTransaction>"
        for code, ad, sh, px, d in txs)
    return (f"<SEC-DOCUMENT>junk header\n<ownershipDocument><documentType>4</documentType><issuer><issuerCik>{issuer_cik}</issuerCik>"
            f"<issuerName>Acme</issuerName><issuerTradingSymbol>{symbol}</issuerTradingSymbol></issuer>{owner_xml}<aff10b5One>{aff}</aff10b5One>"
            f"<nonDerivativeTable>{tx_xml}</nonDerivativeTable></ownershipDocument>\n</SEC-DOCUMENT>")


def test_index_lists_each_form_4_filing_once_and_ignores_other_forms():
    rows = parse_index(INDEX)
    assert [r["accession"] for r in rows] == ["0001889614-26-000011", "0000066740-26-000314"]  # the owner and issuer lines of one filing merge
    assert rows[0]["path"] == "edgar/data/1889614/0001889614-26-000011.txt" and rows[0]["filing_date"] == "2026-11-02"


def test_a_purchase_is_extracted_with_value_and_owner():
    buys = parse_form4(form4(), filing_date="2026-11-02", accession="A1")
    assert buys == [{"accession": "A1", "filing_date": "2026-11-02", "trade_date": "2026-10-30", "issuer_cik": "0000555",
                     "symbol": "ACME", "owners": ["0001"], "shares": 1000.0, "price": 12.5, "value": 12500.0}]


def test_only_open_market_purchases_count():
    txs = (("M", "A", 100, 10, "2026-10-30"), ("F", "D", 50, 10, "2026-10-30"), ("S", "D", 10, 10, "2026-10-30"),
           ("A", "A", 100, 0, "2026-10-30"), ("P", "D", 10, 10, "2026-10-30"), ("P", "A", 10, 10, "2026-10-30"))
    buys = parse_form4(form4(txs=txs), "2026-11-02", "A1")
    assert [b["shares"] for b in buys] == [10.0]


def test_pre_planned_10b5_1_purchases_and_unpriced_or_odd_symbols_are_ignored():
    assert parse_form4(form4(aff="1"), "2026-11-02", "A1") == []
    assert parse_form4(form4(txs=(("P", "A", 100, 0, "2026-10-30"),)), "2026-11-02", "A1") == []
    assert parse_form4(form4(symbol="BRK-B"), "2026-11-02", "A1") == []
    assert parse_form4(form4(symbol=""), "2026-11-02", "A1") == []


def test_a_filing_without_a_document_gives_nothing():
    assert parse_form4("<html>not a form 4</html>", "2026-11-02", "A1") == []


def test_several_owners_are_all_recorded():
    buys = parse_form4(form4(owners=(("0001", "A"), ("0002", "B"))), "2026-11-02", "A1")
    assert buys[0]["owners"] == ["0001", "0002"]


def buy(owner, value=150_000.0, price=10.0, filed="2026-11-02", symbol="ACME", acc=None):
    return {"accession": acc or f"{owner}-{filed}", "filing_date": filed, "trade_date": filed, "issuer_cik": "555", "symbol": symbol,
            "owners": [owner], "shares": value / price, "price": price, "value": value}


ASOF = date(2026, 11, 2)


def test_two_insiders_and_enough_money_make_a_cluster():
    found = clusters([buy("1", 120_000), buy("2", 100_000)], ASOF)
    assert len(found) == 1 and found[0]["symbol"] == "ACME" and found[0]["owners"] == ["1", "2"]
    assert found[0]["value"] == pytest.approx(220_000) and found[0]["vwap"] == pytest.approx(10.0)
    assert found[0]["last_filing_date"] == "2026-11-02"


def test_one_insider_is_not_a_cluster_even_if_large():
    assert clusters([buy("1", 5_000_000)], ASOF) == []
    assert clusters([buy("1", 3_000_000), buy("1", 2_000_000, acc="x")], ASOF) == []  # the same person twice


def test_the_money_and_price_thresholds_apply_to_the_total():
    assert clusters([buy("1", 90_000), buy("2", 100_000)], ASOF) == []                         # 190k: under 200k
    assert clusters([buy("1", 150_000, price=4.0), buy("2", 150_000, price=4.0)], ASOF) == []  # price under 5
    assert len(clusters([buy("1", 100_000), buy("2", 100_000)], ASOF)) == 1                    # exactly 200k passes


def test_vwap_weights_by_value():
    found = clusters([buy("1", 300_000, price=10.0), buy("2", 100_000, price=20.0)], ASOF)
    assert found[0]["vwap"] == pytest.approx(400_000 / (30_000 + 5_000))


def test_only_the_last_seven_days_of_filings_count_and_nothing_from_the_future():
    old = buy("1", 150_000, filed="2026-10-25")        # 8 days before: outside the window
    inside = buy("1", 150_000, filed="2026-10-27")     # 6 days before: inside
    future = buy("3", 150_000, filed="2026-11-03")     # after the as-of day: never used
    assert clusters([old, buy("2", 150_000)], ASOF) == []
    assert len(clusters([inside, buy("2", 150_000)], ASOF)) == 1
    assert clusters([buy("2", 150_000), future], ASOF) == []


def test_clusters_are_per_issuer():
    mixed = [buy("1", 150_000, symbol="AAA"), buy("2", 150_000, symbol="BBB")]
    assert clusters(mixed, ASOF) == []


def test_new_signals_skips_an_issuer_signalled_in_the_last_thirty_days(tmp_path):
    ET = ZoneInfo("America/New_York")
    ledger = Ledger(tmp_path / "l.jsonl", clock=lambda: datetime(2026, 11, 3, 9, 0, tzinfo=ET).timestamp())
    found = clusters([buy("1", 150_000), buy("2", 150_000)], ASOF)
    first = new_signals(found, ledger)
    assert [s["symbol"] for s in first] == ["ACME"] and first[0]["features"]["round_trip_cost"] == 0.005
    assert first[0]["direction"] == 1 and first[0]["event_id"] == "20261102"
    assert new_signals(found, ledger) == []   # the same cluster is not signalled twice
    later = Ledger(tmp_path / "l.jsonl", clock=lambda: datetime(2026, 12, 15, 9, 0, tzinfo=ET).timestamp())
    again = clusters([buy("1", 150_000, filed="2026-12-14"), buy("2", 150_000, filed="2026-12-14")], date(2026, 12, 14))
    assert len(new_signals(again, later)) == 1  # 40 days on, a new cluster may signal again


def test_xml_with_a_dtd_or_entities_is_refused_not_expanded():
    bomb = ('<SEC-DOCUMENT><!DOCTYPE lolz [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]>'
            + form4().split("<SEC-DOCUMENT>junk header\n")[1].replace("<issuerName>Acme</issuerName>", "<issuerName>&b;</issuerName>"))
    assert parse_form4(bomb, "2026-11-02", "A1") == []
    assert parse_form4(form4().replace("<ownershipDocument>", "<ownershipDocument><!ENTITY x 'y'>", 1), "2026-11-02", "A1") == []


def test_an_absurdly_large_document_is_refused():
    huge = form4().replace("<aff10b5One>0</aff10b5One>", "<aff10b5One>0</aff10b5One><remarks>" + "x" * 600_000 + "</remarks>")
    assert parse_form4(huge, "2026-11-02", "A1") == []


def test_the_window_is_exactly_seven_calendar_days():
    seven_days_before = buy("1", 150_000, filed="2026-10-26")   # asof 2026-11-02 minus 7 days: outside
    six_days_before = buy("1", 150_000, filed="2026-10-27")     # inside
    assert clusters([seven_days_before, buy("2", 150_000)], ASOF) == []
    assert len(clusters([six_days_before, buy("2", 150_000)], ASOF)) == 1


def test_an_issuer_signalled_recently_is_skipped_even_for_a_new_cluster_event(tmp_path):
    ET = ZoneInfo("America/New_York")
    first = Ledger(tmp_path / "l.jsonl", clock=lambda: datetime(2026, 11, 3, 9, 0, tzinfo=ET).timestamp())
    new_signals(clusters([buy("1", 150_000), buy("2", 150_000)], ASOF), first)
    week_later = Ledger(tmp_path / "l.jsonl", clock=lambda: datetime(2026, 11, 11, 9, 0, tzinfo=ET).timestamp())
    fresh = clusters([buy("3", 150_000, filed="2026-11-10"), buy("4", 150_000, filed="2026-11-10")], date(2026, 11, 10))
    assert fresh and new_signals(fresh, week_later) == []   # different event id, same issuer, 8 days later: still skipped


from tempo.edgar import EdgarError
from tempo.insider import load_cache, process_day


def fake_fetcher(urls, fail_on=None):
    def fetch(url):
        urls.append(url)
        if "daily-index" in url:
            return INDEX
        if fail_on and fail_on in url:
            raise EdgarError(url, "HTTP 500")
        return form4()
    return fetch


def test_process_day_uses_the_real_url_layout_and_caches_purchases(tmp_path):
    urls = []
    stats = process_day(date(2026, 11, 2), fetcher=fake_fetcher(urls), cache=tmp_path / "c.jsonl", say=lambda *_: None)
    assert urls[0] == "https://www.sec.gov/Archives/edgar/daily-index/2026/QTR4/form.20261102.idx"
    assert urls[1:] == ["https://www.sec.gov/Archives/edgar/data/1889614/0001889614-26-000011.txt",
                        "https://www.sec.gov/Archives/edgar/data/66740/0000066740-26-000314.txt"]
    assert stats == {"filings": 2, "new": 2, "purchases": 2, "failed": 0}
    seen, buys = load_cache(tmp_path / "c.jsonl")
    assert seen == {"0001889614-26-000011", "0000066740-26-000314"} and len(buys) == 2


def test_a_second_run_downloads_no_filing_again(tmp_path):
    cache = tmp_path / "c.jsonl"
    process_day(date(2026, 11, 2), fetcher=fake_fetcher([]), cache=cache, say=lambda *_: None)
    urls = []
    stats = process_day(date(2026, 11, 2), fetcher=fake_fetcher(urls), cache=cache, say=lambda *_: None)
    assert len(urls) == 1 and stats["new"] == 0   # only the index


def test_a_failed_filing_is_retried_next_time_not_marked_as_seen(tmp_path):
    cache = tmp_path / "c.jsonl"
    stats = process_day(date(2026, 11, 2), fetcher=fake_fetcher([], fail_on="66740"), cache=cache, say=lambda *_: None)
    assert stats["failed"] == 1 and stats["purchases"] == 1
    assert "0000066740-26-000314" not in load_cache(cache)[0]
    urls = []
    again = process_day(date(2026, 11, 2), fetcher=fake_fetcher(urls), cache=cache, say=lambda *_: None)
    assert again["new"] == 1 and again["failed"] == 0 and len(urls) == 2   # the index and only the failed filing
