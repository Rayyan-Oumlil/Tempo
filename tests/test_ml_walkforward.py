import numpy as np
import pandas as pd

from tempo import ml_walkforward as mw
from tempo.history_core import Verdict


def test_per_side_bounds():
    assert mw.per_side(50) == 10          # floor
    assert mw.per_side(300) == 30         # 10%
    assert mw.per_side(5000) == 50        # cap


def test_train_cutoff_is_ten_sessions_before_the_test_year():
    sessions = [f"2021-12-{d:02d}" for d in range(1, 32)] + ["2022-01-03"]
    cut = mw.train_cutoff(sessions, 2022)
    assert cut == sessions[len(sessions) - 1 - mw.PURGE_SESSIONS]
    assert cut < "2022-01-03"


def _day(n: int) -> pd.DataFrame:
    return pd.DataFrame({"symbol": [f"S{i:03d}" for i in range(n)], "gross": np.linspace(-0.1, 0.1, n)})


def test_pick_books_takes_highest_and_lowest_scores():
    day = _day(200)
    score = np.arange(200, dtype=float)             # S199 has the best score
    top, bottom = mw.pick_books(day, score)
    assert len(top) == len(bottom) == 20
    assert top[0][0] == "S199" and bottom[-1][0] == "S000"
    assert {s for s, _ in top}.isdisjoint({s for s, _ in bottom})


def test_pick_books_is_deterministic_on_ties():
    day = _day(100)
    assert mw.pick_books(day, np.zeros(100)) == mw.pick_books(day, np.zeros(100))


def test_books_from_scores_signs_the_short_leg():
    day = _day(100)
    day["date"], day["entry"], day["y"] = "2022-01-03", "2022-01-04", 0.0
    score = np.arange(100, dtype=float)
    books = mw.books_from_scores(day, score)
    assert len(books["long_only"]) == 10 and len(books["long_short"]) == 20
    shorts = [t for t in books["long_short"] if t.symbol in {f"S{i:03d}" for i in range(10)}]
    assert all(t.gross > 0 for t in shorts)          # shorting the stocks with the lowest gross return: positive
    assert all(t.day == "2022-01-04" for t in books["long_short"])


def test_bh_flags_one_sided():
    neg = Verdict(1000, 200, -0.003, (-0.005, -0.001), -3.5, {}, -0.004, "KILL", ())
    pos = Verdict(1000, 200, 0.01, (0.005, 0.015), 5.0, {}, 0.009, "FORWARD", ())
    flags = mw.bh_flags({"neg": neg, "pos": pos})
    assert flags == {"neg": False, "pos": True}


def test_ic_summary_needs_enough_days():
    assert mw.ic_summary([0.1] * 10)[1] is None
