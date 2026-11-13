"""D3 + D4 as pure functions. NOT wired into the order path (plan: needs a broker dry run first).

book:   [{"symbol", "notional" (signed USD: long +, short -), "beta", "sector"}]
net exposure  = sum of signed notionals; it must stay within MAX_NET_PCT of equity.
beta exposure = sum of notional x beta (USD of SPY-equivalent). hedge_order() returns the single SPY trade that cancels it, or None when
                it is already small (below MIN_HEDGE_PCT of equity: a ticket that small costs more commission than the risk it removes).
sector cap    = no sector may hold more than MAX_SECTOR_SHARE of GROSS exposure; check_sector_cap() names offenders, it never trims.
Unknown beta or sector is an error, never a default: a guessed beta hides the very risk this exists to show.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MAX_NET_PCT = 10.0
MIN_HEDGE_PCT = 1.0
MAX_SECTOR_SHARE = 0.15


@dataclass(frozen=True)
class Hedge:
    side: str            # "SELL" or "BUY"
    notional: float      # USD of SPY, always positive


def _check(book: list[dict], need_sector: bool = False) -> None:
    for p in book:
        for key in ("symbol", "notional", "beta") + (("sector",) if need_sector else ()):
            if p.get(key) is None:
                raise ValueError(f"{p.get('symbol', '?')}: missing {key}")
        if not (math.isfinite(p["notional"]) and math.isfinite(p["beta"])):
            raise ValueError(f"{p['symbol']}: non-finite notional or beta")


def gross(book: list[dict]) -> float:
    return sum(abs(p["notional"]) for p in book)


def net(book: list[dict]) -> float:
    return sum(p["notional"] for p in book)


def beta_exposure(book: list[dict]) -> float:
    _check(book)
    return sum(p["notional"] * p["beta"] for p in book)


def net_within_cap(book: list[dict], equity: float) -> bool:
    if not (math.isfinite(equity) and equity > 0):
        raise ValueError("equity must be positive")
    return abs(net(book)) <= equity * MAX_NET_PCT / 100


def hedge_order(book: list[dict], equity: float) -> Hedge | None:
    """The one SPY order that zeroes the book's beta exposure, or None if it is below the minimum ticket."""
    if not (math.isfinite(equity) and equity > 0):
        raise ValueError("equity must be positive")
    exposure = beta_exposure(book)
    if abs(exposure) < equity * MIN_HEDGE_PCT / 100:
        return None
    return Hedge("SELL" if exposure > 0 else "BUY", abs(exposure))


def check_sector_cap(book: list[dict]) -> list[str]:
    """Sectors above MAX_SECTOR_SHARE of gross, as 'sector share'. An empty book has no offenders."""
    _check(book, need_sector=True)
    total = gross(book)
    if total == 0:
        return []
    by: dict[str, float] = {}
    for p in book:
        by[p["sector"]] = by.get(p["sector"], 0.0) + abs(p["notional"])
    return sorted(f"{s} {v / total:.0%}" for s, v in by.items() if v / total > MAX_SECTOR_SHARE)
