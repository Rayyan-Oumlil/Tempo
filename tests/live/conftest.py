"""Live checks against the real IB Gateway PAPER account. Skipped unless TEMPO_LIVE=1.

Run on a trading day during regular hours:   $env:TEMPO_LIVE=1; pytest tests/live -v
They place real (paper) orders, use a temporary journal and state file, and always end by cancelling everything
and flattening, so the account is left clean.
"""
import dataclasses
import os

import pytest
from dotenv import load_dotenv
from ib_async import Stock

from tempo.account import equity_usd, last_close
from tempo.config import load_config
from tempo.flatten import flatten_positions
from tempo.hours import is_regular_hours
from tempo.ibkr import connect
from tempo.journal import Journal
from tempo.orders import Limits

pytestmark = pytest.mark.live


def pytest_collection_modifyitems(config, items):
    if os.environ.get("TEMPO_LIVE") != "1":
        skip = pytest.mark.skip(reason="live tests need TEMPO_LIVE=1 (and IB Gateway on the paper account)")
        for item in items:
            if "tests/live" in str(item.fspath).replace("\\", "/"):
                item.add_marker(skip)


@pytest.fixture(scope="module")
def ib():
    load_dotenv()
    if not is_regular_hours():
        pytest.skip("market is closed: live order tests need regular hours")
    conn = connect(dataclasses.replace(load_config(), readonly=False))
    conn.RequestTimeout = 15
    yield conn
    conn.disconnect()


@pytest.fixture
def spy(ib):
    contract = Stock("SPY", "SMART", "USD")
    ib.qualifyContracts(contract)
    return contract


@pytest.fixture
def env(ib, spy, tmp_path):
    journal = Journal(tmp_path / "journal.jsonl")
    ctx = dict(journal=journal, limits=Limits(max_position_pct=100.0), state_path=tmp_path / "state.json")
    ctx["equity"], ctx["price"] = equity_usd(ib), last_close(ib, spy)
    yield ctx
    # always leave the account clean, whatever the test did
    ib.reqGlobalCancel()
    ib.sleep(3)
    flatten_positions(ib, journal=Journal(tmp_path / "cleanup.jsonl"), limits=ctx["limits"], state_path=ctx["state_path"])
    ib.sleep(1)
