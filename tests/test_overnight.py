import random

import pytest

from tempo.backtest import Costs, cagr
from tempo.data import Bars, drop_incomplete_today_bars
from tempo.overnight import break_even_slippage, run_overnight, t_statistic

NO_COSTS = Costs(per_share=0.0, min_per_order=0.0, sell_fee_per_million=0.0, slippage_bps=0.0)


def world(n=600, seed=2, overnight=0.0004, intraday=0.0, vol=0.004):
    """Prices where each night drifts by `overnight` and each day by `intraday`, plus noise."""
    rng = random.Random(seed)
    opens, closes, px = [], [], 100.0
    for _ in range(n):
        px *= 1 + overnight + rng.gauss(0, vol)
        opens.append(px)
        px *= 1 + intraday + rng.gauss(0, vol)
        closes.append(px)
    return opens, closes


def test_zero_costs_equity_follows_the_overnight_returns():
    opens, closes = world()
    result = run_overnight(opens, closes, NO_COSTS, capital=1_000_000.0)
    expected = 1_000_000.0
    for t in range(1, len(closes)):
        expected *= opens[t] / closes[t - 1]
        assert result.equity[t] == pytest.approx(expected, rel=2e-4)


def test_orders_are_buy_at_the_close_then_sell_at_the_next_open():
    opens, closes = world(n=10)
    result = run_overnight(opens, closes, NO_COSTS, capital=100_000.0)
    sells = [t for t in result.trades if t.side == "SELL"]
    buys = [t for t in result.trades if t.side == "BUY"]
    assert [b.day for b in buys] == list(range(0, 9))  # every close except the last, which has no next open
    assert [s.day for s in sells] == list(range(1, 10))
    assert all(b.price == closes[b.day] for b in buys) and all(s.price == opens[s.day] for s in sells)
    assert all(s.shares == buys[i].shares for i, s in enumerate(sells))


def test_nothing_is_held_after_the_last_day():
    opens, closes = world(n=20)
    result = run_overnight(opens, closes, NO_COSTS, capital=100_000.0)
    assert result.trades[-1].side == "SELL"


def test_the_intraday_leg_earns_nothing():
    opens, closes = world(overnight=0.0, intraday=0.01, vol=0.0)  # +1% every day, flat every night
    result = run_overnight(opens, closes, NO_COSTS, capital=100_000.0)
    # nights are flat after the day's +1%? price rises intraday, then opens at that close: night return is 0
    assert result.equity[-1] == pytest.approx(100_000.0, rel=1e-3)


def test_costs_and_slippage_reduce_equity_monotonically():
    opens, closes = world()
    ends = [run_overnight(opens, closes, Costs(slippage_bps=s), capital=100_000.0).equity[-1] for s in (0, 1, 3, 10)]
    assert ends == sorted(ends, reverse=True) and ends[0] > ends[-1]


def test_cash_never_goes_negative_and_shares_are_whole():
    opens, closes = world()
    result = run_overnight(opens, closes, Costs(), capital=5_000.0)
    assert all(t.shares == int(t.shares) and t.shares > 0 for t in result.trades)
    assert min(result.equity) > 0


def test_a_run_on_the_first_k_days_matches_the_longer_run_except_the_last_day():
    opens, closes = world()
    full = run_overnight(opens, closes, Costs(), capital=100_000.0)
    for k in (100, 333, 500):
        cut = run_overnight(opens[:k], closes[:k], Costs(), capital=100_000.0)
        assert cut.equity[:k - 1] == pytest.approx(full.equity[:k - 1])


def test_break_even_slippage_matches_the_drift():
    opens, closes = world(n=2000, overnight=0.0005, intraday=0.0, vol=0.0)  # 5 bps a night, no noise, no commission
    be = break_even_slippage(opens, closes, NO_COSTS, capital=100_000.0)
    assert be == pytest.approx(2.5, abs=0.15)  # two orders a night, so about half the nightly drift per side


def test_break_even_is_zero_when_the_idea_already_loses_before_slippage():
    opens, closes = world(n=800, overnight=-0.0005, vol=0.0)
    assert break_even_slippage(opens, closes, NO_COSTS, capital=100_000.0) == 0.0


def test_break_even_is_monotone_with_the_edge():
    small = break_even_slippage(*world(n=1500, overnight=0.0002, vol=0.0), NO_COSTS, capital=100_000.0)
    big = break_even_slippage(*world(n=1500, overnight=0.0006, vol=0.0), NO_COSTS, capital=100_000.0)
    assert 0 < small < big


def test_t_statistic_of_a_constant_positive_return_is_huge_and_of_noise_is_small():
    assert t_statistic([0.001, 0.0011, 0.0009] * 100) > 50
    rng = random.Random(0)
    assert abs(t_statistic([rng.gauss(0, 0.01) for _ in range(5000)])) < 3


def test_t_statistic_needs_two_points():
    with pytest.raises(ValueError):
        t_statistic([0.01])


def test_drops_a_bar_dated_today():
    from datetime import date
    bars = Bars(["2026-11-02", "2026-11-03"], [1.0, 2.0], [1.0, 2.0], [1.0, 2.0], [1.0, 2.0])
    cut = drop_incomplete_today_bars(bars, today=date(2026, 11, 3))
    assert cut.dates == ["2026-11-02"] and cut.open == [1.0] and cut.close == [1.0]
    assert drop_incomplete_today_bars(cut, today=date(2026, 11, 3)) == cut


def test_cagr_helper_is_used_consistently():
    opens, closes = world()
    assert cagr(run_overnight(opens, closes, NO_COSTS, capital=100_000.0).equity) > 0
