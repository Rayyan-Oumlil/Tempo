"""Overnight drift backtest: buy the close, sell the next open, every day (rule fixed in evidence/overnight_drift.json).

Honesty rules, as in `tempo.backtest`: every order pays `Costs` (commission, the SEC fee on sells, slippage in bps),
whole shares, cash idle at 0 during the day, nothing is bought on the last bar because there is no next open to sell
into, and a run on the first k days equals the first k-1 days of a longer run (the last day differs only because it
does not re-buy), which rules out look-ahead.
"""
from __future__ import annotations

import math
from dataclasses import replace

from tempo.backtest import Costs, Result, Trade, cagr, order_cost

MAX_SLIPPAGE_BPS = 200.0


def run_overnight(opens: list[float], closes: list[float], costs: Costs, capital: float) -> Result:
    """equity[t] is valued at day t's close, after that close's buy."""
    if len(opens) != len(closes):
        raise ValueError("opens and closes must have the same length")
    cash, shares = capital, 0
    equity: list[float] = []
    trades: list[Trade] = []
    for t in range(len(closes)):
        if shares:  # sell at today's open what we bought at yesterday's close
            cost = order_cost(shares, opens[t], "SELL", costs)
            cash += shares * opens[t] - cost
            trades.append(Trade(t, "SELL", shares, opens[t], cost))
            shares = 0
        if t < len(closes) - 1:  # buy at today's close, only if tomorrow's open exists to sell into
            qty = int(cash // closes[t])
            while qty > 0 and qty * closes[t] + order_cost(qty, closes[t], "BUY", costs) > cash:
                qty -= 1
            if qty > 0:
                cost = order_cost(qty, closes[t], "BUY", costs)
                cash -= qty * closes[t] + cost
                shares = qty
                trades.append(Trade(t, "BUY", qty, closes[t], cost))
        equity.append(cash + shares * closes[t])
    return Result(equity=equity, trades=trades, costs=sum(tr.cost for tr in trades))


def break_even_slippage(opens: list[float], closes: list[float], costs: Costs, capital: float) -> float:
    """Slippage in bps per side at which net CAGR reaches zero (commissions and fees in `costs` still apply).

    0.0 if the idea already loses at zero slippage; MAX_SLIPPAGE_BPS if it still wins there.
    """
    def net(bps: float) -> float:
        return cagr(run_overnight(opens, closes, replace(costs, slippage_bps=bps), capital).equity)

    if net(0.0) <= 0:
        return 0.0
    if net(MAX_SLIPPAGE_BPS) > 0:
        return MAX_SLIPPAGE_BPS
    lo, hi = 0.0, MAX_SLIPPAGE_BPS
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if net(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def t_statistic(returns: list[float]) -> float:
    """t-statistic of the mean of a return series (sample standard deviation)."""
    n = len(returns)
    if n < 2:
        raise ValueError("need at least two returns")
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if var == 0:
        return math.inf if mean > 0 else (-math.inf if mean < 0 else 0.0)
    return mean / math.sqrt(var / n)
