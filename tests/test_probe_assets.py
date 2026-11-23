from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tempo import probe_assets as p


def test_candidates_cover_the_plan_and_build_contracts():
    names = " ".join(p.CANDIDATES)
    for needle in ("XAUUSD", "MGC", "BTC", "ETH", "MBT", "GLD"):
        assert needle in names
    for make in p.CANDIDATES.values():
        assert make().symbol


def test_probe_module_never_touches_order_entry():
    src = Path(p.__file__).read_text()
    for banned in ("placeOrder", "whatIfOrder", "cancelOrder", "LimitOrder", "MarketOrder", "tempo.orders"):
        assert banned not in src.replace("NEVER places an order", "")


def test_resolve_explains_a_missing_instrument():
    ib = MagicMock()
    ib.reqContractDetails.return_value = []
    with pytest.raises(RuntimeError, match="200"):
        p._resolve(ib, p.CANDIDATES["XAUUSD spot gold"])


def test_failed_details_skips_dependent_tests():
    ib = MagicMock()
    ib.reqContractDetails.return_value = []
    ib.errorEvent = MagicMock()
    ib.errorEvent.__iadd__ = lambda s, f: s
    ib.errorEvent.__isub__ = lambda s, f: s
    results = p.probe_one(ib, "XAUUSD spot gold", p.CANDIDATES["XAUUSD spot gold"])
    assert len(results) == 1 and not results[0].ok
