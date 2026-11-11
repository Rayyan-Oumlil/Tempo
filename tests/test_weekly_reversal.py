from datetime import date

import pytest

from tempo.daybars import DayBars
from tempo.weekly_reversal import SOURCE, is_week_end, pick, r5


def test_week_end_is_the_last_trading_day_of_the_calendar_week():
    assert is_week_end(date(2026, 11, 13)) is True        # Friday
    assert is_week_end(date(2026, 11, 12)) is False
    assert is_week_end(date(2026, 11, 25)) is False       # Wednesday before Thanksgiving: Friday 27 still trades
    assert is_week_end(date(2026, 11, 27)) is True
    assert is_week_end(date(2026, 12, 24)) is True        # Christmas on Friday 25: Thursday 24 ends the week
    assert is_week_end(date(2026, 11, 14)) is False       # Saturday


def bars(closes):
    return DayBars([f"2026-10-{d:02d}" for d in range(1, len(closes) + 1)], list(closes), [1_000_000.0] * len(closes))


def test_r5_is_the_five_session_return_minus_spy():
    stock = bars([10.0] * 25 + [9.0])                      # down 10% over the last 5 sessions
    spy = bars([100.0] * 25 + [101.0])                     # SPY up 1%
    assert r5(stock, spy, stock.dates[-1]) == pytest.approx(-0.11)
    assert r5(bars([10.0] * 3), spy, "2026-10-03") is None  # not enough history
    assert r5(stock, bars([100.0] * 20), stock.dates[-1]) is None   # SPY lacks the day


def test_pick_takes_the_10_worst_long_and_the_10_best_short_with_ties_by_symbol():
    moves = {f"S{i:02d}": (i - 20) / 100 for i in range(41)}          # 41 symbols from -20% to +20%
    longs, shorts = pick(moves, n=10)
    assert longs == [f"S{i:02d}" for i in range(10)]
    assert shorts == [f"S{i:02d}" for i in range(40, 30, -1)]
    tie = {"B": -0.1, "A": -0.1, **{f"Z{i:02d}": 0.0 for i in range(40)}}
    assert pick(tie, n=1)[0] == ["A"]


def test_pick_refuses_a_thin_universe():
    assert pick({f"S{i}": 0.0 for i in range(39)}, n=10) == ([], [])


def test_source_name_matches_the_registration():
    import json
    from pathlib import Path
    spec = json.loads((Path(__file__).parents[1] / "evidence" / "weekly_reversal_forward.json").read_text(encoding="utf-8"))
    assert spec["source_name"] == SOURCE
