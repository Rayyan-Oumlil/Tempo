"""Print-only daily X4 check (plan v2, Workstream Y rule 1): BTC close > 100-day SMA, sized to a 40% volatility target, 0.10 band.

Places no order and imports no broker code. It reads BTC-USD daily closes from Yahoo (or a CSV), uses only COMPLETED UTC days,
and prints the decided weight plus, if a budget is given, the USD notional and BTC quantity that weight means.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
import urllib.request
from dataclasses import dataclass

import pandas as pd

from tempo import history_y as y


@dataclass(frozen=True)
class X4Signal:
    as_of: str
    close: float
    sma100: float
    vol30: float
    signal_on: bool
    target_weight: float
    changed_today: bool


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
    )


def fetch_closes(symbol: str = "BTC-USD") -> pd.Series:  # pragma: no cover - network
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1=0&period2={now}&interval=1d"
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
    d = json.loads(raw)["chart"]["result"][0]
    idx = pd.to_datetime([dt.datetime.fromtimestamp(t, dt.timezone.utc).date() for t in d["timestamp"]])
    s = pd.Series(d["indicators"]["adjclose"][0]["adjclose"], index=idx, dtype="float64").dropna()
    today = pd.Timestamp(dt.datetime.now(dt.timezone.utc).date())
    return s[s.index < today]  # the current UTC day is still open


def describe(sig: X4Signal, budget_usd: float | None) -> str:
    lines = [
        f"X4 as of {sig.as_of} (last completed UTC day)",
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
