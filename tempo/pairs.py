"""Dollar-neutral pairs trading on daily closes (rule fixed in evidence/pairs_trading.json).

Same honesty rules as `tempo.backtest`: a signal decided from closes through day t is filled at day t+1's close,
every order pays `Costs` on both legs, shorts pay a daily borrow fee, and a run on the first k days equals the
first k days of a longer run (tested), which rules out look-ahead.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from tempo.backtest import TRADING_DAYS, Costs, order_cost


@dataclass(frozen=True)
class PairParams:
    window: int = 60
    enter: float = 2.0
    exit_z: float = 0.5
    stop_z: float = 4.0
    max_hold: int = 30


@dataclass(frozen=True)
class PairTrade:
    day: int
    leg: str  # "A" or "B"
    side: str
    shares: int
    price: float
    cost: float


@dataclass(frozen=True)
class PairResult:
    equity: list[float]
    trades: list[PairTrade]
    costs: float
    borrow: float


def zscores(spread: list[float], window: int) -> list[float | None]:
    """Rolling z-score of the spread over the last `window` values (including today). None until the window is
    full, and None when the window is flat (no division by zero)."""
    out: list[float | None] = []
    for t in range(len(spread)):
        if t + 1 < window:
            out.append(None)
            continue
        chunk = spread[t + 1 - window:t + 1]
        mean = sum(chunk) / window
        std = math.sqrt(sum((x - mean) ** 2 for x in chunk) / window)
        out.append(None if std < 1e-12 else (spread[t] - mean) / std)
    return out


def pair_signals(closes_a: list[float], closes_b: list[float], params: PairParams) -> list[int]:
    """Target position per day, decided at that day's close: +1 long the spread (buy A, short B), -1 short it, 0 flat."""
    spread = [math.log(a) - math.log(b) for a, b in zip(closes_a, closes_b)]
    pos, held, out = 0, 0, []
    for z in zscores(spread, params.window):
        if z is None:
            pos = 0
        elif pos == 0:
            held = 0
            if params.enter < abs(z) <= params.stop_z:
                pos = -1 if z > 0 else 1
        else:
            held += 1
            if abs(z) < params.exit_z or abs(z) > params.stop_z or held >= params.max_hold:
                pos = 0
        out.append(pos)
    return out


def run_pair(closes_a: list[float], closes_b: list[float], signals: list[int], costs: Costs, capital: float,
             borrow_rate: float) -> PairResult:
    """Trade the signals. Each leg is half of the pair's current equity, whole shares. Borrow is charged daily on the
    previous close's short value at borrow_rate / 252."""
    if not (len(closes_a) == len(closes_b) == len(signals)):
        raise ValueError("closes and signals must have the same length")
    cash, sa, sb, pos = capital, 0, 0, 0
    equity: list[float] = []
    trades: list[PairTrade] = []
    borrow_total = 0.0
    for t in range(len(closes_a)):
        pa, pb = closes_a[t], closes_b[t]
        if t > 0:
            short_value = max(-sa, 0) * closes_a[t - 1] + max(-sb, 0) * closes_b[t - 1]
            fee = short_value * borrow_rate / TRADING_DAYS
            cash -= fee
            borrow_total += fee
        target = signals[t - 1] if t > 0 else 0  # yesterday's decision, filled at today's close
        if target != pos:
            for leg, shares, price in (("A", sa, pa), ("B", sb, pb)):
                if shares:  # close what we hold
                    side = "SELL" if shares > 0 else "BUY"
                    cost = order_cost(abs(shares), price, side, costs)
                    cash += shares * price - cost
                    trades.append(PairTrade(t, leg, side, abs(shares), price, cost))
            sa = sb = 0
            if target != 0:
                half = (cash) / 2
                qa, qb = int(half // pa), int(half // pb)
                sa, sb = (qa, -qb) if target == 1 else (-qa, qb)
                for leg, shares, price in (("A", sa, pa), ("B", sb, pb)):
                    if shares:
                        side = "BUY" if shares > 0 else "SELL"
                        cost = order_cost(abs(shares), price, side, costs)
                        cash -= shares * price + cost
                        trades.append(PairTrade(t, leg, side, abs(shares), price, cost))
            pos = target
        equity.append(cash + sa * pa + sb * pb)
    return PairResult(equity=equity, trades=trades, costs=sum(tr.cost for tr in trades), borrow=borrow_total)
