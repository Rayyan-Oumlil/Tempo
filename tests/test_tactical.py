import random

import pytest

from tempo.backtest import Costs
from tempo.portfolio import month_end_indices, run_weighted
from tempo.tactical import fixed_weight_fn, trend_weight_fn

NO_COSTS = Costs(per_share=0.0, min_per_order=0.0, sell_fee_per_million=0.0, slippage_bps=0.0)


def calendar(days=900):
    """21 'trading days' per month, so month ends are every 21st day."""
    return [f"{2000 + d // 252}-{(d % 252) // 21 + 1:02d}-{d % 21 + 1:02d}" for d in range(days)]


def prices(days=900, seed=1, drift=0.0004, vol=0.008, start=100.0):
    rng, px, out = random.Random(seed), start, []
    for _ in range(days):
        px *= 1 + drift + rng.gauss(0, vol)
        out.append(px)
    return out


def test_fully_invested_in_one_asset_follows_that_asset_after_the_first_fill():
    dates = calendar()
    closes = {"A": prices(), "B": prices(seed=2)}
    result = run_weighted(dates, closes, NO_COSTS, fixed_weight_fn({"A": 1.0}), capital=1_000_000.0)
    first_fill = min(tr.day for tr in result.trades)
    assert first_fill == month_end_indices(dates)[0] + 1
    for t in range(first_fill + 5, 800, 60):
        assert result.equity[t] / result.equity[first_fill] == pytest.approx(closes["A"][t] / closes["A"][first_fill], rel=3e-3)


def test_half_invested_keeps_half_in_cash():
    dates = calendar()
    closes = {"A": [100.0 * 1.001 ** i for i in range(900)]}
    result = run_weighted(dates, closes, NO_COSTS, fixed_weight_fn({"A": 0.5}), capital=1_000_000.0)
    first_fill = min(tr.day for tr in result.trades)
    t = 600
    growth = result.equity[t] / result.equity[first_fill]
    full_growth = closes["A"][t] / closes["A"][first_fill]
    # a constant 50% weight rebalanced monthly compounds a little slower than half of the asset's total gain
    assert 1.0 + 0.3 * (full_growth - 1) < growth < 1.0 + 0.5 * (full_growth - 1)


def test_orders_are_filled_the_trading_day_after_a_month_end():
    dates = calendar()
    closes = {"A": prices(), "B": prices(seed=2)}
    result = run_weighted(dates, closes, Costs(), fixed_weight_fn({"A": 0.5, "B": 0.5}), capital=100_000.0)
    signal_days = set(month_end_indices(dates))
    assert result.trades and all(tr.day - 1 in signal_days for tr in result.trades)


def test_no_weights_means_no_trades():
    dates = calendar()
    result = run_weighted(dates, {"A": prices()}, Costs(), lambda t: None, capital=100_000.0)
    assert result.trades == [] and result.equity[-1] == pytest.approx(100_000.0)


def test_weights_over_100_percent_or_negative_are_refused():
    dates = calendar()
    with pytest.raises(ValueError):
        run_weighted(dates, {"A": prices(), "B": prices(seed=2)}, Costs(), fixed_weight_fn({"A": 0.7, "B": 0.5}), capital=1000.0)
    with pytest.raises(ValueError):
        run_weighted(dates, {"A": prices()}, Costs(), fixed_weight_fn({"A": -0.1}), capital=1000.0)


def test_costs_reduce_equity_and_shares_stay_whole():
    dates = calendar()
    closes = {"A": prices(), "B": prices(seed=2)}
    free = run_weighted(dates, closes, NO_COSTS, fixed_weight_fn({"A": 0.5, "B": 0.5}), capital=100_000.0)
    paid = run_weighted(dates, closes, Costs(slippage_bps=5.0), fixed_weight_fn({"A": 0.5, "B": 0.5}), capital=100_000.0)
    assert paid.costs > 0 and paid.equity[-1] < free.equity[-1]
    assert all(tr.shares == int(tr.shares) and tr.shares > 0 for tr in paid.trades)
    assert min(paid.equity) > 0


def test_trend_rule_holds_a_rising_asset_and_sheds_a_falling_one():
    dates = calendar()
    closes = {"UP": [100.0 * 1.002 ** i for i in range(900)], "DOWN": [100.0 * 0.998 ** i for i in range(900)]}
    fn = trend_weight_fn(closes, dates, months=10, weight_each=0.2)
    month_ends = month_end_indices(dates)
    late = month_ends[-3]
    assert fn(late) == {"UP": 0.2}


def test_trend_rule_gives_no_signal_before_ten_month_ends_exist():
    dates = calendar()
    closes = {"A": prices()}
    fn = trend_weight_fn(closes, dates, months=10, weight_each=0.2)
    month_ends = month_end_indices(dates)
    assert fn(month_ends[8]) is None  # only 9 month ends so far
    assert fn(month_ends[9]) is not None


def test_trend_rule_uses_the_average_including_the_current_month_end():
    dates = calendar()
    month_ends = month_end_indices(dates)
    closes = {"A": [100.0] * 900}
    t = month_ends[12]
    closes["A"][t] = 100.0 + 1.0  # one dollar above a flat history: above the average
    fn = trend_weight_fn(closes, dates, months=10, weight_each=0.2)
    assert fn(t) == {"A": 0.2}
    closes["A"][t] = 100.0  # equal to the average: not above
    assert fn(t) == {}


def test_a_run_on_the_first_k_days_matches_the_longer_run():
    dates = calendar()
    closes = {"A": prices(), "B": prices(seed=2, drift=0.0001), "C": prices(seed=3, drift=-0.0002)}
    full = run_weighted(dates, closes, Costs(), trend_weight_fn(closes, dates, 10, 0.2), capital=100_000.0)
    for k in (400, 555, 700):
        c = {s: v[:k] for s, v in closes.items()}
        cut = run_weighted(dates[:k], c, Costs(), trend_weight_fn(c, dates[:k], 10, 0.2), capital=100_000.0)
        assert cut.equity == pytest.approx(full.equity[:k])


def test_every_order_pays_costs_including_sells():
    dates = calendar()
    closes = {"A": prices(), "B": prices(seed=2)}
    result = run_weighted(dates, closes, Costs(), fixed_weight_fn({"A": 0.5, "B": 0.5}), capital=100_000.0)
    sells = [tr for tr in result.trades if tr.side == "SELL"]
    assert sells and all(tr.cost > 0 for tr in result.trades)
