from datetime import date

import pytest

from tempo.short_volume import SOURCE, candidates, ratio, record_signals, zscores
from tests.test_ledger import make_ledger


def day(**sym):
    return {s: v for s, v in sym.items()}


def test_ratio_is_short_over_total_and_none_for_no_volume():
    assert ratio((50.0, 200.0)) == 0.25
    assert ratio((5.0, 0.0)) is None


def test_zscore_compares_today_with_the_stocks_own_history():
    history = [{"A": (40_000.0 + (i % 2) * 2_000, 100_000.0)} for i in range(20)]        # ratio 0.40 / 0.42, sd 0.01 -> floored at 0.02
    today = {"A": (50_000.0, 100_000.0)}                                         # ratio 0.50
    z = zscores(today, history, ["A"])
    assert z["A"] == pytest.approx((0.50 - 0.41) / 0.02)


def test_zscore_skips_thin_volume_short_history_and_unknown_symbols():
    history = [{"A": (40_000.0, 100_000.0), "B": (40_000.0, 100_000.0)} for _ in range(20)]
    today = {"A": (60_000.0, 99_999.0), "B": (60_000.0, 100_000.0)}
    assert set(zscores(today, history, ["A", "B", "C"])) == {"B"}                   # A under 100k shares, C absent
    assert zscores(today, history[:14], ["B"]) == {}                                # 14 baseline days is too few
    assert set(zscores(today, history[:15], ["B"])) == {"B"}


def test_the_baseline_excludes_today_and_floors_the_deviation():
    flat = [{"A": (40_000.0, 100_000.0)} for _ in range(20)]
    z = zscores({"A": (42_000.0, 100_000.0)}, flat, ["A"])
    assert z["A"] == pytest.approx(1.0)                                            # (0.42 - 0.40) / floor 0.02


def test_candidates_put_the_lowest_z_on_the_long_side_and_the_highest_on_the_short_side():
    z = {f"S{i:03d}": float(i) for i in range(120)}
    longs, shorts = candidates(z, per_side=3)
    assert longs == ["S000", "S001", "S002"] and shorts == ["S119", "S118", "S117"]


def test_candidates_refuse_a_thin_universe_and_break_ties_by_symbol():
    assert candidates({f"S{i}": 0.0 for i in range(99)}) == ([], [])
    tie = {f"S{i:03d}": 0.0 for i in range(100)}
    assert candidates(tie, per_side=2)[0] == ["S000", "S001"]


def test_signals_are_recorded_once_with_the_registered_cost(tmp_path):
    ledger = make_ledger(tmp_path)
    info = {"AAA": {"close": 10.0, "z": 3.14159}, "BBB": {"close": 20.0, "z": -2.0}}
    picks = [("AAA", -1), ("BBB", 1)]
    first = record_signals(picks, info, date(2026, 11, 11), ledger)
    assert [r["signal_id"] for r in first] == [f"{SOURCE}:AAA:20261111", f"{SOURCE}:BBB:20261111"]
    assert first[0]["features"] == {"round_trip_cost": 0.002, "z": 3.142} and first[0]["direction"] == -1
    assert record_signals(picks, info, date(2026, 11, 11), ledger) == []            # a rerun adds nothing
