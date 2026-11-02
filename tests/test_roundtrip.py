import pytest
from fakes import OPEN_NOW, SPY, FakeIB

from tempo.journal import Journal
from tempo.orders import Limits
from tempo.roundtrip import far_limit_price, run_roundtrip


@pytest.fixture
def env(tmp_path):
    return dict(journal=Journal(tmp_path / "j.jsonl"), limits=Limits(max_position_pct=50.0), equity_usd=100_000.0,
                state_path=tmp_path / "state.json", now=OPEN_NOW)


def test_far_limit_price_is_half_of_last_close():
    assert far_limit_price(755.72) == 377.86


def test_happy_path_places_far_limit_then_cancels(env):
    ib = FakeIB(fill=False)
    checks = run_roundtrip(ib, SPY, 755.72, **env)
    assert [c.name for c in checks] == ["place", "visible", "cancel", "clean"]
    assert all(c.ok for c in checks)
    order = ib.placed[0]
    assert (order.action, order.totalQuantity, order.lmtPrice) == ("BUY", 1, 377.86)
    assert env["journal"].unresolved() == []


def test_order_that_would_fill_is_reported_as_failure(env):
    ib = FakeIB(fill=True)  # a "far" order that fills means the safety premise is broken
    checks = {c.name: c for c in run_roundtrip(ib, SPY, 755.72, **env)}
    assert not checks["place"].ok


def test_order_is_cancelled_even_if_a_step_raises(env):
    ib = FakeIB(fill=False)

    def boom():
        raise RuntimeError("boom")

    ib.openTrades = boom
    with pytest.raises(RuntimeError):
        run_roundtrip(ib, SPY, 100.0, **env)
    assert ib.trades[0].orderStatus.status == "Cancelled"
