"""Low-exposure mean reversion on daily bars: RSI(2) with a trend filter, and internal bar strength (IBS).

Rules are fixed in evidence/mean_reversion_etf.json. Signals are decided from data through day t's close. The honest
fill is the NEXT open (a market-on-open order); `fill="same_close"` is the optimistic reference the literature
usually assumes, kept only to show how much of a result depends on an unachievable fill.
"""
from __future__ import annotations

import random

from tempo.backtest import Costs, Result, Trade, order_cost
from tempo.data import Bars


def sma(values: list[float], n: int) -> list[float | None]:
    return [None if t + 1 < n else sum(values[t + 1 - n:t + 1]) / n for t in range(len(values))]


def _rsi_value(avg_gain: float, avg_loss: float) -> float | None:
    if avg_loss == 0:
        return None if avg_gain == 0 else 100.0
    return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)


def rsi(closes: list[float], period: int = 2) -> list[float | None]:
    """Wilder's RSI: the first average is the simple mean of the first `period` changes, then Wilder smoothing.
    None until there are `period` changes, and None when the market has not moved at all."""
    out: list[float | None] = [None] * len(closes)
    if len(closes) <= period:
        return out
    gains = [max(b - a, 0.0) for a, b in zip(closes, closes[1:])]
    losses = [max(a - b, 0.0) for a, b in zip(closes, closes[1:])]
    avg_gain, avg_loss = sum(gains[:period]) / period, sum(losses[:period]) / period
    out[period] = _rsi_value(avg_gain, avg_loss)
    for t in range(period + 1, len(closes)):
        avg_gain = (avg_gain * (period - 1) + gains[t - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[t - 1]) / period
        out[t] = _rsi_value(avg_gain, avg_loss)
    return out


def ibs(highs: list[float], lows: list[float], closes: list[float]) -> list[float | None]:
    """Internal bar strength: where the close sits in the day's range (0 = at the low, 1 = at the high)."""
    return [None if h == lo else (c - lo) / (h - lo) for h, lo, c in zip(highs, lows, closes)]


def rsi2_signals(closes: list[float], trend: int = 200, exit_sma: int = 5, entry: float = 10.0) -> list[int]:
    """1 = long after this close. Enter when close > SMA(trend) and RSI(2) < entry; exit when close > SMA(exit_sma)."""
    r, slow, fast = rsi(closes, 2), sma(closes, trend), sma(closes, exit_sma)
    pos, out = 0, []
    for t, close in enumerate(closes):
        if slow[t] is None:
            pos = 0
        elif pos == 0:
            if r[t] is not None and close > slow[t] and r[t] < entry:
                pos = 1
        elif fast[t] is not None and close > fast[t]:
            pos = 0
        out.append(pos)
    return out


def ibs_signals(highs: list[float], lows: list[float], closes: list[float], entry: float = 0.2, exit_: float = 0.8) -> list[int]:
    pos, out = 0, []
    for value in ibs(highs, lows, closes):
        if value is not None:
            if pos == 0 and value < entry:
                pos = 1
            elif pos == 1 and value > exit_:
                pos = 0
        out.append(pos)
    return out


def run_longflat(opens: list[float], closes: list[float], signals: list[int], costs: Costs, capital: float,
                 fill: str = "next_open") -> Result:
    """All-in long or flat in whole shares, cash idle at 0. equity[t] is valued at day t's close.

    next_open: yesterday's signal is filled at today's open. same_close: today's signal is filled at today's close.
    """
    if fill not in ("next_open", "same_close"):
        raise ValueError(f"unknown fill rule {fill!r}")
    cash, shares = capital, 0
    equity: list[float] = []
    trades: list[Trade] = []
    for t in range(len(closes)):
        if fill == "next_open":
            target, price = (signals[t - 1] if t > 0 else 0), opens[t]
        else:
            target, price = signals[t], closes[t]
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
        equity.append(cash + shares * closes[t])
    return Result(equity=equity, trades=trades, costs=sum(tr.cost for tr in trades))


def days_invested(trades: list[Trade], n_days: int) -> int:
    """Number of daily closes at which a position was held (a buy at day b sold at day s counts s - b days)."""
    total, entered = 0, None
    for tr in trades:
        if tr.side == "BUY":
            entered = tr.day
        elif entered is not None:
            total += tr.day - entered
            entered = None
    return total + (n_days - entered if entered is not None else 0)


def shuffle_bars(bars: Bars, rng: random.Random) -> Bars:
    """Shuffle the order of days as whole bars. Each day's gap from the previous close, high, low and close (relative
    to its open) travel together, so every bar stays valid and the return distribution is unchanged, but serial
    structure, which mean reversion needs, is destroyed. The first bar is kept as the starting point."""
    shapes = [(bars.open[t] / bars.close[t - 1], bars.high[t] / bars.open[t], bars.low[t] / bars.open[t], bars.close[t] / bars.open[t])
              for t in range(1, len(bars.close))]
    rng.shuffle(shapes)
    o, h, lo, c = [bars.open[0]], [bars.high[0]], [bars.low[0]], [bars.close[0]]
    for gap, hi, low, cl in shapes:
        op = c[-1] * gap
        o.append(op), h.append(op * hi), lo.append(op * low), c.append(op * cl)
    return Bars(list(bars.dates), o, h, lo, c)
