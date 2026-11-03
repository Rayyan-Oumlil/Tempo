import random

import pytest

from tempo.backtest import Costs, sharpe
from tempo.portfolio import (align, month_end_indices, momentum_scores, pick, run_rotation,
                             same_permutation_shuffle)

NO_COSTS = Costs(per_share=0.0, min_per_order=0.0, sell_fee_per_million=0.0, slippage_bps=0.0)


def make_world(days=800, seed=3):
    """Three assets with different drifts, plus business-day-like dates (21 per 'month')."""
    rng = random.Random(seed)
    dates = [f"{2000 + d // 252}-{(d % 252) // 21 + 1:02d}-{d % 21 + 1:02d}" for d in range(days)]
    closes = {}
    for sym, drift in {"AAA": 0.0008, "BBB": 0.0001, "CCC": -0.0004}.items():
        px, series = 100.0, []
        for _ in range(days):
            px *= 1 + drift + rng.gauss(0, 0.01)
            series.append(px)
        closes[sym] = series
    return dates, closes


def test_month_end_indices_picks_last_day_of_each_month():
    dates = ["2020-01-30", "2020-01-31", "2020-02-03", "2020-02-28", "2020-03-02"]
    assert month_end_indices(dates) == [1, 3]  # the final, unfinished month is not a month end


def test_score_skips_the_latest_month():
    closes = {"A": [float(i + 1) for i in range(300)]}
    t = 299
    assert momentum_scores(closes, t, lookback=252, skip=21)["A"] == pytest.approx(closes["A"][t - 21] / closes["A"][t - 252] - 1)


def test_no_score_without_enough_history():
    assert momentum_scores({"A": [1.0] * 100}, 99, lookback=252, skip=21) == {}


def test_pick_takes_top_n_positive_only():
    assert pick({"A": 0.3, "B": 0.1, "C": 0.2, "D": -0.5}, top_n=2) == ["A", "C"]
    assert pick({"A": -0.1, "B": -0.2}, top_n=3) == []  # all negative -> cash
    assert pick({"A": 0.1}, top_n=3) == ["A"]  # fewer than n positives -> the rest stays cash


def test_pick_is_deterministic_on_ties():
    assert pick({"B": 0.1, "A": 0.1}, top_n=1) == ["A"]


def test_all_cash_when_everything_falls():
    dates = [f"2000-{d // 21 + 1:02d}-{d % 21 + 1:02d}" for d in range(400)]
    closes = {s: [100.0 * 0.999 ** i for i in range(400)] for s in ("A", "B")}
    result = run_rotation(dates, closes, NO_COSTS, lookback=100, skip=21, top_n=1)
    assert result.trades == []
    assert result.equity[-1] == pytest.approx(100_000.0)


def test_orders_fill_the_day_after_the_signal():
    dates, closes = make_world()
    result = run_rotation(dates, closes, NO_COSTS, lookback=252, skip=21, top_n=2)
    signal_days = set(month_end_indices(dates))
    assert result.trades
    assert all(tr.day - 1 in signal_days for tr in result.trades)


def test_no_lookahead_prefix_of_a_longer_run_is_identical():
    """Running on the first k days must give exactly the first k days of the full run."""
    dates, closes = make_world()
    full = run_rotation(dates, closes, Costs(), lookback=252, skip=21, top_n=2)
    for k in (300, 450, 611, 700):
        cut = run_rotation(dates[:k], {s: c[:k] for s, c in closes.items()}, Costs(), lookback=252, skip=21, top_n=2)
        assert cut.equity == pytest.approx(full.equity[:k])


def test_costs_reduce_equity():
    dates, closes = make_world()
    free = run_rotation(dates, closes, NO_COSTS, lookback=252, skip=21, top_n=2)
    paid = run_rotation(dates, closes, Costs(), lookback=252, skip=21, top_n=2)
    assert paid.costs > 0
    assert paid.equity[-1] < free.equity[-1]


def test_never_negative_cash_or_short_and_slots_are_capped():
    dates, closes = make_world()
    result = run_rotation(dates, closes, Costs(), lookback=252, skip=21, top_n=2)
    held: dict[str, int] = {}
    for tr in result.trades:
        held[tr.symbol] = held.get(tr.symbol, 0) + (tr.shares if tr.side == "BUY" else -tr.shares)
        assert held[tr.symbol] >= 0
        assert len([s for s, q in held.items() if q > 0]) <= 2


def test_equal_weight_mode_holds_everything():
    dates, closes = make_world()
    result = run_rotation(dates, closes, NO_COSTS, lookback=252, skip=21, top_n=3, mode="equal_weight")
    assert {tr.symbol for tr in result.trades} == {"AAA", "BBB", "CCC"}


def test_align_keeps_only_common_dates():
    series = {"A": (["2020-01-01", "2020-01-02", "2020-01-03"], [1.0, 2.0, 3.0]),
              "B": (["2020-01-02", "2020-01-03", "2020-01-06"], [5.0, 6.0, 7.0])}
    dates, closes = align(series)
    assert dates == ["2020-01-02", "2020-01-03"]
    assert closes == {"A": [2.0, 3.0], "B": [5.0, 6.0]}


def test_align_refuses_an_empty_overlap():
    with pytest.raises(ValueError):
        align({"A": (["2020-01-01"], [1.0]), "B": (["2021-01-01"], [1.0])})


def test_shuffle_uses_one_permutation_for_all_assets():
    dates, closes = make_world(days=200)
    shuffled = same_permutation_shuffle(closes, random.Random(1))
    for sym in closes:
        orig = sorted(round(b / a, 10) for a, b in zip(closes[sym], closes[sym][1:]))
        new = sorted(round(b / a, 10) for a, b in zip(shuffled[sym], shuffled[sym][1:]))
        assert orig == pytest.approx(new)
    # same permutation: the day-by-day ratio between two assets' returns is preserved as a set of pairs
    pairs = lambda c: sorted((round(c["AAA"][i + 1] / c["AAA"][i], 10), round(c["BBB"][i + 1] / c["BBB"][i], 10)) for i in range(len(c["AAA"]) - 1))
    assert pairs(closes) == pairs(shuffled)
    assert shuffled["AAA"] != closes["AAA"]


def test_sharpe_of_result_is_finite():
    dates, closes = make_world()
    assert abs(sharpe(run_rotation(dates, closes, Costs(), lookback=252, skip=21, top_n=2).equity)) < 10
