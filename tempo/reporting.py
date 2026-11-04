"""Small helpers shared by the strategy report runners (one copy, tested)."""
from __future__ import annotations


def daily_returns(values: list[float]) -> list[float]:
    return [b / a - 1 for a, b in zip(values, values[1:])]


def by_year(dates: list[str], equity: list[float]) -> list[tuple[str, float]]:
    """Return for each calendar year, chained from the previous year's last value (the first year from its own first value)."""
    out, start = [], 0
    for i in range(1, len(dates) + 1):
        if i == len(dates) or dates[i][:4] != dates[start][:4]:
            out.append((dates[start][:4], equity[i - 1] / equity[max(start - 1, 0)] - 1))
            start = i
    return out
