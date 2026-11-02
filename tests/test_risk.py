import json
from types import SimpleNamespace as NS

import pytest

from tempo.account import equity_usd
from tempo.risk import RiskRules, load_rules, position_size

RULES = RiskRules(risk_per_trade_pct=1.0, max_position_pct=10.0, max_daily_loss_pct=5.0)


def test_position_cap_limits_a_tight_stop():
    r = position_size(5000, entry=100, stop=98, rules=RULES)
    assert (r.shares, r.limited_by) == (5, "position cap")  # risk would allow 25, cap allows 5
    assert r.notional == 500 and r.risk_amount == 10


def test_risk_limits_a_wide_stop():
    r = position_size(10000, entry=50, stop=40, rules=RULES)
    assert (r.shares, r.limited_by) == (10, "risk")  # risk allows 10, cap allows 20
    assert r.risk_amount == 100


def test_zero_shares_when_one_share_breaks_the_cap():
    r = position_size(1000, entry=500, stop=490, rules=RULES)
    assert r.shares == 0 and r.limited_by == "position cap"


def test_shares_are_whole_numbers():
    assert isinstance(position_size(10000, 33.3, 31.1, RULES).shares, int)


@pytest.mark.parametrize("entry,stop", [(100, 100), (100, 105), (0, -1), (-5, -6)])
def test_bad_prices_fail_loudly(entry, stop):
    with pytest.raises(ValueError):
        position_size(5000, entry, stop, RULES)


def test_non_positive_equity_fails():
    with pytest.raises(ValueError):
        position_size(0, 100, 98, RULES)


@pytest.mark.parametrize("risk,cap", [(0, 10), (1, 0), (-1, 10), (101, 10), (1, 150)])
def test_invalid_rules_rejected(risk, cap):
    with pytest.raises(ValueError):
        RiskRules(risk_per_trade_pct=risk, max_position_pct=cap, max_daily_loss_pct=5.0)


def test_load_rules_from_json(tmp_path):
    p = tmp_path / "rules.json"
    p.write_text(json.dumps({"risk_per_trade_pct": 0.5, "max_position_pct": 5, "max_daily_loss_pct": 3}))
    assert load_rules(p) == RiskRules(0.5, 5, 3)


def test_load_rules_missing_key_fails(tmp_path):
    p = tmp_path / "rules.json"
    p.write_text(json.dumps({"risk_per_trade_pct": 1}))
    with pytest.raises(ValueError, match="max_position_pct"):
        load_rules(p)


def values(net_ccy="CAD", net="6559.22", usd_rate="1.40"):
    return [
        NS(tag="NetLiquidation", currency="BASE", value="1"),
        NS(tag="NetLiquidation", currency=net_ccy, value=net),
        NS(tag="ExchangeRate", currency="USD", value=usd_rate),
        NS(tag="ExchangeRate", currency="CAD", value="1.0"),
    ]


def test_equity_usd_converts_from_base_currency():
    assert equity_usd(NS(accountValues=lambda: values())) == pytest.approx(6559.22 / 1.40)


def fx_ib(vs, bars):
    return NS(
        accountValues=lambda: vs,
        qualifyContracts=lambda *c: list(c),
        reqHistoricalData=lambda *a, **k: bars,
    )


def test_equity_usd_falls_back_to_forex_rate_when_account_has_no_usd_rate():
    vs = [v for v in values() if v.tag != "ExchangeRate"]  # paper account holding only CAD
    assert equity_usd(fx_ib(vs, [NS(close=1.40)])) == pytest.approx(6559.22 / 1.40)


def test_equity_usd_fails_loudly_when_no_rate_anywhere():
    vs = [v for v in values() if v.tag != "ExchangeRate"]
    with pytest.raises(RuntimeError, match="USD.CAD"):
        equity_usd(fx_ib(vs, []))


def test_equity_usd_passthrough_for_usd_accounts():
    vs = [NS(tag="NetLiquidation", currency="USD", value="5000")]
    assert equity_usd(fx_ib(vs, [])) == 5000.0


def test_equity_usd_fails_without_net_liquidation():
    with pytest.raises(RuntimeError, match="NetLiquidation"):
        equity_usd(fx_ib([], []))


@pytest.mark.parametrize("bad", [0, -1, 101])
def test_invalid_daily_loss_limit_rejected(bad):
    with pytest.raises(ValueError, match="max_daily_loss_pct"):
        RiskRules(risk_per_trade_pct=1.0, max_position_pct=10.0, max_daily_loss_pct=bad)


def test_rules_file_without_the_daily_loss_limit_fails_loudly(tmp_path):
    p = tmp_path / "rules.json"
    p.write_text(json.dumps({"risk_per_trade_pct": 1, "max_position_pct": 10}))
    with pytest.raises(ValueError, match="max_daily_loss_pct"):
        load_rules(p)
