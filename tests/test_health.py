from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

from tempo.health import run_health


def fake_ib(accounts=("DU1234567",), net="1000000", skew=0, positions=(), trades=()):
    summary = [NS(tag=t, value=v, currency="USD") for t, v in
               [("NetLiquidation", net), ("TotalCashValue", "500"), ("BuyingPower", "2000"), ("AvailableFunds", "500")]]
    return NS(
        managedAccounts=lambda: list(accounts),
        accountSummary=lambda: summary,
        reqCurrentTime=lambda: datetime.now(timezone.utc) + timedelta(seconds=skew),
        positions=lambda: list(positions),
        openTrades=lambda: list(trades),
    )


def by_name(checks):
    return {c.name: c for c in checks}


def test_healthy_paper_account_all_ok():
    checks = run_health(fake_ib(positions=[NS(position=10)]))
    assert all(c.ok for c in checks)
    assert by_name(checks)["positions"].detail == "1 open"


def test_flat_positions_not_counted():
    assert by_name(run_health(fake_ib(positions=[NS(position=0)])))["positions"].detail == "0 open"


def test_live_account_fails():
    assert not by_name(run_health(fake_ib(accounts=("U1234567",))))["account"].ok


def test_zero_equity_fails():
    assert not by_name(run_health(fake_ib(net="0")))["equity"].ok


def test_clock_skew_fails():
    assert not by_name(run_health(fake_ib(skew=60)))["clock"].ok
