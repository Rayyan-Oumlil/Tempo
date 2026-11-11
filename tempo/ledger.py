"""Signal ledger: an append-only record of every call a signal source makes, scored later against what happened.

Why it exists: historical tests of text and event signals (especially LLM ones) are contaminated by look-ahead and
overfitting. A call recorded NOW, with the system clock's timestamp, and scored only against prices from the next
trading day on, cannot be either. Every forward test (insider purchases, a Claude reading of earnings releases, the
mean reversion rules) can use the same ledger.

Rules enforced here:
  * a signal is stamped with the system clock and cannot be edited or backdated (`backfill=True` records are kept
    for reference and excluded from evaluation);
  * one signal per (source, symbol, event_id);
  * scoring enters at the open of the first trading day STRICTLY AFTER the signal's New York date, holds `horizon`
    trading days, exits at the close, and is measured against SPY over the same days;
  * no verdict is printed before MIN_SCORED scored signals exist for a source and horizon.

Usage: python -m tempo.ledger            show counts and statistics per source and horizon
       python -m tempo.ledger add SOURCE SYMBOL long|short|+1|-1 EVENT_ID --confidence 1-5 [--reason TEXT] [--url URL] [--eps X]
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from tempo.data import Bars
from tempo.journal import Journal
from tempo.overnight import t_statistic

LEDGER_FILE = Path(__file__).resolve().parents[1] / "ledger" / "ledger.jsonl"
HORIZONS = (1, 5, 21)
ROUND_TRIP_COST = 0.0006  # assumed 3 bps per side; real slippage is unmeasured (see docs/research/log.md)
MIN_SCORED = 30
NEW_YORK = ZoneInfo("America/New_York")


class SignalRefused(ValueError):
    """The ledger refused to record this signal. Nothing was written."""


class Ledger:
    def __init__(self, path: Path = LEDGER_FILE, clock: Callable[[], float] = time.time):
        self.journal = Journal(path, clock=clock)

    def record_signal(self, *, source: str, symbol: str, direction: int, event_id: str, features: dict | None = None,
                      price: float | None = None, backfill: bool = False) -> dict:
        if not source or not symbol or not event_id:
            raise SignalRefused("source, symbol and event_id are all required")
        if direction not in (1, -1):
            raise SignalRefused(f"direction must be 1 (long) or -1 (short), got {direction!r}")
        signal_id = f"{source}:{symbol}:{event_id}"
        with self.journal.lock():  # the duplicate check and the write are one step
            if any(r.get("signal_id") == signal_id for r in self.journal.records() if r["kind"] == "signal"):
                raise SignalRefused(f"{signal_id} already recorded")
            date_et = datetime.fromtimestamp(self.journal.now(), NEW_YORK).date().isoformat()
            return self.journal.append("signal", signal_id=signal_id, source=source, symbol=symbol, direction=direction,
                                       event_id=event_id, date_et=date_et, features=features or {}, price=price,
                                       backfill=backfill)

    def signals(self, source: str | None = None, include_backfill: bool = False) -> list[dict]:
        return [r for r in self.journal.records() if r["kind"] == "signal" and (source is None or r["source"] == source)
                and (include_backfill or not r["backfill"])]

    def scores(self, source: str | None = None) -> list[dict]:
        wanted = {s["signal_id"] for s in self.signals(source)}
        return [r for r in self.journal.records() if r["kind"] == "score" and r["signal_id"] in wanted]

    def record_scores(self, scores: list[dict]) -> int:
        """Append scores not already recorded (one per signal and horizon). Returns how many were written."""
        with self.journal.lock():
            done = {(r["signal_id"], r["horizon"]) for r in self.journal.records() if r["kind"] == "score"}
            fresh = [s for s in scores if (s["signal_id"], s["horizon"]) not in done]
            for s in fresh:
                self.journal.append("score", **s)
            return len(fresh)


def score_signal(signal: dict, bars: Bars, bench: Bars, horizon: int) -> dict | None:
    """Score one signal at one horizon, or None if it cannot be scored yet (not enough days, or no benchmark days)."""
    entry = next((i for i, d in enumerate(bars.dates) if d > signal["date_et"]), None)
    if entry is None or entry + horizon - 1 >= len(bars.dates):
        return None
    exit_ = entry + horizon - 1
    entry_date, exit_date = bars.dates[entry], bars.dates[exit_]
    bench_index = {d: i for i, d in enumerate(bench.dates)}
    if entry_date not in bench_index or exit_date not in bench_index:
        return None
    d = signal["direction"]
    cost = signal["features"].get("round_trip_cost", ROUND_TRIP_COST)  # a source may declare a harsher cost (small stocks)
    ret = d * (bars.close[exit_] / bars.open[entry] - 1)
    bench_ret = d * (bench.close[bench_index[exit_date]] / bench.open[bench_index[entry_date]] - 1)
    return {"signal_id": signal["signal_id"], "source": signal["source"], "symbol": signal["symbol"], "horizon": horizon,
            "entry_date": entry_date, "exit_date": exit_date, "ret": ret, "bench_ret": bench_ret, "excess": ret - bench_ret,
            "net_excess": ret - bench_ret - cost, "round_trip_cost": cost}


def unscored(ledger: Ledger, horizons: tuple[int, ...] = HORIZONS) -> list[tuple[dict, int]]:
    done = {(r["signal_id"], r["horizon"]) for r in ledger.journal.records() if r["kind"] == "score"}
    return [(s, h) for s in ledger.signals() for h in horizons if (s["signal_id"], h) not in done]


def summarize(scores: list[dict]) -> tuple[int, float, float | None, float]:
    """(n, mean net excess return, t-statistic or None, share of positive scores)."""
    n = len(scores)
    if n == 0:
        return 0, 0.0, None, 0.0
    values = [s["net_excess"] for s in scores]
    return n, sum(values) / n, t_statistic(values) if n >= 2 else None, sum(1 for v in values if v > 0) / n


def status_line(n: int, mean: float, t: float | None, hit: float) -> str:
    text = f"n={n}, mean net excess {mean:+.2%}, hit rate {hit:.0%}" + (f", t={t:.2f}" if t is not None else "")
    return text + (f"  NOT ENOUGH SCORED SIGNALS (need {MIN_SCORED}); nothing should be concluded" if n < MIN_SCORED else "")


def power_line(values: list[float], horizon: int, per_week: float, t_target: float = 2.5) -> str:
    """How many scored signals the current mean and spread would need to reach t_target, and how long at this pace.
    An estimate from a noisy sample, not a promise: it moves as scores arrive."""
    n = len(values)
    if n < 2:
        return f"  power ({horizon}-day): too few scores to estimate"
    mean = sum(values) / n
    sd = (sum((v - mean) ** 2 for v in values) / (n - 1)) ** 0.5
    if mean <= 0 or sd == 0:
        return f"  power ({horizon}-day): n={n}, mean {mean:+.2%}: no sample size reaches t={t_target} at this effect"
    needed = math.ceil((t_target * sd / mean) ** 2)
    if n >= needed:
        return f"  power ({horizon}-day): n={n}, needs about {needed} scored for t={t_target} at this effect: already enough"
    weeks = math.ceil((needed - n) / per_week) if per_week > 0 else None
    pace = f"about {weeks} more weeks of signals at {per_week:.1f}/week, plus {horizon} trading days to score them" if weeks else "no pace yet"
    return f"  power ({horizon}-day): n={n}, needs about {needed} scored for t={t_target} at this effect: {pace}"


def _per_week(signals: list[dict]) -> float:
    if not signals:
        return 0.0
    first, last = date.fromisoformat(signals[0]["date_et"]), date.fromisoformat(signals[-1]["date_et"])
    return len(signals) / max(1.0, ((last - first).days + 1) / 7)


def report(ledger: Ledger | None = None) -> str:
    ledger = ledger or Ledger()
    sources = sorted({s["source"] for s in ledger.signals()})
    if not sources:
        return "ledger is empty: no signals recorded yet"
    lines = []
    for source in sources:
        sigs = ledger.signals(source)
        lines.append(f"{source}: {len(sigs)} signals ({sigs[0]['date_et']} to {sigs[-1]['date_et']})")
        scored = ledger.scores(source)
        for h in HORIZONS:
            lines.append(f"  {h:>2}-day: " + status_line(*summarize([s for s in scored if s["horizon"] == h])))
        primary = HORIZONS[-1]
        at = primary if sum(1 for s in scored if s["horizon"] == primary) >= 2 else HORIZONS[0]
        lines.append(power_line([s["net_excess"] for s in scored if s["horizon"] == at], at, _per_week(sigs))
                     + ("" if at == primary else "  (1-day only: indicative, not the registered horizon)"))
    return "\n".join(lines)


DIRECTIONS = {"+1": 1, "1": 1, "long": 1, "-1": -1, "short": -1}


def cli_add(argv: list[str], ledger: Ledger | None = None) -> dict:
    """Record one call from the command line (used for Claude's in-session readings)."""
    p = argparse.ArgumentParser(prog="tempo.ledger add")
    p.add_argument("source"), p.add_argument("symbol"), p.add_argument("direction"), p.add_argument("event_id")
    p.add_argument("--confidence", type=int, required=True)
    p.add_argument("--reason", default=""), p.add_argument("--url", default=""), p.add_argument("--eps", type=float)
    a = p.parse_args(argv)
    if a.direction not in DIRECTIONS:
        raise SignalRefused(f"direction must be long, short, +1 or -1, got {a.direction!r}")
    if not 1 <= a.confidence <= 5:
        raise SignalRefused(f"confidence must be 1 to 5, got {a.confidence}")
    features = {"confidence": a.confidence, "reason": a.reason, "release_url": a.url}
    if a.eps is not None:
        features["eps_estimate"] = a.eps
    return (ledger or Ledger()).record_signal(source=a.source, symbol=a.symbol, direction=DIRECTIONS[a.direction],
                                              event_id=a.event_id, features=features)


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "add":
            rec = cli_add(sys.argv[2:])
            print(f"recorded {rec['signal_id']} {'long' if rec['direction'] == 1 else 'short'} on {rec['date_et']}")
            raise SystemExit(0)
        print(report())
    except (OSError, ValueError, SignalRefused) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
