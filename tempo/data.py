"""Daily price history for backtests: download once from IBKR (free, no subscription), keep as CSV.

Usage: python -m tempo.data SYMBOL [YEARS]      (default 20 years; saved to data/SYMBOL_1d.csv; read-only)

Bars are ADJUSTED_LAST (adjusted for splits and dividends), so a buy-and-hold backtest approximates total return.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from dotenv import load_dotenv
from ib_async import Stock

from tempo.config import load_config
from tempo.ibkr import connect

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def csv_path(symbol: str) -> Path:
    return DATA_DIR / f"{symbol}_1d.csv"


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


def main(symbol: str, years: int) -> int:
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
    save_bars(csv_path(symbol), [(str(b.date), b.close) for b in bars])
    print(f"saved {len(bars)} bars for {symbol}: {bars[0].date} to {bars[-1].date} -> {csv_path(symbol)}")
    return 0


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise ValueError("usage: python -m tempo.data SYMBOL [YEARS]")
        raise SystemExit(main(sys.argv[1].upper(), int(sys.argv[2]) if len(sys.argv) > 2 else 20))
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
