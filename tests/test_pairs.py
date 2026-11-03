import math
import random

import pytest

from tempo.backtest import Costs
from tempo.pairs import PairParams, pair_signals, run_pair, zscores

NO_COSTS = Costs(per_share=0.0, min_per_order=0.0, sell_fee_per_million=0.0, slippage_bps=0.0)
P = PairParams(window=20, enter=2.0, exit_z=0.5, stop_z=4.0, max_hold=30)


def spread_to_prices(spread, base=100.0):
    """B flat at `base`; A = base * exp(spread), so log(A) - log(B) is exactly `spread`."""
    return [base * math.exp(s) for s in spread], [base] * len(spread)


def ou_spread(n=1500, seed=5, theta=0.15, sigma=0.01):
    rng, x, out = random.Random(seed), 0.0, []
    for _ in range(n):
        x += -theta * x + rng.gauss(0, sigma)
        out.append(x)
    return out


def test_zscore_needs_a_full_window():
    z = zscores([0.0] * 5 + [1.0], window=10)
    assert z == [None] * 6


def test_zscore_matches_the_definition():
    spread = [0.0, 1.0, 0.0, 1.0, 5.0]
    z = zscores(spread, window=5)[-1]
    mean = sum(spread) / 5
    std = math.sqrt(sum((s - mean) ** 2 for s in spread) / 5)
    assert z == pytest.approx((5.0 - mean) / std)


def test_zscore_of_a_flat_window_is_none_not_a_division_by_zero():
    assert zscores([0.3] * 30, window=10)[-1] is None


def test_zscore_uses_only_data_through_day_t():
    base = [math.sin(i / 3) for i in range(80)]
    changed = base[:50] + [99.0] * 30
    assert zscores(base, 20)[:50] == zscores(changed, 20)[:50]


def test_flat_when_nothing_stretches():
    a, b = spread_to_prices([0.0] * 100)
    assert set(pair_signals(a, b, P)) == {0}


def test_shorts_the_spread_when_it_stretches_up_then_exits_on_reversion():
    spread = [0.0, 0.001] * 15 + [0.2] * 3 + [0.0] * 20
    a, b = spread_to_prices(spread)
    sig = pair_signals(a, b, P)
    assert -1 in sig and 1 not in sig
    first = sig.index(-1)
    assert first >= 30  # not before the spread jumped
    assert sig[-1] == 0  # back to flat after reverting


def test_longs_the_spread_when_it_stretches_down():
    spread = [0.0, 0.001] * 15 + [-0.2] * 3 + [0.0] * 20
    sig = pair_signals(*spread_to_prices(spread), P)
    assert 1 in sig and -1 not in sig


def test_stop_exits_a_runaway_spread():
    spread = [0.0, 0.001] * 15 + [0.05, 0.1, 0.2, 0.4, 0.8, 1.6] + [3.0] * 20
    sig = pair_signals(*spread_to_prices(spread), P)
    assert sig[-1] == 0  # stopped out, not stuck in


def test_time_stop_exits_a_trade_that_never_reverts():
    # a persistently stretched but not exploding spread: z stays between 0.5 and 4 only while the window is moving;
    # use a slow ramp so |z| stays above the exit level for a long time
    spread = [0.0, 0.001] * 15 + [0.02 * i for i in range(1, 80)]
    sig = pair_signals(*spread_to_prices(spread), PairParams(window=20, enter=2.0, exit_z=0.01, stop_z=50.0, max_hold=10))
    runs, cur = [], 0
    for s in sig:
        cur = cur + 1 if s else 0
        runs.append(cur)
    assert max(runs) <= 10


def test_signals_use_only_closes_through_day_t():
    spread = ou_spread()
    a, b = spread_to_prices(spread)
    full = pair_signals(a, b, P)
    for k in (200, 600, 1100):
        assert pair_signals(a[:k], b[:k], P) == full[:k]


def test_orders_fill_the_day_after_the_signal():
    spread = ou_spread()
    a, b = spread_to_prices(spread)
    sig = pair_signals(a, b, P)
    result = run_pair(a, b, sig, NO_COSTS, capital=100_000.0, borrow_rate=0.0)
    assert result.trades
    first_signal_day = next(i for i, s in enumerate(sig) if s)
    assert min(tr.day for tr in result.trades) == first_signal_day + 1


def test_legs_are_dollar_neutral_after_entry():
    a, b = [100.0] * 5, [37.0] * 5
    sig = [0, 1, 1, 1, 1]
    result = run_pair(a, b, sig, NO_COSTS, capital=100_000.0, borrow_rate=0.0)
    by = {tr.leg: tr for tr in result.trades if tr.day == 2}
    long_value, short_value = by["A"].shares * 100.0, by["B"].shares * 37.0
    assert by["A"].side == "BUY" and by["B"].side == "SELL"
    assert abs(long_value - short_value) / 100_000.0 < 0.01


def test_constant_prices_lose_only_costs():
    a, b = [100.0] * 10, [50.0] * 10
    sig = [0, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    free = run_pair(a, b, sig, NO_COSTS, capital=100_000.0, borrow_rate=0.0)
    assert free.equity[-1] == pytest.approx(100_000.0)
    paid = run_pair(a, b, sig, Costs(), capital=100_000.0, borrow_rate=0.0)
    assert paid.costs > 0 and paid.equity[-1] == pytest.approx(100_000.0 - paid.costs)


def test_borrow_cost_reduces_equity_and_scales_with_the_rate():
    a, b = [100.0] * 60, [50.0] * 60
    sig = [0] + [1] * 58 + [0]
    zero = run_pair(a, b, sig, NO_COSTS, capital=100_000.0, borrow_rate=0.0).equity[-1]
    low = run_pair(a, b, sig, NO_COSTS, capital=100_000.0, borrow_rate=0.003).equity[-1]
    high = run_pair(a, b, sig, NO_COSTS, capital=100_000.0, borrow_rate=0.015).equity[-1]
    assert zero > low > high
    assert (zero - high) == pytest.approx(5 * (zero - low), rel=0.01)


def test_a_mean_reverting_spread_makes_money_without_costs():
    spread = ou_spread(n=3000, seed=9)
    a, b = spread_to_prices(spread)
    result = run_pair(a, b, pair_signals(a, b, P), NO_COSTS, capital=100_000.0, borrow_rate=0.0)
    assert result.equity[-1] > 100_000.0


def test_prefix_of_a_longer_run_is_identical():
    spread = ou_spread()
    a, b = spread_to_prices(spread)
    full = run_pair(a, b, pair_signals(a, b, P), Costs(), capital=100_000.0, borrow_rate=0.003)
    for k in (300, 700, 1200):
        cut = run_pair(a[:k], b[:k], pair_signals(a[:k], b[:k], P), Costs(), capital=100_000.0, borrow_rate=0.003)
        assert cut.equity == pytest.approx(full.equity[:k])


def test_signal_length_must_match():
    with pytest.raises(ValueError):
        run_pair([1.0] * 5, [1.0] * 5, [0] * 4, NO_COSTS, capital=1000.0, borrow_rate=0.0)
