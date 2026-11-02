import math
from types import SimpleNamespace as NS

import pytest

from tempo import size, smoke
from tempo.config import IbkrConfig
from tempo.risk import RiskRules


class SmokeIB:
    """Just enough of IB for the smoke checks; each method can be overridden per test."""

    def __init__(self, **overrides):
        self.errorEvent = _Event()
        self.disconnected = False
        for name, fn in overrides.items():
            setattr(self, name, fn)

    def qualifyContracts(self, contract):
        contract.conId = 756733
        return [contract]

    def reqContractDetails(self, contract):
        return [NS(longName="SPDR", minTick=0.01, timeZoneId="US/Eastern", tradingHours="20261102:0930-20261102:1600;x")]

    def reqMarketDataType(self, kind):
        pass

    def reqTickers(self, contract):
        return [NS(marketPrice=lambda: 100.0, bid=99.9, ask=100.1, close=99.0)]

    def reqHeadTimeStamp(self, contract, **kwargs):
        return "1993-01-29"

    def reqHistoricalData(self, *args, **kwargs):
        return [NS(date="2026-11-02", open=1, high=2, low=0.5, close=1.5, volume=10)]

    def whatIfOrder(self, contract, order):
        return NS(commission=1.0, commissionCurrency="USD", initMarginChange="318")

    def disconnect(self):
        self.disconnected = True


class _Event:
    def __iadd__(self, fn):
        return self

    def __isub__(self, fn):
        return self


def test_qualify_reports_the_contract_and_fails_when_nothing_qualifies():
    assert "conId=756733" in smoke.t_qualify(SmokeIB(), "SPY")
    with pytest.raises(RuntimeError, match="could not be qualified"):
        smoke.t_qualify(SmokeIB(qualifyContracts=lambda c: []), "ZZZZ")


def test_contract_details_fail_when_empty():
    assert "SPDR" in smoke.t_contract_details(SmokeIB(), "SPY")
    with pytest.raises(RuntimeError, match="no contract details"):
        smoke.t_contract_details(SmokeIB(reqContractDetails=lambda c: []), "SPY")


def test_snapshot_uses_the_market_price_then_falls_back_to_the_close_then_fails():
    assert "price=100.0" in smoke.t_snapshot(SmokeIB(), "SPY")
    no_live = lambda c: [NS(marketPrice=lambda: math.nan, bid=math.nan, ask=math.nan, close=99.0)]
    assert "price=99.0" in smoke.t_snapshot(SmokeIB(reqTickers=no_live), "SPY")
    nothing = lambda c: [NS(marketPrice=lambda: math.nan, bid=math.nan, ask=math.nan, close=math.nan)]
    with pytest.raises(RuntimeError, match="no price"):
        smoke.t_snapshot(SmokeIB(reqTickers=nothing), "SPY")


def test_head_timestamp_daily_bars_and_what_if():
    assert "1993-01-29" in smoke.t_head_timestamp(SmokeIB(), "SPY")
    assert "1 bars" in smoke.t_daily_bars(SmokeIB(), "SPY")
    with pytest.raises(RuntimeError, match="no bars"):
        smoke.t_daily_bars(SmokeIB(reqHistoricalData=lambda *a, **k: []), "SPY")
    assert "commission=1.0 USD" in smoke.t_what_if(SmokeIB(), "SPY")


def cfg(readonly=True):
    return IbkrConfig(host="h", port=1, client_id=1, readonly=readonly, timeout=1.0)


def test_smoke_main_runs_every_check_and_returns_zero_when_all_pass(monkeypatch, capsys):
    ib = SmokeIB()
    monkeypatch.setattr(smoke, "load_dotenv", lambda: None)
    monkeypatch.setattr(smoke, "load_config", lambda: cfg())
    monkeypatch.setattr(smoke, "connect", lambda c: ib)
    assert smoke.main("SPY") == 0
    out = capsys.readouterr().out
    assert out.count("[OK]") == len(smoke.TESTS) and ib.disconnected


def test_smoke_main_returns_one_when_a_check_fails(monkeypatch, capsys):
    ib = SmokeIB(reqHistoricalData=lambda *a, **k: [])
    monkeypatch.setattr(smoke, "load_dotenv", lambda: None)
    monkeypatch.setattr(smoke, "load_config", lambda: cfg())
    monkeypatch.setattr(smoke, "connect", lambda c: ib)
    assert smoke.main("SPY") == 1
    assert "[FAIL]" in capsys.readouterr().out


def test_smoke_what_if_refuses_to_run_on_a_read_only_connection(monkeypatch):
    monkeypatch.setattr(smoke, "load_dotenv", lambda: None)
    monkeypatch.setattr(smoke, "load_config", lambda: cfg(readonly=True))
    with pytest.raises(RuntimeError, match="IBKR_READONLY=0"):
        smoke.main("SPY", what_if=True)


def fake_size_env(monkeypatch, bars, equity=100_000.0):
    ib = SmokeIB(reqHistoricalData=lambda *a, **k: bars)
    monkeypatch.setattr(size, "load_dotenv", lambda: None)
    monkeypatch.setattr(size, "load_config", lambda: cfg())
    monkeypatch.setattr(size, "connect", lambda c: ib)
    monkeypatch.setattr(size, "equity_usd", lambda i: equity)
    monkeypatch.setattr(size, "load_rules", lambda: RiskRules(2.0, 50.0))
    return ib


def test_size_prints_the_shares_the_rules_allow(monkeypatch, capsys):
    ib = fake_size_env(monkeypatch, [NS(close=100.0)])
    assert size.main("SPY", 98.0) == 0
    out = capsys.readouterr().out
    assert "500 shares" in out and "position cap" in out and ib.disconnected


def test_size_explains_a_zero_share_result(monkeypatch, capsys):
    fake_size_env(monkeypatch, [NS(close=100.0)], equity=10.0)
    assert size.main("SPY", 98.0) == 0
    assert "0 shares" in capsys.readouterr().out


def test_size_fails_without_price_data_and_with_a_bad_stop(monkeypatch):
    fake_size_env(monkeypatch, [])
    with pytest.raises(RuntimeError, match="No daily bars"):
        size.main("SPY", 98.0)
    fake_size_env(monkeypatch, [NS(close=100.0)])
    with pytest.raises(ValueError, match="stop"):
        size.main("SPY", 105.0)
