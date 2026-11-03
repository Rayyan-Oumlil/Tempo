"""Score the ledger's signals against what actually happened.

Usage: python -m tempo.ledger_score      (needs IB Gateway; read-only; downloads recent daily bars for the symbols)

Each symbol and SPY are fetched once. A signal that cannot be scored yet (the horizon has not elapsed, or the
benchmark lacks the days) is left alone and reported as waiting; scores already written are never rewritten.
"""
from __future__ import annotations

import sys
from typing import Callable

from tempo.data import Bars, drop_incomplete_today_bars
from tempo.ledger import HORIZONS, Ledger, score_signal, unscored

BENCHMARK = "SPY"


def score_pending(ledger: Ledger, get_bars: Callable[[str], Bars | None], horizons: tuple[int, ...] = HORIZONS) -> tuple[int, int]:
    """Returns (scores written, scores still waiting for more days or data)."""
    todo = unscored(ledger, horizons)
    if not todo:
        return 0, 0
    cache: dict[str, Bars | None] = {}

    def bars_for(symbol: str) -> Bars | None:
        if symbol not in cache:
            cache[symbol] = get_bars(symbol)
        return cache[symbol]

    bench = bars_for(BENCHMARK)
    fresh, waiting = [], 0
    for signal, horizon in todo:
        stock = bars_for(signal["symbol"])
        score = score_signal(signal, stock, bench, horizon) if stock is not None and bench is not None else None
        if score is None:
            waiting += 1
        else:
            fresh.append(score)
    return ledger.record_scores(fresh), waiting


def ibkr_bars(ib, symbol: str) -> Bars | None:
    """Recent finished daily bars for a US stock, or None if IBKR has none."""
    from ib_async import Stock
    contract = Stock(symbol, "SMART", "USD")
    if not ib.qualifyContracts(contract):
        return None
    raw = ib.reqHistoricalData(contract, "", "2 M", "1 day", "ADJUSTED_LAST", useRTH=True, formatDate=1)
    if not raw:
        return None
    bars = Bars([str(b.date) for b in raw], [b.open for b in raw], [b.high for b in raw], [b.low for b in raw], [b.close for b in raw])
    return drop_incomplete_today_bars(bars)


def main() -> int:
    from dotenv import load_dotenv

    from tempo.config import load_config
    from tempo.ibkr import connect

    load_dotenv()
    ib = connect(load_config())
    ib.RequestTimeout = 60
    try:
        written, waiting = score_pending(Ledger(), lambda s: ibkr_bars(ib, s))
    finally:
        ib.disconnect()
    print(f"scores written: {written}; still waiting: {waiting}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConnectionError, RuntimeError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
