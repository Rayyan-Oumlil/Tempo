"""Print-only daily X4 check (plan v2, Workstream Y rule 1): BTC close > 100-day SMA, sized to a 40% volatility target, 0.10 band.

Places no order and imports no broker code. It reads BTC-USD daily closes from Yahoo (or a CSV), uses only COMPLETED UTC days,
and prints the decided weight plus, if a budget is given, the USD notional and BTC quantity that weight means.

Yahoo leaves yesterday's daily close empty for hours after 00:00 UTC. For that one day only, the close of Yahoo's own 23:00 UTC
hourly bar is used (measured 2026-11-28 over 91 days: median gap to the daily close 0.017%, max 0.19%), and the signal says so.
Without that bar the series stays one day short and the trader refuses. The frozen X4 rule is unchanged.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from tempo import history_y as y

DAILY_SOURCE, HOURLY_SOURCE = "yahoo daily", "yahoo 23:00 UTC hourly"
SOURCE_ATTR = "last_close_source"


@dataclass(frozen=True)
class X4Signal:
    as_of: str
    close: float
    sma100: float
    vol30: float
    signal_on: bool
    target_weight: float
    changed_today: bool
    close_source: str = DAILY_SOURCE


def compute_signal(close: pd.Series) -> X4Signal:
    """Replays the frozen X4 weight path over the whole history, so the band state is exactly the backtest's."""
    if len(close) < y.X4_SMA + y.X4_VOL_WINDOW:
        raise ValueError(f"need at least {y.X4_SMA + y.X4_VOL_WINDOW} daily closes, got {len(close)}")
    weights = y.x4_weights(close.rename("BTC-USD")).iloc[:, 0]
    sma = float(close.rolling(y.X4_SMA).mean().iloc[-1])
    vol = float(close.pct_change().rolling(y.X4_VOL_WINDOW).std().iloc[-1] * math.sqrt(365))
    return X4Signal(
        as_of=close.index[-1].strftime("%Y-%m-%d"),
        close=float(close.iloc[-1]),
        sma100=sma,
        vol30=vol,
        signal_on=bool(close.iloc[-1] > sma),
        target_weight=float(weights.iloc[-1]),
        changed_today=bool(len(weights) > 1 and weights.iloc[-1] != weights.iloc[-2]),
        close_source=close.attrs.get(SOURCE_ATTR, DAILY_SOURCE),
    )


def _utc_date(ts: int) -> dt.date:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).date()


def parse_closes(daily: dict, load_hourly: Callable[[], dict], today: dt.date) -> pd.Series:
    """Completed-day closes from a Yahoo daily chart; yesterday is taken from the hourly chart if the daily one lacks it."""
    idx = pd.to_datetime([_utc_date(ts) for ts in daily["timestamp"]])
    s = pd.Series(daily["indicators"]["adjclose"][0]["adjclose"], index=idx, dtype="float64").dropna()
    s = s[s.index < pd.Timestamp(today)]  # the current UTC day is still open
    s.attrs[SOURCE_ATTR] = DAILY_SOURCE
    yesterday = pd.Timestamp(today - dt.timedelta(days=1))
    if yesterday in s.index:
        return s
    hourly = load_hourly()
    final_bar = int(dt.datetime.combine(yesterday.date(), dt.time(23), dt.timezone.utc).timestamp())
    close = dict(zip(hourly["timestamp"], hourly["indicators"]["quote"][0]["close"])).get(final_bar)
    if close is None:
        return s
    filled = pd.concat([s, pd.Series([close], index=[yesterday], dtype="float64")])
    filled.attrs[SOURCE_ATTR] = HOURLY_SOURCE
    return filled


def _chart(symbol: str, query: str) -> dict:  # pragma: no cover - network
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{query}"
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
    return json.loads(raw)["chart"]["result"][0]


def fetch_closes(symbol: str = "BTC-USD") -> pd.Series:  # pragma: no cover - network
    now = dt.datetime.now(dt.timezone.utc)
    daily = _chart(symbol, f"period1=0&period2={int(now.timestamp())}&interval=1d")
    return parse_closes(daily, lambda: _chart(symbol, "range=5d&interval=1h"), now.date())


def describe(sig: X4Signal, budget_usd: float | None) -> str:
    lines = [
        f"X4 as of {sig.as_of} (last completed UTC day), last close from {sig.close_source}",
        f"  BTC close {sig.close:,.2f}   SMA100 {sig.sma100:,.2f}   30d vol {sig.vol30:.0%} annualised",
        f"  signal: {'ON (close above SMA100)' if sig.signal_on else 'OFF (close at or below SMA100)'}",
        f"  decided target weight: {sig.target_weight:.0%} of the sleeve{'  (CHANGED today)' if sig.changed_today else ''}",
    ]
    if budget_usd is not None:
        usd = sig.target_weight * budget_usd
        lines.append(f"  with a sleeve of {budget_usd:,.0f} USD: hold {usd:,.0f} USD = {usd / sig.close:.6f} BTC, rest in cash")
    lines.append("  PRINT ONLY: no order was placed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget-usd", type=float, default=None, help="size of the BTC sleeve, to print a notional")
    ap.add_argument("--csv", default=None, help="read date,close from a CSV instead of Yahoo")
    args = ap.parse_args(argv)
    close = pd.read_csv(args.csv, parse_dates=["date"]).set_index("date")["close"] if args.csv else fetch_closes()
    print(describe(compute_signal(close), args.budget_usd))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
