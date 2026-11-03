from datetime import date

import pytest

from tempo.backtest import Costs
from tempo.data import Bars
from tempo.forward import (MIN_POOLED_TRIPS, forward_round_trips, mask_initial_run, pooled_stats, ready_to_judge, verdict)

NO_COSTS = Costs(per_share=0.0, min_per_order=0.0, sell_fee_per_million=0.0, slippage_bps=0.0)


def ibs_bars(pattern, start="2026-01-01"):
    """Daily bars whose IBS follows `pattern` (range 100 to 110, open = previous close)."""
    from datetime import timedelta
    d0 = date.fromisoformat(start)
    dates = [(d0 + timedelta(days=i)).isoformat() for i in range(len(pattern))]
    close = [100.0 + 10.0 * p for p in pattern]
    open_ = [close[0]] + close[:-1]
    return Bars(dates, open_, [110.0] * len(pattern), [100.0] * len(pattern), close)


def test_mask_ignores_a_signal_already_long_at_the_start():
    assert mask_initial_run([1, 1, 0, 1, 1, 0]) == [0, 0, 0, 1, 1, 0]


def test_mask_leaves_a_flat_start_alone():
    assert mask_initial_run([0, 1, 1, 0]) == [0, 1, 1, 0]
    assert mask_initial_run([]) == []


def test_only_trades_after_the_start_date_count():
    # IBS: weak close (0.1) on day 2 -> long; strong (0.9) on day 4 -> flat; again weak on day 8, strong day 10
    bars = ibs_bars([0.5, 0.5, 0.1, 0.5, 0.9, 0.5, 0.5, 0.5, 0.1, 0.5, 0.9, 0.5])
    all_trips = forward_round_trips(bars, "ibs", bars.dates[0], NO_COSTS, 10_000.0).trips
    late = forward_round_trips(bars, "ibs", bars.dates[7], NO_COSTS, 10_000.0).trips
    assert len(all_trips) == 2 and len(late) == 1


def test_a_position_already_open_at_the_start_is_not_entered_until_it_resets():
    bars = ibs_bars([0.5, 0.1, 0.5, 0.5, 0.9, 0.5, 0.1, 0.5, 0.9, 0.5])  # long from day 1 to 4, again from day 6
    result = forward_round_trips(bars, "ibs", bars.dates[2], NO_COSTS, 10_000.0)  # start while the first long is on
    assert len(result.trips) == 1  # only the second round trip


def test_no_data_after_the_start_gives_no_trips_and_no_error():
    bars = ibs_bars([0.5, 0.1, 0.5, 0.9])
    result = forward_round_trips(bars, "ibs", "2030-01-01", NO_COSTS, 10_000.0)
    assert result.trips == [] and result.equity == []


def test_costs_lower_the_trip_returns():
    bars = ibs_bars([0.5, 0.5, 0.1, 0.5, 0.9, 0.5, 0.5, 0.5, 0.1, 0.5, 0.9, 0.5])
    free = forward_round_trips(bars, "ibs", bars.dates[0], NO_COSTS, 10_000.0).trips
    paid = forward_round_trips(bars, "ibs", bars.dates[0], Costs(slippage_bps=30.0), 10_000.0).trips
    assert all(p < f for p, f in zip(paid, free))


def test_pooled_stats():
    n, mean, t = pooled_stats({"a": [0.01, 0.02, 0.03], "b": [0.02, 0.02]})
    assert n == 5 and mean == pytest.approx(0.02) and t > 3
    assert pooled_stats({}) == (0, 0.0, None)
    assert pooled_stats({"a": [0.01]})[2] is None


def test_not_ready_before_60_trips_or_the_deadline():
    assert not ready_to_judge(MIN_POOLED_TRIPS - 1, date(2027, 6, 1))
    assert ready_to_judge(MIN_POOLED_TRIPS, date(2027, 6, 1))
    assert ready_to_judge(3, date(2028, 11, 3))


GOOD = {"SPY ibs": [0.004] * 30, "QQQ ibs": [0.004] * 30, "SPY rsi2": [0.004] * 20, "QQQ rsi2": [0.004] * 20}


def test_verdict_passes_when_the_three_criteria_hold():
    trips = {k: [0.004 + (i % 3) * 0.003 for i in range(len(v))] for k, v in GOOD.items()}
    assert all(ok for _, ok in verdict(trips))


def test_verdict_has_three_criteria_and_each_can_fail():
    base = {k: [0.004 + (i % 3) * 0.003 for i in range(len(v))] for k, v in GOOD.items()}
    assert len(verdict(base)) == 3
    low = {k: [x * 0.1 for x in v] for k, v in base.items()}  # average 0.04%: under the 0.10% bar
    assert not verdict(low)[0][1]
    noisy = {k: [0.02, -0.0195] * (len(v) // 2) for k, v in base.items()}  # average ~0.0025%: not significant either
    assert not verdict(noisy)[1][1]
    one_lucky = {"SPY ibs": [0.02] * 30, "QQQ ibs": [0.0005] * 30, "SPY rsi2": [0.0005] * 20, "QQQ rsi2": [0.0005] * 20}
    assert not verdict(one_lucky)[2][1]
