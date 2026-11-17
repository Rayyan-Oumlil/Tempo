import io
import zipfile
from datetime import date, timedelta

from tempo.history_core import Series
from tempo.history_insider import buys_from_zip, signals, to_trades

SUB = "ACCESSION_NUMBER\tFILING_DATE\tDOCUMENT_TYPE\tISSUERCIK\tISSUERTRADINGSYMBOL\tAFF10B5ONE\n"
OWN = "ACCESSION_NUMBER\tRPTOWNERCIK\tRPTOWNER_RELATIONSHIP\n"
TRN = "ACCESSION_NUMBER\tTRANS_DATE\tTRANS_CODE\tTRANS_SHARES\tTRANS_PRICEPERSHARE\tTRANS_ACQUIRED_DISP_CD\n"


def make_zip(subs, owns, trns, sub_header=SUB):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("SUBMISSION.tsv", sub_header + "".join("\t".join(r) + "\n" for r in subs))
        z.writestr("REPORTINGOWNER.tsv", OWN + "".join("\t".join(r) + "\n" for r in owns))
        z.writestr("NONDERIV_TRANS.tsv", TRN + "".join("\t".join(r) + "\n" for r in trns))
    return buf.getvalue()


def test_only_counted_purchases_are_rebuilt_in_the_live_shape():
    raw = make_zip(
        subs=[("A1", "05-MAR-2024", "4", "0000555", "ACME", "0"),
              ("A2", "05-MAR-2024", "4/A", "0000555", "ACME", "0"),       # amendment
              ("A3", "05-MAR-2024", "4", "0000555", "ACME", "1"),         # pre-planned 10b5-1
              ("A4", "05-MAR-2024", "4", "0000555", "ACME", "0"),         # a sale
              ("A5", "05-MAR-2024", "4", "0000555", "BRK.A", "0"),        # odd symbol
              ("A6", "05-MAR-2024", "4", "0000555", "NONE", "0")],        # placeholder symbol
        owns=[("A1", "0000111", "Officer"), ("A1", "0000222", "10% Owner"), ("A2", "0000111", "Officer"), ("A3", "0000111", "Officer"),
              ("A4", "0000111", "Officer"), ("A5", "0000111", "Officer"), ("A6", "0000111", "Officer")],
        trns=[("A1", "04-MAR-2024", "P", "10000", "10", "A"), ("A2", "04-MAR-2024", "P", "10000", "10", "A"),
              ("A3", "04-MAR-2024", "P", "10000", "10", "A"), ("A4", "04-MAR-2024", "S", "10000", "10", "D"),
              ("A5", "04-MAR-2024", "P", "10000", "10", "A"), ("A6", "04-MAR-2024", "P", "10000", "10", "A")])
    (b,) = buys_from_zip(raw)
    assert b == {"accession": "A1", "filing_date": "2024-03-05", "trade_date": "2024-03-04", "issuer_cik": "0000555", "symbol": "ACME",
                 "owners": ["0000111", "0000222"], "officer_director": ["0000111"], "shares": 10000.0, "price": 10.0, "value": 100000.0}


def test_sets_before_2023_have_no_10b5_1_column_and_are_still_read():
    raw = make_zip(subs=[("A1", "05-MAR-2021", "4", "0000555", "ACME")], owns=[("A1", "0000111", "Director")],
                   trns=[("A1", "04-MAR-2021", "P", "100", "20", "A")], sub_header="ACCESSION_NUMBER\tFILING_DATE\tDOCUMENT_TYPE\tISSUERCIK\tISSUERTRADINGSYMBOL\n")
    assert len(buys_from_zip(raw)) == 1


def weekdays(start, end):
    d, out = date.fromisoformat(start), []
    while d <= date.fromisoformat(end):
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def buy(acc, filed, owner, value, symbol="ACME", officer=True):
    return {"accession": acc, "filing_date": filed, "trade_date": filed, "issuer_cik": "555", "symbol": symbol, "owners": [owner],
            "officer_director": [owner] if officer else [], "shares": value / 10, "price": 10.0, "value": float(value)}


INDEX = {"years": [2021, 2022, 2023], "owners": {}}
CAL = weekdays("2024-02-01", "2024-06-28")


def test_a_cluster_is_entered_at_the_next_session_and_not_repeated_within_30_days():
    buys = [buy("a", "2024-03-05", "1", 150_000), buy("b", "2024-03-06", "2", 150_000),            # cluster as of 03-06
            buy("c", "2024-03-15", "3", 150_000), buy("d", "2024-03-15", "4", 150_000),            # 9 days later: suppressed
            buy("e", "2024-04-22", "5", 150_000), buy("f", "2024-04-22", "6", 150_000)]            # 47 days later: allowed again
    out = signals(buys, INDEX, CAL, "2024-03-01")
    assert out["insider_cluster_v1"] == [("2024-03-07", "ACME"), ("2024-04-23", "ACME")]


def test_one_insider_is_an_opportunistic_signal_but_not_a_cluster():
    out = signals([buy("a", "2024-03-05", "1", 80_000)], INDEX, CAL, "2024-03-01")
    assert out["insider_cluster_v1"] == [] and out["insider_opportunistic_v1"] == [("2024-03-06", "ACME")]


def test_a_routine_buyer_is_not_opportunistic():
    routine = {"years": [2021, 2022, 2023], "owners": {"1": ["2021-03", "2022-03", "2023-03"]}}
    out = signals([buy("a", "2024-03-05", "1", 80_000)], routine, CAL, "2024-03-01")
    assert out["insider_opportunistic_v1"] == []


def test_entries_outside_the_window_are_ignored_and_the_2026_holdout_is_never_entered():
    cal = weekdays("2025-12-01", "2026-01-30")
    buys = [buy("a", "2025-12-22", "1", 80_000), buy("b", "2025-12-29", "1", 80_000, symbol="LATE")]
    out = signals(buys, {"years": [2022, 2023, 2024], "owners": {}}, cal, "2025-12-01")
    assert out["insider_opportunistic_v1"] == [("2025-12-23", "ACME")]      # the 12-29 filing would enter after the cap
    assert signals([buy("a", "2025-12-22", "1", 80_000)], {"years": [2022, 2023, 2024], "owners": {}}, cal, "2025-12-24")["insider_opportunistic_v1"] == []


def flat(dates, px=10.0):
    return Series(dates, [px] * len(dates), [px] * len(dates), [1e6] * len(dates))


def test_to_trades_counts_what_it_cannot_score_instead_of_guessing():
    dates = weekdays("2024-01-01", "2024-06-28")
    spy = Series(dates, [100.0 + (i % 5) for i in range(len(dates))], [100.0 + ((i + 1) % 5) for i in range(len(dates))], [1e6] * len(dates))
    have = {"OK": flat(dates), "SHORT": Series(dates[:50], [10.0] * 50, [10.0] * 50, [1e6] * 50)}
    trades, counts = to_trades([("2024-05-06", "OK"), ("2024-05-06", "GONE"), ("2024-05-06", "SHORT")], spy, have.get)
    assert counts == {"scored": 1, "no_bars": 1, "unscored": 1} and [t.symbol for t in trades] == ["OK"]


def test_a_purchase_filed_more_than_a_year_after_the_trade_is_not_a_signal():
    late = dict(buy("a", "2024-03-05", "1", 80_000), trade_date="2023-01-10")
    assert signals([late], INDEX, CAL, "2024-03-01")["insider_opportunistic_v1"] == []
    fresh = dict(buy("a", "2024-03-05", "1", 80_000), trade_date="2024-03-01")
    assert signals([fresh], INDEX, CAL, "2024-03-01")["insider_opportunistic_v1"] == [("2024-03-06", "ACME")]
