import math

import pytest

from tempo.backtest import (Costs, backtest, buy_and_hold, flat, max_drawdown, negative_control, order_cost,
                            sharpe, sma_trend)

COSTS = Costs(per_share=0.005, min_per_order=1.0, sell_fee_per_million=20.6, slippage_bps=0.0)


def test_order_cost_matches_the_commissions_measured_on_the_paper_account():
    assert order_cost(1, 760.0, "BUY", COSTS) == pytest.approx(1.0)      # minimum
    assert order_cost(300, 760.36, "BUY", COSTS) == pytest.approx(1.5)   # 300 * 0.005
    sell = order_cost(300, 760.37, "SELL", COSTS)
    assert sell == pytest.approx(1.5 + 300 * 760.37 * 20.6 / 1e6)        # plus the sell-side fee, about 4.70


def test_slippage_is_charged_on_notional():
    costs = Costs(0.005, 1.0, 0.0, slippage_bps=2.0)
    assert order_cost(100, 100.0, "BUY", costs) == pytest.approx(1.0 + 10_000 * 2.0 / 1e4)


def test_flat_strategy_never_trades_and_keeps_its_cash():
    closes = [100.0, 101.0, 99.0, 105.0]
    r = backtest(closes, flat(closes), COSTS)
    assert r.trades == [] and r.equity == [100_000.0] * 4


def test_buy_and_hold_buys_once_a_day_late_and_pays_costs():
    closes = [100.0, 100.0, 110.0, 121.0]
    r = backtest(closes, buy_and_hold(closes), COSTS)
    assert [(t.day, t.side) for t in r.trades] == [(1, "BUY")]   # signal on day 0, filled at day 1's close
    assert r.equity[-1] / r.equity[0] == pytest.approx(1.21, rel=1e-3)
    assert r.costs == pytest.approx(5.0, abs=0.01)  # 999 shares * 0.005 (1000 would not fit with costs)


def test_a_signal_is_executed_at_the_next_close_not_the_same_close():
    closes = [10.0, 10.0, 10.0, 20.0, 20.0]
    signals = [0, 0, 1, 1, 1]   # decided on day 2's data
    r = backtest(closes, signals, COSTS)
    assert r.trades[0].day == 3 and r.trades[0].price == 20.0   # bought AFTER the jump: no free ride


def test_sma_trend_uses_no_future_data():
    closes = [100 + math.sin(i / 3) * 10 + i * 0.1 for i in range(120)]
    full = sma_trend(20)(closes)
    for cut in (30, 60, 90):
        assert sma_trend(20)(closes[:cut]) == full[:cut]


def test_sma_trend_is_flat_until_it_has_enough_history():
    assert sma_trend(5)([1, 2, 3, 4])[:4] == [0, 0, 0, 0]


def test_max_drawdown_and_sharpe():
    assert max_drawdown([100, 120, 90, 130]) == pytest.approx(-0.25)
    assert sharpe([100.0, 100.0, 100.0]) == 0.0
    assert sharpe([100.0, 101.0, 102.01, 103.03]) > 0


def test_negative_control_is_deterministic_and_reports_where_the_real_result_ranks():
    closes = [100 + math.sin(i / 5) * 5 + i * 0.05 for i in range(300)]
    a = negative_control(closes, sma_trend(20), COSTS, n=30, seed=7)
    b = negative_control(closes, sma_trend(20), COSTS, n=30, seed=7)
    assert a == b
    assert 0.0 <= a["beat_pct"] <= 100.0 and a["n"] == 30
