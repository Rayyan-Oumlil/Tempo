"""A deliberately small daily-bar backtester. Long-only, one instrument, all-in or all-out.

Honesty rules built into the engine:
  * a signal decided from data through day t is executed at day t+1's close (no same-close fills)
  * every order pays the costs we measured on the paper account (see docs/ibkr-gotchas.md): 0.005 USD per share
    with a 1.00 USD minimum, the sell-side fee, plus an assumed slippage
  * a strategy returns one signal per day and may only look at closes up to that day (tested)
  * `negative_control` runs the same strategy on shuffled returns, to see what the pipeline reports on data
    with no serial structure

Limits: daily closes only, fills at the close, no dividends beyond what adjusted prices contain, one symbol (so
survivorship bias does not apply, but neither do portfolio effects).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable

TRADING_DAYS = 252
Strategy = Callable[[list[float]], list[int]]  # closes -> signal per day (1 = hold, 0 = flat)


@dataclass(frozen=True)
class Costs:
    per_share: float = 0.005
    min_per_order: float = 1.0
    sell_fee_per_million: float = 20.6  # inferred from paper fills, likely the SEC fee
    slippage_bps: float = 1.0  # assumed, not measured


@dataclass(frozen=True)
class Trade:
    day: int
    side: str
    shares: int
    price: float
    cost: float


@dataclass(frozen=True)
class Result:
    equity: list[float]
    trades: list[Trade]
    costs: float


def order_cost(shares: int, price: float, side: str, costs: Costs) -> float:
    notional = shares * price
    fee = max(costs.min_per_order, shares * costs.per_share)
    if side == "SELL":
        fee += notional * costs.sell_fee_per_million / 1e6
    return fee + notional * costs.slippage_bps / 1e4


def flat(closes: list[float]) -> list[int]:
    return [0] * len(closes)


def buy_and_hold(closes: list[float]) -> list[int]:
    return [1] * len(closes)


def sma_trend(window: int) -> Strategy:
    """Hold while the close is above its simple moving average. Uses only closes up to each day."""
    def signals(closes: list[float]) -> list[int]:
        out = []
        for t in range(len(closes)):
            if t + 1 < window:
                out.append(0)
            else:
                out.append(1 if closes[t] > sum(closes[t + 1 - window:t + 1]) / window else 0)
        return out
    return signals


def backtest(closes: list[float], signals: list[int], costs: Costs, start_cash: float = 100_000.0) -> Result:
    cash, shares = start_cash, 0
    equity: list[float] = []
    trades: list[Trade] = []
    for t, price in enumerate(closes):
        target = signals[t - 1] if t > 0 else 0  # yesterday's decision, filled at today's close
        if target == 1 and shares == 0:
            qty = int(cash // price)
            while qty > 0 and qty * price + order_cost(qty, price, "BUY", costs) > cash:
                qty -= 1
            if qty > 0:
                cost = order_cost(qty, price, "BUY", costs)
                cash -= qty * price + cost
                shares = qty
                trades.append(Trade(t, "BUY", qty, price, cost))
        elif target == 0 and shares > 0:
            cost = order_cost(shares, price, "SELL", costs)
            cash += shares * price - cost
            trades.append(Trade(t, "SELL", shares, price, cost))
            shares = 0
        equity.append(cash + shares * price)
    return Result(equity=equity, trades=trades, costs=sum(tr.cost for tr in trades))


def max_drawdown(equity: list[float]) -> float:
    peak, worst = equity[0], 0.0
    for value in equity:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1)
    return worst


def sharpe(equity: list[float]) -> float:
    """Annualised Sharpe of daily returns, risk-free rate 0."""
    rets = [b / a - 1 for a, b in zip(equity, equity[1:])]
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return 0.0 if var == 0 else mean / math.sqrt(var) * math.sqrt(TRADING_DAYS)


def cagr(equity: list[float]) -> float:
    years = (len(equity) - 1) / TRADING_DAYS
    return (equity[-1] / equity[0]) ** (1 / years) - 1 if years > 0 and equity[0] > 0 else 0.0


def summarize(result: Result) -> dict:
    return {"total_return": result.equity[-1] / result.equity[0] - 1, "cagr": cagr(result.equity),
            "sharpe": sharpe(result.equity), "max_drawdown": max_drawdown(result.equity),
            "orders": len(result.trades), "costs": result.costs}


def shuffled_closes(closes: list[float], rng: random.Random) -> list[float]:
    """Same daily returns, random order: keeps the distribution and drift, destroys any serial structure."""
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:])]
    rng.shuffle(rets)
    out = [closes[0]]
    for r in rets:
        out.append(out[-1] * math.exp(r))
    return out


def negative_control(closes: list[float], strategy: Strategy, costs: Costs, n: int = 200, seed: int = 1) -> dict:
    """Where does the real Sharpe rank among n shuffled-order versions of the same data?

    beat_pct = share of shuffles the real run beats. A strategy with no real edge sits near 50. A high number
    means the strategy likes the real order of returns; it is NOT proof of an edge (shuffling also removes
    volatility clustering, which trend rules can exploit without predicting anything).
    """
    rng = random.Random(seed)
    real = sharpe(backtest(closes, strategy(closes), costs).equity)
    fakes = []
    for _ in range(n):
        path = shuffled_closes(closes, rng)
        fakes.append(sharpe(backtest(path, strategy(path), costs).equity))
    beat = sum(1 for f in fakes if real > f)
    return {"real_sharpe": real, "shuffled_mean": sum(fakes) / n, "shuffled_max": max(fakes),
            "beat_pct": 100.0 * beat / n, "n": n}
