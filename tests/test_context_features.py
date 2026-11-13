import statistics

import pytest

from tempo.daybars import DayBars, vol20
from tempo.snapshots import Borrow, context_features


def bars(closes):
    return DayBars([f"d{n}" for n in range(len(closes))], closes, [1.0] * len(closes))


def test_vol20_is_the_stdev_of_the_20_returns_before_the_event_day():
    closes = [100.0 + (3 if n % 2 else -2) + n for n in range(30)]
    i = 25
    rets = [closes[n] / closes[n - 1] - 1 for n in range(i - 20, i)]
    assert vol20(bars(closes), i) == pytest.approx(statistics.stdev(rets))


def test_the_event_day_move_never_enters_vol20():
    base = [100.0 + n * 0.1 for n in range(30)]
    shocked = base[:25] + [base[25] * 1.5] + base[26:]
    assert vol20(bars(base), 25) == vol20(bars(shocked), 25)


def test_vol20_needs_21_closes_before_and_including_the_window():
    assert vol20(bars([100.0] * 30), 20) is None and vol20(bars([100.0] * 30), 21) == 0.0


def test_context_features_carry_vol_and_borrow_and_record_a_missing_vol_as_none():
    table = {"AAA": Borrow(rebate=1.0, fee=2.5, available=1000, capped=False)}
    out = context_features({"vol20": 0.0123456789}, table, "AAA")
    assert out["vol20"] == 0.01235 and out["borrow_known"] is True and out["borrow_fee"] == 2.5
    none = context_features({"vol20": None}, None, "ZZZ")
    assert none == {"vol20": None, "borrow_known": False}
    assert context_features({}, None, "ZZZ")["vol20"] is None
