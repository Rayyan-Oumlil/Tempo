"""Daily price history for backtests: download once from IBKR (free, no subscription), keep as CSV.

Usage: python -m tempo.data SYMBOL [YEARS]            (default 20 years; saved to data/SYMBOL_1d.csv, closes only; read-only)
       python -m tempo.data SYMBOL [YEARS] --ohlc     (saved to data/SYMBOL_ohlc.csv with open, high, low, close)

Bars are ADJUSTED_LAST (adjusted for splits and dividends), so a buy-and-hold backtest approximates total return.
"""
from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from ib_async import Stock

from tempo.config import load_config
from tempo.ibkr import connect

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def csv_path(symbol: str) -> Path:
    return DATA_DIR / f"{symbol}_1d.csv"


def ohlc_path(symbol: str) -> Path:
    return DATA_DIR / f"{symbol}_ohlc.csv"


@dataclass(frozen=True)
class Bars:
    dates: list[str]
    open: list[float]
    high: list[float]
    low: list[float]
    close: list[float]


OHLC_TOLERANCE = 1e-4  # adjusted prices are rounded, so a bar may break high >= close by a hair; more than this is bad data


def drop_incomplete_today_bars(bars: Bars, today: date | None = None) -> Bars:
    """IBKR returns the session in progress as the newest daily bar. It is not a finished bar: drop it."""
    if bars.dates and bars.dates[-1] >= (today or date.today()).isoformat():
        return Bars(bars.dates[:-1], bars.open[:-1], bars.high[:-1], bars.low[:-1], bars.close[:-1])
    return bars


def save_ohlc(path: Path, rows: list[tuple[str, float, float, float, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close"])
        w.writerows(rows)


def load_ohlc(path: Path) -> Bars:
    with Path(path).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    bars = Bars(dates=[r["date"] for r in rows], open=[float(r["open"]) for r in rows], high=[float(r["high"]) for r in rows],
                low=[float(r["low"]) for r in rows], close=[float(r["close"]) for r in rows])
    if bars.dates != sorted(bars.dates):
        raise ValueError(f"{path}: dates are not sorted")
    if any(v <= 0 for series in (bars.open, bars.high, bars.low, bars.close) for v in series):
        raise ValueError(f"{path}: prices must be positive")
    tol = 1 + OHLC_TOLERANCE
    for d, o, h, lo, c in zip(bars.dates, bars.open, bars.high, bars.low, bars.close):
        if h * tol < max(o, c, lo) or lo > min(o, c, h) * tol:
            raise ValueError(f"{path}: impossible bar on {d} (open {o}, high {h}, low {lo}, close {c})")
    return bars


def save_bars(path: Path, rows: list[tuple[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "close"])
        w.writerows(rows)


def load_closes(path: Path) -> tuple[list[str], list[float]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    dates = [r["date"] for r in rows]
    closes = [float(r["close"]) for r in rows]
    if dates != sorted(dates):
        raise ValueError(f"{path}: dates are not sorted")
    if any(c <= 0 for c in closes):
        raise ValueError(f"{path}: closes must be positive")
    return dates, closes


def main(symbol: str, years: int, ohlc: bool = False) -> int:
    load_dotenv()
    ib = connect(load_config())
    ib.RequestTimeout = 60
    try:
        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        bars = ib.reqHistoricalData(contract, "", f"{years} Y", "1 day", "ADJUSTED_LAST", useRTH=True, formatDate=1)
    finally:
        ib.disconnect()
    if not bars:
        raise RuntimeError(f"No daily bars returned for {symbol}")
    if ohlc:
        save_ohlc(ohlc_path(symbol), [(str(b.date), b.open, b.high, b.low, b.close) for b in bars])
        path = ohlc_path(symbol)
    else:
        save_bars(csv_path(symbol), [(str(b.date), b.close) for b in bars])
        path = csv_path(symbol)
    print(f"saved {len(bars)} bars for {symbol}: {bars[0].date} to {bars[-1].date} -> {path}")
    return 0


if __name__ == "__main__":
    try:
        args = [a for a in sys.argv[1:] if a != "--ohlc"]
        if not args:
            raise ValueError("usage: python -m tempo.data SYMBOL [YEARS] [--ohlc]")
        raise SystemExit(main(args[0].upper(), int(args[1]) if len(args) > 1 else 20, ohlc="--ohlc" in sys.argv))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
