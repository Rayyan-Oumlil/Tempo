"""Tactical asset allocation (rule fixed in evidence/tactical_allocation.json): hold each asset only while its
month-end close is above the average of its last M month-end closes (including the current one), else cash.

Weight functions for `tempo.portfolio.run_weighted`. They only look at closes through the month-end index they are
asked about, so a run on the first k days equals the first k days of a longer run (tested).
"""
from __future__ import annotations

from tempo.portfolio import Closes, month_end_indices


def trend_weight_fn(closes: Closes, dates: list[str], months: int, weight_each: float):
    """weight_each for every asset above its `months`-month-end average; None until `months` month ends exist."""
    month_ends = month_end_indices(dates)

    def weights(t: int):
        window = [i for i in month_ends if i <= t][-months:]
        if len(window) < months:
            return None
        return {s: weight_each for s, c in closes.items() if c[t] > sum(c[i] for i in window) / months}

    return weights


def fixed_weight_fn(weights: dict[str, float]):
    """The same target weights at every month end (monthly rebalancing)."""
    return lambda t: dict(weights)
