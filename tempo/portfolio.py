"""Multi-asset daily backtester for monthly rotation rules. Long-only, whole shares, cash earns 0.

Same honesty rules as `tempo.backtest`: a signal decided from closes through day s is filled at day s+1's close,
every order pays `Costs`, and a run on the first k days is identical to the first k days of a longer run (tested),
which is the property that rules out look-ahead.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from tempo.backtest import Costs, order_cost

Closes = dict[str, list[float]]


@dataclass(frozen=True)
class PTrade:
    day: int
    symbol: str
    side: str
    shares: int
    price: float
    cost: float


@dataclass(frozen=True)
class PResult:
    equity: list[float]
    trades: list[PTrade]
    costs: float


def align(series: dict[str, tuple[list[str], list[float]]]) -> tuple[list[str], Closes]:
    """Keep only the dates every symbol has, so the sample starts when the youngest ETF does."""
    common = set.intersection(*(set(dates) for dates, _ in series.values()))
    if not common:
        raise ValueError("the symbols share no dates")
    dates = sorted(common)
    lookup = {sym: dict(zip(d, c)) for sym, (d, c) in series.items()}
    return dates, {sym: [lookup[sym][day] for day in dates] for sym in series}


def month_end_indices(dates: list[str]) -> list[int]:
    """Index of the last trading day of each month. The final month is skipped: it may be unfinished."""
    return [i for i in range(len(dates) - 1) if dates[i][:7] != dates[i + 1][:7]]


def momentum_scores(closes: Closes, t: int, lookback: int, skip: int) -> dict[str, float]:
    """close[t-skip] / close[t-lookback] - 1 for each symbol; empty if there is not enough history."""
    if t - lookback < 0:
        return {}
    return {sym: c[t - skip] / c[t - lookback] - 1 for sym, c in closes.items()}


def pick(scores: dict[str, float], top_n: int) -> list[str]:
    """Top n by score among the positive ones; ties broken by symbol so the result is deterministic."""
    positive = sorted(((-s, sym) for sym, s in scores.items() if s > 0))
    return [sym for _, sym in positive[:top_n]]


def run_rotation(dates: list[str], closes: Closes, costs: Costs, lookback: int = 252, skip: int = 21,
                 top_n: int = 3, mode: str = "momentum", start_cash: float = 100_000.0) -> PResult:
    """mode 'momentum': hold the picks, 1/top_n of equity each. mode 'equal_weight': hold every symbol equally."""
    if mode not in ("momentum", "equal_weight"):
        raise ValueError(f"unknown mode {mode!r}")
    symbols = sorted(closes)
    signal_days = set(month_end_indices(dates))
    cash, shares = start_cash, {s: 0 for s in symbols}
    targets: list[str] | None = None
    equity: list[float] = []
    trades: list[PTrade] = []
    for t in range(len(dates)):
        px = {s: closes[s][t] for s in symbols}
        if targets is not None:  # decided at yesterday's close, filled at today's
            slots = len(symbols) if mode == "equal_weight" else top_n
            total = cash + sum(shares[s] * px[s] for s in symbols)
            want = {s: (int(total / slots // px[s]) if s in targets else 0) for s in symbols}
            for s in symbols:  # sells first so the buys can use the cash
                if want[s] < shares[s]:
                    qty = shares[s] - want[s]
                    cost = order_cost(qty, px[s], "SELL", costs)
                    cash += qty * px[s] - cost
                    shares[s] = want[s]
                    trades.append(PTrade(t, s, "SELL", qty, px[s], cost))
            for s in symbols:
                qty = want[s] - shares[s]
                while qty > 0 and qty * px[s] + order_cost(qty, px[s], "BUY", costs) > cash:
                    qty -= 1
                if qty > 0:
                    cost = order_cost(qty, px[s], "BUY", costs)
                    cash -= qty * px[s] + cost
                    shares[s] += qty
                    trades.append(PTrade(t, s, "BUY", qty, px[s], cost))
            targets = None
        equity.append(cash + sum(shares[s] * px[s] for s in symbols))
        if t in signal_days:
            if mode == "equal_weight":
                targets = symbols if t >= 1 else None
            else:
                scores = momentum_scores(closes, t, lookback, skip)
                targets = pick(scores, top_n) if scores else None
    return PResult(equity=equity, trades=trades, costs=sum(tr.cost for tr in trades))


def same_permutation_shuffle(closes: Closes, rng: random.Random) -> Closes:
    """Shuffle the order of days, using ONE permutation for every asset.

    Keeps each asset's return distribution and the correlations between assets, and destroys serial structure:
    the thing a momentum rule needs. A rule with no real edge should do about as well on these as on the real data.
    """
    symbols = list(closes)
    n = len(closes[symbols[0]]) - 1
    order = list(range(n))
    rng.shuffle(order)
    out: Closes = {}
    for sym, c in closes.items():
        ratios = [c[i + 1] / c[i] for i in range(n)]
        path = [c[0]]
        for i in order:
            path.append(path[-1] * ratios[i])
        out[sym] = path
    return out
