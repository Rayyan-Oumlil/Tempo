from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from tempo.insider_history import HistoryMissing
from tempo.insider_opp import SOURCE, opportunistic_signals, record_signals
from tempo.ledger import Ledger

ET = ZoneInfo("America/New_York")
ASOF = date(2026, 11, 10)
IDX = {"years": [2023, 2024, 2025], "owners": {"77": ["2023-11", "2024-11", "2025-11"]}}   # owner 77 is routine in November


def buy(symbol="ACME", od=("11",), value=60_000.0, price=10.0, filing="2026-11-10", trade="2026-11-06", acc="A1", cik="555"):
    return {"accession": acc, "filing_date": filing, "trade_date": trade, "issuer_cik": cik, "symbol": symbol, "owners": list(od),
            "officer_director": list(od), "shares": value / price, "price": price, "value": value}


def test_an_opportunistic_director_purchase_of_50k_at_5_dollars_signals():
    (s,) = opportunistic_signals([buy()], ASOF, IDX)
    assert (s["symbol"], s["value"], s["vwap"], s["last_filing_date"]) == ("ACME", 60_000.0, 10.0, "2026-11-10")


def test_routine_buyers_do_not_count():
    assert opportunistic_signals([buy(od=("77",))], ASOF, IDX) == []
    assert opportunistic_signals([buy(od=("0000000077",))], ASOF, IDX) == []   # leading zeros are the same person


def test_a_filing_counts_if_at_least_one_of_its_officers_or_directors_is_opportunistic():
    assert len(opportunistic_signals([buy(od=("77", "11"))], ASOF, IDX)) == 1


def test_thresholds_value_price_and_window():
    assert opportunistic_signals([buy(value=49_000.0)], ASOF, IDX) == []
    assert opportunistic_signals([buy(price=4.99)], ASOF, IDX) == []
    assert opportunistic_signals([buy(filing="2026-11-07")], ASOF, IDX) == []          # 3 calendar days: 08, 09, 10
    assert len(opportunistic_signals([buy(filing="2026-11-08")], ASOF, IDX)) == 1
    assert opportunistic_signals([buy(filing="2026-11-11")], ASOF, IDX) == []          # the future is never used
    two = [buy(value=30_000.0, acc="A1"), buy(value=25_000.0, acc="A2", od=("12",))]
    assert opportunistic_signals(two, ASOF, IDX)[0]["value"] == 55_000.0               # adds up per issuer


def test_purchases_without_roles_or_by_ten_percent_owners_only_do_not_count():
    old_cache_row = {k: v for k, v in buy().items() if k != "officer_director"}        # cached before roles were parsed
    assert opportunistic_signals([old_cache_row], ASOF, IDX) == []
    assert opportunistic_signals([buy(od=())], ASOF, IDX) == []


def test_the_routine_test_uses_the_trade_month_and_needs_history():
    assert len(opportunistic_signals([buy(od=("77",), trade="2026-10-30")], ASOF, IDX)) == 1   # routine in Nov, not Oct
    with pytest.raises(HistoryMissing):
        opportunistic_signals([buy()], ASOF, {"years": [2024, 2025], "owners": {}})


def ledger_at(tmp_path, day):
    return Ledger(tmp_path / "ledger.jsonl", clock=lambda: datetime(day.year, day.month, day.day, 8, 0, tzinfo=ET).timestamp())


def test_signals_are_recorded_long_with_their_cost_and_not_repeated_within_30_days(tmp_path):
    found = opportunistic_signals([buy()], ASOF, IDX)
    (rec,) = record_signals(found, ledger_at(tmp_path, date(2026, 11, 11)))
    assert rec["source"] == SOURCE and rec["direction"] == 1 and rec["event_id"] == "20261110"
    assert rec["features"]["round_trip_cost"] == 0.005 and rec["features"]["n_opportunistic"] == 1
    again = opportunistic_signals([buy(filing="2026-11-20", acc="A9")], date(2026, 11, 20), IDX)
    assert record_signals(again, ledger_at(tmp_path, date(2026, 11, 21))) == []
    later = opportunistic_signals([buy(filing="2026-12-15", acc="B1")], date(2026, 12, 15), IDX)
    assert len(record_signals(later, ledger_at(tmp_path, date(2026, 12, 16)))) == 1
