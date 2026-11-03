import random

import pytest

from tempo.backtest import Costs
from tempo.data import Bars
from tempo.meanrev import (days_invested, ibs, ibs_signals, rsi, rsi2_signals, run_longflat, shuffle_bars, sma)

NO_COSTS = Costs(per_share=0.0, min_per_order=0.0, sell_fee_per_million=0.0, slippage_bps=0.0)


def test_sma():
    assert sma([1, 2, 3, 4, 5], 3) == [None, None, 2.0, 3.0, 4.0]


def test_rsi_period_2_matches_a_hand_calculation():
    # changes +1, -1, +1, +1. Seed: avg gain (1+0)/2 = 0.5, avg loss (0+1)/2 = 0.5 -> RS 1 -> 50.
    # Wilder: gain (0.5+1)/2 = 0.75, loss 0.25 -> RS 3 -> 75; then gain 0.875, loss 0.125 -> RS 7 -> 87.5
    assert rsi([10, 11, 10, 11, 12], 2) == [None, None, pytest.approx(50.0), pytest.approx(75.0), pytest.approx(87.5)]


def test_rsi_is_100_with_only_gains_and_undefined_on_a_flat_series():
    assert rsi([1, 2, 3, 4], 2)[-1] == 100.0
    assert rsi([5, 5, 5, 5], 2) == [None] * 4


def test_ibs_and_its_undefined_case():
    assert ibs([12.0, 10.0], [8.0, 10.0], [9.0, 10.0]) == [pytest.approx(0.25), None]


def uptrend_with_a_dip(n=320, dip_at=260):
    closes = [100 * 1.001 ** i for i in range(n)]
    for i in range(dip_at, n):
        closes[i] *= 0.95 if i < dip_at + 2 else 1.0  # two sharp down days, then back to trend (a bounce)
    for i in range(dip_at + 2, n):
        closes[i] = closes[i - 1] * 1.004
    return closes


def test_rsi2_enters_a_dip_in_an_uptrend_and_exits_on_the_bounce():
    sig = rsi2_signals(uptrend_with_a_dip())
    assert sum(sig[:200]) == 0  # needs the 200-day average first
    first = sig.index(1)
    assert 258 <= first <= 264
    assert sig[-1] == 0 and sum(sig) < 12  # out again after the bounce


def test_rsi2_never_buys_below_the_200_day_average():
    closes = [200 * 0.999 ** i for i in range(400)]  # steady decline: always below its SMA(200)
    for i in range(300, 303):
        closes[i] *= 0.9
    assert sum(rsi2_signals(closes)) == 0


def test_ibs_signals_buy_weak_closes_and_sell_strong_ones():
    highs = [10, 10, 10, 10, 10, 10]
    lows = [0, 0, 0, 0, 0, 0]
    closes = [5, 1, 5, 9, 5, 5]  # IBS .5, .1, .5, .9, ...
    assert ibs_signals(highs, lows, closes) == [0, 1, 1, 0, 0, 0]


def test_signals_use_only_data_through_day_t():
    rng = random.Random(4)
    closes = [100.0]
    for _ in range(499):
        closes.append(closes[-1] * (1 + rng.gauss(0.0003, 0.012)))
    highs = [c * (1 + abs(rng.gauss(0, 0.004))) for c in closes]
    lows = [c * (1 - abs(rng.gauss(0, 0.004))) for c in closes]
    for k in (260, 350, 450):
        assert rsi2_signals(closes[:k]) == rsi2_signals(closes)[:k]
        assert ibs_signals(highs[:k], lows[:k], closes[:k]) == ibs_signals(highs, lows, closes)[:k]


OPENS = [10.0, 10.0, 11.0, 12.0, 13.0, 14.0]
CLOSES = [10.0, 10.5, 11.5, 12.5, 13.5, 14.5]


def test_next_open_fills_the_morning_after_the_signal():
    result = run_longflat(OPENS, CLOSES, [0, 1, 1, 0, 0, 0], NO_COSTS, capital=1000.0)
    assert [(t.day, t.side, t.price) for t in result.trades] == [(2, "BUY", 11.0), (4, "SELL", 13.0)]


def test_same_close_fill_is_the_optimistic_reference():
    result = run_longflat(OPENS, CLOSES, [0, 1, 1, 0, 0, 0], NO_COSTS, capital=1000.0, fill="same_close")
    assert [(t.day, t.side, t.price) for t in result.trades] == [(1, "BUY", 10.5), (3, "SELL", 12.5)]


def test_a_signal_on_the_last_day_cannot_be_filled_at_the_next_open():
    result = run_longflat(OPENS, CLOSES, [0, 0, 0, 0, 0, 1], NO_COSTS, capital=1000.0)
    assert result.trades == []


def test_unknown_fill_rule_is_refused():
    with pytest.raises(ValueError):
        run_longflat(OPENS, CLOSES, [0] * 6, NO_COSTS, capital=1000.0, fill="whenever")


def test_flat_prices_lose_only_costs():
    opens = closes = [100.0] * 10
    sig = [0, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    assert run_longflat(opens, closes, sig, NO_COSTS, capital=10_000.0).equity[-1] == pytest.approx(10_000.0)
    paid = run_longflat(opens, closes, sig, Costs(), capital=10_000.0)
    assert paid.costs > 0 and paid.equity[-1] == pytest.approx(10_000.0 - paid.costs)


def test_a_run_on_the_first_k_days_equals_the_start_of_the_longer_run():
    rng = random.Random(8)
    opens, closes, px = [], [], 100.0
    for _ in range(400):
        px *= 1 + rng.gauss(0.0003, 0.01)
        opens.append(px)
        px *= 1 + rng.gauss(0.0003, 0.01)
        closes.append(px)
    sig = rsi2_signals(closes)
    full = run_longflat(opens, closes, sig, Costs(), capital=100_000.0)
    for k in (250, 300, 399):
        cut = run_longflat(opens[:k], closes[:k], rsi2_signals(closes[:k]), Costs(), capital=100_000.0)
        assert cut.equity == pytest.approx(full.equity[:k])


def test_days_invested_counts_nights_held_and_a_position_still_open_at_the_end():
    result = run_longflat(OPENS, CLOSES, [0, 1, 1, 0, 0, 0], NO_COSTS, capital=1000.0)
    assert days_invested(result.trades, 6) == 2  # bought at day 2's open, sold at day 4's open: held through closes 2 and 3
    held = run_longflat(OPENS, CLOSES, [0, 1, 1, 1, 1, 1], NO_COSTS, capital=1000.0)
    assert days_invested(held.trades, 6) == 4  # bought day 2, never sold


def test_shuffle_bars_keeps_each_days_shape_and_stays_valid():
    rng = random.Random(1)
    px, o, h, lo, c, d = 100.0, [], [], [], [], []
    for i in range(300):
        op = px * (1 + rng.gauss(0, 0.004))
        cl = op * (1 + rng.gauss(0, 0.01))
        o.append(op), c.append(cl), h.append(max(op, cl) * 1.002), lo.append(min(op, cl) * 0.998), d.append(f"d{i:04d}")
        px = cl
    bars = Bars(d, o, h, lo, c)
    fake = shuffle_bars(bars, random.Random(2))

    def shapes(b):
        out = []
        for t in range(1, len(b.close)):
            out.append(tuple(round(x, 9) for x in (b.open[t] / b.close[t - 1], b.high[t] / b.open[t], b.low[t] / b.open[t], b.close[t] / b.open[t])))
        return sorted(out)

    assert len(fake.close) == len(bars.close) and fake.dates == bars.dates
    assert fake.close != bars.close
    assert all(hi >= max(op, cl) - 1e-9 and l <= min(op, cl) + 1e-9 for op, hi, l, cl in zip(fake.open, fake.high, fake.low, fake.close))
    # bar 0 is kept as the starting point; every later day's shape is the same set of shapes, reordered
    flat = lambda shapes_: [x for tup in shapes_ for x in tup]
    assert flat(shapes(fake)) == pytest.approx(flat(shapes(bars)), abs=1e-7)
    assert [shapes(fake)[i] for i in range(3)] != []  # sanity: shapes exist
    same_order = sum(1 for t in range(1, 300) if abs(fake.close[t] / fake.close[t - 1] - bars.close[t] / bars.close[t - 1]) < 1e-12)
    assert same_order < 30  # a real permutation moves almost every day


def test_rsi2_holds_until_the_first_close_above_the_5_day_average():
    closes = uptrend_with_a_dip()
    sig = rsi2_signals(closes)
    fast = sma(closes, 5)
    entry = sig.index(1)
    first_bounce = next(t for t in range(entry + 1, len(closes)) if closes[t] > fast[t])
    assert all(sig[t] == 1 for t in range(entry, first_bounce))  # stays long while the close is at or below the 5-day average
    assert sig[first_bounce] == 0                                # and leaves on the first close above it
