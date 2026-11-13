"""Daily bars with volume, the liquidity filter shared by the evening sources, and the frozen universe file."""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MIN_PRICE = 5.0
MIN_ADV = 5_000_000.0
ADV_DAYS = 20


@dataclass(frozen=True)
class DayBars:
    dates: list[str]
    close: list[float]
    volume: list[float]


def vol20(bars: DayBars, i: int) -> float | None:
    """Standard deviation of the 20 daily returns that end the session BEFORE bar i (the event day is excluded on purpose: this is the
    state going into the event, a conditioning feature, not the event). None if fewer than 21 closes exist."""
    if i < ADV_DAYS + 1:
        return None
    closes = bars.close[i - ADV_DAYS - 1:i]
    return statistics.stdev(closes[n] / closes[n - 1] - 1 for n in range(1, len(closes)))


def liquid(bars: DayBars, day: str) -> dict[str, Any]:
    """Close of `day` and the average dollar volume of the 20 sessions before it; status ok/no_bar/short_history/filtered."""
    if day not in bars.dates:
        return {"status": "no_bar"}
    i = bars.dates.index(day)
    if i < ADV_DAYS:
        return {"status": "short_history"}
    adv = sum(bars.close[n] * bars.volume[n] for n in range(i - ADV_DAYS, i)) / ADV_DAYS
    close = bars.close[i]
    return {"status": "ok" if close >= MIN_PRICE and adv >= MIN_ADV else "filtered", "close": close, "adv20": adv, "vol20": vol20(bars, i)}


def day_bars(ib, symbol: str, duration: str = "3 M") -> DayBars | None:  # pragma: no cover - IBKR
    from ib_async import Stock
    contract = Stock(symbol, "SMART", "USD")
    if not ib.qualifyContracts(contract):
        return None
    raw = ib.reqHistoricalData(contract, "", duration, "1 day", "TRADES", useRTH=True, formatDate=1)
    if not raw:
        return None
    return DayBars([str(b.date) for b in raw], [float(b.close) for b in raw], [float(b.volume) for b in raw])


def load_universe(path: str | Path) -> list[str]:
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
