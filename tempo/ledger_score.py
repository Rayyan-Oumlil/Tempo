"""Score the ledger's signals against what actually happened.

Usage: python -m tempo.ledger_score      (needs IB Gateway; read-only; downloads recent daily bars for the symbols)

Each symbol and SPY are fetched once (daily bars for the dates and the beta, 5-minute bars for the executable entry and
exit prices; see exec_score.py). A signal that cannot be scored yet (the horizon has not elapsed, a bar or the beta
history is missing) is left alone and reported as waiting; scores already written are never rewritten.
"""
from __future__ import annotations

import sys
from typing import Callable

from tempo.data import Bars, drop_incomplete_today_bars
from tempo.exec_score import Intraday, score_signal_exec
from tempo.hours import EASTERN
from tempo.ledger import HORIZONS, Ledger, unscored

BENCHMARK = "SPY"


DAILY_DURATION = "6 M"      # about 125 sessions: 60 for the beta before the entry day, plus the horizon
INTRADAY_DURATION = "2 M"


def score_pending(ledger: Ledger, get_bars: Callable[[str], Bars | None], get_intraday: Callable[[str], Intraday | None],
                  horizons: tuple[int, ...] = HORIZONS) -> tuple[int, int]:
    """Returns (scores written, scores still waiting for more days or data)."""
    todo = unscored(ledger, horizons)
    if not todo:
        return 0, 0
    daily_cache: dict[str, Bars | None] = {}
    intraday_cache: dict[str, Intraday | None] = {}

    def bars_for(symbol: str) -> Bars | None:
        if symbol not in daily_cache:
            daily_cache[symbol] = get_bars(symbol)
        return daily_cache[symbol]

    def intraday_for(symbol: str) -> Intraday | None:
        if symbol not in intraday_cache:
            intraday_cache[symbol] = get_intraday(symbol)
        return intraday_cache[symbol]

    bench, bench_intra = bars_for(BENCHMARK), intraday_for(BENCHMARK)
    fresh, waiting = [], 0
    for signal, horizon in todo:
        stock, stock_intra = bars_for(signal["symbol"]), intraday_for(signal["symbol"])
        if stock is None or bench is None or stock_intra is None or bench_intra is None:
            waiting += 1
            continue
        score = score_signal_exec(signal, stock, bench, stock_intra, bench_intra, horizon)
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
    raw = ib.reqHistoricalData(contract, "", DAILY_DURATION, "1 day", "ADJUSTED_LAST", useRTH=True, formatDate=1)
    if not raw:
        return None
    bars = Bars([str(b.date) for b in raw], [b.open for b in raw], [b.high for b in raw], [b.low for b in raw], [b.close for b in raw])
    return drop_incomplete_today_bars(bars)


def ibkr_intraday(ib, symbol: str) -> Intraday | None:
    """Open of every 5-minute regular-hours bar for the last two months, keyed by New York date and start time."""
    from datetime import datetime

    from ib_async import Stock
    contract = Stock(symbol, "SMART", "USD")
    if not ib.qualifyContracts(contract):
        return None
    raw = ib.reqHistoricalData(contract, "", INTRADAY_DURATION, "5 mins", "TRADES", useRTH=True, formatDate=1)
    if not raw:
        return None
    opens: dict[tuple[str, str], float] = {}
    for b in raw:
        stamp = b.date if isinstance(b.date, datetime) else datetime.strptime(str(b.date)[:19], "%Y-%m-%d %H:%M:%S")
        stamp = stamp.astimezone(EASTERN) if stamp.tzinfo else stamp
        opens[(stamp.strftime("%Y-%m-%d"), stamp.strftime("%H:%M"))] = float(b.open)
    return Intraday(opens)


def main() -> int:
    from dotenv import load_dotenv

    from tempo.config import load_config
    from tempo.ibkr import connect

    load_dotenv()
    ib = connect(load_config())
    ib.RequestTimeout = 60
    try:
        written, waiting = score_pending(Ledger(), lambda s: ibkr_bars(ib, s), lambda s: ibkr_intraday(ib, s))
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
