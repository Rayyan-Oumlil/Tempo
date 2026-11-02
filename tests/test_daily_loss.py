import math

import pytest
from fakes import OPEN_NOW, SPY, FakeIB
from ib_async import MarketOrder

from tempo.account import daily_loss_pct
from tempo.bracket import place_bracket, plan_bracket
from tempo.journal import Journal
from tempo.orders import Limits, OrderRefused, place
from tempo.risk import RiskRules


def ib_with(daily_pnl, net_liq=100_000.0, **kw):
    ib = FakeIB(**kw)
    ib.daily_pnl, ib.net_liq = daily_pnl, net_liq
    return ib


def test_loss_pct_is_measured_against_the_start_of_day_equity():
    # now 95,000 after losing 5,000 today -> the day started at 100,000 -> 5.0%
    assert daily_loss_pct(ib_with(-5_000.0, net_liq=95_000.0)) == pytest.approx(5.0)
    assert daily_loss_pct(ib_with(0.0)) == 0.0
    assert daily_loss_pct(ib_with(2_000.0, net_liq=102_000.0)) == pytest.approx(-2.0)   # a gain is a negative loss


def test_it_waits_for_the_first_update_and_always_cancels_the_subscription():
    ib = ib_with(-1_000.0, net_liq=99_000.0)
    ib.pnl_after_polls = 3
    assert daily_loss_pct(ib) == pytest.approx(1.0)
    assert ib.pnl_cancelled == 1


def test_a_stale_first_update_is_not_trusted():
    """Seen live: the first P&L callback said -11 and the real figure, -151, arrived about a second later."""
    ib = ib_with(-5_000.0, net_liq=95_000.0)
    ib.stale_pnl, ib.pnl_after_polls = 0.0, 4          # a stale zero for the first second
    assert daily_loss_pct(ib) == pytest.approx(5.0)    # must report the real loss, not the stale zero


def test_it_never_returns_before_the_settle_time_even_if_a_value_is_known_at_once():
    ib = ib_with(-1_000.0, net_liq=99_000.0)
    sleeps = []
    original = ib.sleep
    ib.sleep = lambda seconds: (sleeps.append(seconds), original(seconds))
    daily_loss_pct(ib)
    assert sum(sleeps) >= 2.0


@pytest.mark.parametrize("unavailable", [math.nan, 1.7976931348623157e308])
def test_unavailable_pnl_raises_and_still_cancels(unavailable):
    ib = ib_with(unavailable)
    with pytest.raises(RuntimeError, match="daily P&L"):
        daily_loss_pct(ib, timeout=1.0)
    assert ib.pnl_cancelled == 1


def test_missing_net_liquidation_raises():
    ib = ib_with(-1.0)
    ib.accountValues = lambda: []
    with pytest.raises(RuntimeError, match="NetLiquidation"):
        daily_loss_pct(ib)


def test_a_day_pnl_larger_than_total_equity_is_nonsense_and_raises():
    with pytest.raises(RuntimeError, match="start-of-day"):
        daily_loss_pct(ib_with(150.0, net_liq=100.0))   # would imply a negative starting equity


# --- the limit inside the order door ---

@pytest.fixture
def env(tmp_path):
    return {"journal": Journal(tmp_path / "j.jsonl"), "state_path": tmp_path / "state.json"}


def entry(ib, env, limit=5.0, order=None):
    limits = Limits(max_position_pct=50.0, max_daily_loss_pct=limit)
    return place(ib, SPY, order or MarketOrder("BUY", 10), reason="t", limits=limits, equity_usd=100_000.0,
                 ref_price=100.0, now=OPEN_NOW, **env)


def test_entries_are_allowed_below_the_limit_and_refused_at_it(env):
    entry(ib_with(-4_000.0, net_liq=96_000.0), env)                       # 4.17% < 5%
    with pytest.raises(OrderRefused, match="daily loss limit"):
        entry(ib_with(-5_000.0, net_liq=95_000.0), env, order=MarketOrder("BUY", 11))   # exactly 5.0%


def test_the_refusal_says_how_far_down_the_account_is(env):
    with pytest.raises(OrderRefused, match=r"5\.3.*5\.0"):
        entry(ib_with(-5_300.0, net_liq=94_700.0), env)   # 5,300 down from a 100,000 start = 5.3%, limit 5.0%


def test_exits_are_never_blocked_by_the_daily_loss_limit(env):
    ib = ib_with(-20_000.0, net_liq=80_000.0, positions={"SPY": 10})
    place(ib, SPY, MarketOrder("SELL", 10), reason="exit", limits=Limits(50.0, max_daily_loss_pct=5.0), now=OPEN_NOW, **env)
    assert ib.held["SPY"] == 0


def test_unknown_pnl_blocks_entries_but_not_exits(env):
    with pytest.raises(OrderRefused, match="daily P&L unknown"):
        entry(ib_with(math.nan), env)
    held = ib_with(math.nan, positions={"SPY": 3})
    place(held, SPY, MarketOrder("SELL", 3), reason="exit", limits=Limits(50.0, max_daily_loss_pct=5.0), now=OPEN_NOW, **env)


def test_no_limit_means_the_pnl_is_not_even_asked_for(env):
    ib = ib_with(-90_000.0, net_liq=10_000.0)
    ib.reqPnL = lambda account: pytest.fail("P&L was requested although the limit is disabled")
    entry(ib, env, limit=None)


def test_bracket_entries_obey_the_limit_too(env):
    plan = plan_bracket(100_000.0, 100.0, 98.0, None, RiskRules(2.0, 50.0, 5.0), qty=1)
    ib = ib_with(-6_000.0, net_liq=94_000.0)
    with pytest.raises(OrderRefused, match="daily loss limit"):
        place_bracket(ib, SPY, plan, limits=Limits(50.0, max_daily_loss_pct=5.0), equity_usd=100_000.0, now=OPEN_NOW, **env)
    assert ib.placed == []


def test_the_pnl_check_comes_after_the_cheap_checks(env):
    ib = ib_with(-6_000.0, net_liq=94_000.0)
    ib.reqPnL = lambda account: pytest.fail("P&L requested even though the order is already refused for its size")
    with pytest.raises(OrderRefused, match="position cap"):
        entry(ib, env, order=MarketOrder("BUY", 1000))
