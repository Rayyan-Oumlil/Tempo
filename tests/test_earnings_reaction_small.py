from tempo.snapshots import borrow_features
import pytest

from tempo import earnings_reaction as big
from tempo import earnings_reaction_small as small
from tests.test_ledger import make_ledger


def m(close=10.0, adv=1_000_000.0, reaction=0.08, status="ok"):
    return {"status": status, "close": close, "adv20": adv, "reaction": reaction}


@pytest.mark.parametrize("adv, in_small, in_big", [
    (499_999.0, False, False), (500_000.0, True, False), (4_999_999.0, True, False),
    (5_000_000.0, False, True), (50_000_000.0, False, True)])
def test_the_two_sources_split_the_liquidity_range_without_overlap_or_gap_above_the_floor(adv, in_small, in_big):
    assert small.in_band(m(adv=adv)) is in_small
    assert (big.decide(m(adv=adv)) is not None) is in_big
    assert not (small.in_band(m(adv=adv)) and big.decide(m(adv=adv)) is not None)


def test_price_floor_status_and_threshold():
    assert small.decide(m(close=2.99)) is None and small.decide(m(close=3.0)) == 1
    assert small.decide(m(status="no_bar")) is None
    assert small.decide(m(reaction=0.05)) == 1 and small.decide(m(reaction=-0.05)) == -1
    assert small.decide(m(reaction=0.0499)) is None and small.decide(m(reaction=-0.0499)) is None


def test_signals_carry_the_registered_cost_and_are_not_repeated_within_30_days(tmp_path):
    ledger = make_ledger(tmp_path)
    hit = {"symbol": "AAA", "direction": -1, "day": "2026-11-11", "reaction": -0.0712345, "close": 4.2, "adv20": 750_000.0, "accession": "x"}
    first = small.record_signals([hit, {**hit, "symbol": "BBB", "direction": 1, "reaction": 0.09}], ledger)
    assert [r["signal_id"] for r in first] == [f"{small.SOURCE}:AAA:20261111", f"{small.SOURCE}:BBB:20261111"]
    assert first[0]["features"]["round_trip_cost"] == 0.006 and first[0]["features"]["reaction"] == -0.07123
    assert small.record_signals([hit], ledger) == []
    again = {**hit, "day": "2026-11-12"}                      # a NEW event for the same issuer: only the 30-day rule can stop it
    assert small.record_signals([again], ledger) == []


def test_the_registration_file_matches_the_code():
    import json
    from pathlib import Path
    reg = json.loads((Path(__file__).resolve().parents[1] / "evidence" / "earnings_reaction_small_forward.json").read_text(encoding="utf-8"))
    assert reg["source_name"] == small.SOURCE and "0.006" in reg["cost_assumption"]
    assert "500,000" in reg["liquidity_band"] and "3.00" in reg["liquidity_band"]


def test_borrow_terms_are_logged_beside_the_signal_and_missing_data_is_not_a_zero_fee(tmp_path):
    from tempo.snapshots import Borrow
    ledger = make_ledger(tmp_path)
    hit = {"symbol": "AAA", "direction": -1, "day": "2026-11-11", "reaction": -0.07, "close": 4.2, "adv20": 750_000.0, "accession": "x"}
    table = {"AAA": Borrow(rebate=-33.0, fee=38.0, available=100_000, capped=True)}
    got = small.record_signals([hit, {**hit, "symbol": "BBB"}], ledger, table)
    assert got[0]["features"]["borrow_fee"] == 38.0 and got[0]["features"]["borrow_available"] == 100_000
    assert got[0]["features"]["borrow_capped"] is True and got[0]["features"]["borrow_known"] is True
    assert got[1]["features"] == {**got[1]["features"], "borrow_known": False} and "borrow_fee" not in got[1]["features"]
    assert borrow_features("AAA", None) == {"borrow_known": False}
    assert borrow_features("NA", {"NA": Borrow(None, None, None, False)})["borrow_fee"] is None
