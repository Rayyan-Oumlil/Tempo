from types import SimpleNamespace as NS

import pytest

from tempo import ibkr
from tempo.account import equity_usd, last_close
from tempo.config import IbkrConfig

CFG = IbkrConfig(host="127.0.0.1", port=4002, client_id=21, readonly=True, timeout=5.0)


class FakeConnectIB:
    """Stands in for ib_async.IB() so connect() can be tested without a Gateway."""
    instances = []

    def __init__(self):
        self.accounts = ["DU1234567"]
        self.connect_error = None
        self.disconnected = False
        self.connect_args = None
        FakeConnectIB.instances.append(self)

    def connect(self, host, port, **kwargs):
        if self.connect_error:
            raise self.connect_error
        self.connect_args = (host, port, kwargs)

    def managedAccounts(self):
        return self.accounts

    def disconnect(self):
        self.disconnected = True


@pytest.fixture
def fake_ib(monkeypatch):
    FakeConnectIB.instances = []
    monkeypatch.setattr(ibkr, "IB", FakeConnectIB)
    return FakeConnectIB


def test_connect_paper_account_passes_settings_through(fake_ib):
    ib = ibkr.connect(CFG)
    host, port, kwargs = ib.connect_args
    assert (host, port) == ("127.0.0.1", 4002)
    assert kwargs["clientId"] == 21 and kwargs["readonly"] is True and kwargs["raiseSyncErrors"] is True
    assert not ib.disconnected


def test_connect_refuses_a_live_account_and_disconnects(fake_ib, monkeypatch):
    monkeypatch.setattr(FakeConnectIB, "managedAccounts", lambda self: ["U1234567"])
    with pytest.raises(RuntimeError, match="not a paper account"):
        ibkr.connect(CFG)
    assert fake_ib.instances[0].disconnected


def test_connect_with_no_account_yet_fails_and_disconnects(fake_ib, monkeypatch):
    monkeypatch.setattr(FakeConnectIB, "managedAccounts", lambda self: [])
    with pytest.raises(ConnectionError, match="no account"):
        ibkr.connect(CFG)
    assert fake_ib.instances[0].disconnected


@pytest.mark.parametrize("error", [ConnectionRefusedError("refused"), TimeoutError("slow")])
def test_connect_failure_becomes_a_clear_connection_error(fake_ib, monkeypatch, error):
    def boom(self, *a, **k):
        raise error

    monkeypatch.setattr(FakeConnectIB, "connect", boom)
    with pytest.raises(ConnectionError, match="not reachable"):
        ibkr.connect(CFG)
    assert fake_ib.instances[0].disconnected


@pytest.mark.parametrize("account,ok", [("DU1", True), ("DF2", True), ("U123", False), ("", False), ("none", False)])
def test_assert_paper_only_accepts_paper_prefixes(account, ok):
    if ok:
        ibkr.assert_paper(account)
    else:
        with pytest.raises(RuntimeError):
            ibkr.assert_paper(account)


def values(*rows):
    return NS(accountValues=lambda: [NS(tag=t, currency=c, value=str(v)) for t, c, v in rows])


def test_equity_usd_when_the_account_is_in_usd():
    assert equity_usd(values(("NetLiquidation", "USD", 1000.0))) == 1000.0


def test_equity_usd_uses_the_exchange_rate_rows_when_present():
    ib = values(("NetLiquidation", "CAD", 1400.0), ("ExchangeRate", "CAD", 1.0), ("ExchangeRate", "USD", 1.4))
    assert equity_usd(ib) == pytest.approx(1000.0)


def test_equity_usd_falls_back_to_the_forex_price_for_a_cad_only_account():
    class Ib:
        def accountValues(self):
            return [NS(tag="NetLiquidation", currency="CAD", value="1400"), NS(tag="NetLiquidation", currency="BASE", value="1400")]

        def qualifyContracts(self, *_):
            pass

        def reqHistoricalData(self, *a, **k):
            return [NS(close=1.4)]

    assert equity_usd(Ib()) == pytest.approx(1000.0)


def test_equity_usd_fails_loudly_without_net_liquidation_or_a_rate():
    with pytest.raises(RuntimeError, match="NetLiquidation"):
        equity_usd(values(("TotalCashValue", "USD", 5)))

    class NoRate:
        def accountValues(self):
            return [NS(tag="NetLiquidation", currency="CAD", value="1400")]

        def qualifyContracts(self, *_):
            pass

        def reqHistoricalData(self, *a, **k):
            return []

    with pytest.raises(RuntimeError, match="USD.CAD"):
        equity_usd(NoRate())


def test_last_close_returns_the_newest_close_and_fails_on_no_data():
    ok = NS(reqHistoricalData=lambda *a, **k: [NS(close=10.0), NS(close=11.5)])
    assert last_close(ok, NS(symbol="SPY")) == 11.5
    with pytest.raises(RuntimeError, match="No daily bars"):
        last_close(NS(reqHistoricalData=lambda *a, **k: []), NS(symbol="SPY"))
