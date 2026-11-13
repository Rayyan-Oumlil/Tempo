"""D2 equal-risk sizing as a pure function. NOT wired into the order path: that needs a broker dry run first (plan D2).

notional = target daily risk (USD) / sigma20, capped per name; if the result is below the commission floor the trade is SKIPPED, never
shrunk into a commission trap (a 300 USD ticket pays the minimum commission, so its cost in bps is many times the registered cost).
All three numbers are percentages of equity, so paper and live use the same rule and only equity differs.

target_risk_pct has no default on purpose: it is the one free parameter, it must be chosen and written down before results exist.
Live reference at 20,000 USD: cap 15% (3,000 USD), floor about 1,800 USD on the Fixed plan or about 800 USD on Tiered.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MAX_NAME_PCT = 15.0


@dataclass(frozen=True)
class SizingRules:
    target_risk_pct: float          # daily risk per position, % of equity
    floor_pct: float                # below this notional (% of equity) the commission eats the trade: skip
    max_name_pct: float = MAX_NAME_PCT

    def __post_init__(self) -> None:
        if not (0 < self.target_risk_pct and 0 < self.floor_pct < self.max_name_pct <= 100):
            raise ValueError(f"inconsistent sizing rules: {self}")


@dataclass(frozen=True)
class Sizing:
    shares: int
    notional: float
    status: str                     # sized | capped | skip_below_floor | skip_bad_input


def size_position(equity: float, price: float, sigma20: float, rules: SizingRules) -> Sizing:
    """Whole shares. Bad inputs (non-positive or non-finite equity, price or sigma) skip with a status, never guess a volatility."""
    if not all(math.isfinite(v) and v > 0 for v in (equity, price, sigma20)):
        return Sizing(0, 0.0, "skip_bad_input")
    wanted = equity * rules.target_risk_pct / 100 / sigma20
    cap = equity * rules.max_name_pct / 100
    notional = min(wanted, cap)
    shares = int(notional // price)
    value = shares * price
    if shares == 0 or value < equity * rules.floor_pct / 100:
        return Sizing(0, 0.0, "skip_below_floor")
    return Sizing(shares, value, "capped" if wanted >= cap else "sized")
