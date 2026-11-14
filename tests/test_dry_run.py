import pytest

from tempo.dry_run import plan_day, render
from tempo.sizing import SizingRules

RULES = SizingRules(target_risk_pct=0.3, floor_pct=1.0)
EQ = 100_000.0


def row(sym, d=1, price=50.0, vol=0.02, beta=1.0):
    return {"symbol": sym, "direction": d, "price": price, "vol20": vol, "beta": beta}


def test_sizes_signs_and_hedges_a_long_book():
    p = plan_day([row("A"), row("B")], EQ, RULES)
    assert [b["notional"] for b in p.book] == [15_000.0, 15_000.0]       # 0.3% / 2% = 15% of equity, at the cap
    assert p.hedge is not None and p.hedge.side == "SELL" and p.hedge.notional == pytest.approx(30_000)
    assert not p.net_ok and "ABOVE CAP" in render(p, EQ)


def test_shorts_net_out_and_skips_are_named_never_guessed():
    p = plan_day([row("A"), row("B", d=-1), row("C", vol=None), row("D", price=None), row("E", vol=0.0)], EQ, RULES)
    assert p.net == 0 and p.net_ok and p.hedge is None
    assert dict(p.skipped) == {"C": "no vol20", "D": "no price", "E": "skip_bad_input"}


def test_missing_beta_is_an_error_and_an_empty_day_is_fine():
    with pytest.raises(ValueError):
        plan_day([row("A", beta=None)], EQ, RULES)
    p = plan_day([], EQ, RULES)
    assert p.book == () and p.net_ok and "none needed" in render(p, EQ)
