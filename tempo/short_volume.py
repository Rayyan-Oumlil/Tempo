"""Unusual daily short selling on the S&P 500 (evidence/short_volume_forward.json), recorded as forward signals.

Usage: python -m tempo.short_volume      after the FINRA file is out (the late job runs it from 19:15 ET); needs Gateway.

For each stock: z-score of today's short-volume ratio against its own previous 20 sessions. The 10 highest z (liquid
stocks only) get short signals, the 10 lowest get long signals. Entry is the next session's open; primary horizon 5.
"""
from __future__ import annotations

import statistics
import sys
from datetime import date, datetime
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo

from tempo.daybars import day_bars, liquid, load_universe
from tempo.hours import is_trading_day
from tempo.ledger import Ledger, SignalRefused
from tempo.snapshots import load_short_volume, trading_days_back

SOURCE = "short_volume_v1"
UNIVERSE = "evidence/universe_sp500_20261111.txt"
BASELINE_DAYS = 20
MIN_BASELINE = 15
SD_FLOOR = 0.02
MIN_TOTAL_VOLUME = 100_000
MIN_SCORABLE = 100
CANDIDATES_PER_SIDE = 30
N_EACH = 10
ROUND_TRIP_COST = 0.002
ET = ZoneInfo("America/New_York")


def ratio(short_total: tuple[float, float]) -> float | None:
    short, total = short_total
    return short / total if total > 0 else None


def zscores(today: Mapping[str, tuple[float, float]], history: Sequence[Mapping[str, tuple[float, float]]],
            symbols: Sequence[str]) -> dict[str, float]:
    """symbol -> z of today's ratio against that symbol's own ratios in `history` (the previous sessions)."""
    out: dict[str, float] = {}
    for s in symbols:
        if s not in today or today[s][1] < MIN_TOTAL_VOLUME:
            continue
        r_today = ratio(today[s])
        past = [r for day in history if s in day and (r := ratio(day[s])) is not None]
        if r_today is None or len(past) < MIN_BASELINE:
            continue
        out[s] = (r_today - statistics.fmean(past)) / max(statistics.pstdev(past), SD_FLOOR)
    return out


def candidates(z: Mapping[str, float], per_side: int = CANDIDATES_PER_SIDE) -> tuple[list[str], list[str]]:
    """(longs, shorts) in order of conviction: lowest z first for longs, highest z first for shorts; ties by symbol."""
    if len(z) < MIN_SCORABLE:
        return [], []
    longs = sorted(z, key=lambda s: (z[s], s))[:per_side]
    shorts = sorted(z, key=lambda s: (-z[s], s))[:per_side]
    return longs, shorts


def record_signals(picks: list[tuple[str, int]], info: Mapping[str, dict], day: date, ledger: Ledger) -> list[dict]:
    recorded = []
    for symbol, direction in picks:
        try:
            recorded.append(ledger.record_signal(
                source=SOURCE, symbol=symbol, direction=direction, event_id=day.strftime("%Y%m%d"), price=info[symbol]["close"],
                features={"round_trip_cost": ROUND_TRIP_COST, "z": round(info[symbol]["z"], 3)}))
        except SignalRefused:
            continue
    return recorded


def run(now: datetime, ib, ledger: Ledger, say=print) -> int:  # pragma: no cover - glue, exercised live
    from tempo.earnings_reaction import ready_to_record
    day = now.astimezone(ET).date()
    if not is_trading_day(day):
        say(f"short volume: {day} is not a trading day; nothing to do")
        return 0
    if not ready_to_record(now, day):
        say("not recording: short-volume signals are only recorded on the signal day, after the FINRA file is out")
        return 0
    today = load_short_volume(day)
    if today is None:
        say(f"[FAIL] no FINRA short-volume file saved for {day} yet (run tempo.snapshots first; it may not be published)")
        return 1
    past_days = [d for d in trading_days_back(day, BASELINE_DAYS + 1)[:-1]]
    history = [h for d in past_days if (h := load_short_volume(d)) is not None]
    z = zscores(today, history, load_universe(UNIVERSE))
    longs, shorts = candidates(z)
    counts = {"history_days": len(history), "usable_z": len(z), "no_bar": 0, "short_history": 0, "filtered": 0}
    info: dict[str, dict] = {}

    def take(side: list[str]) -> list[str]:
        kept: list[str] = []
        for symbol in side:
            if len(kept) == N_EACH:
                break
            bars = day_bars(ib, symbol, "2 M")
            m = liquid(bars, day.isoformat()) if bars else {"status": "no_bar"}
            if m["status"] != "ok":
                counts[m["status"]] += 1
                continue
            info[symbol] = {"close": m["close"], "z": z[symbol]}
            kept.append(symbol)
        return kept

    picks = [(s, 1) for s in take(longs)] + [(s, -1) for s in take(shorts)]
    recorded = record_signals(picks, info, day, ledger)
    say(f"short volume {day}: {counts}; new signals recorded: {len(recorded)}")
    for r in recorded:
        say(f"  {r['symbol']:<6} {'LONG ' if r['direction'] == 1 else 'SHORT'} z {r['features']['z']:+.2f}")
    if not z:
        say("[FAIL] no usable z-scores: baseline files missing (run tempo.snapshots to backfill)")
        return 1
    return 0


def main() -> int:  # pragma: no cover - entry point
    from dotenv import load_dotenv

    from tempo.config import load_config
    from tempo.ibkr import connect

    load_dotenv()
    ib = connect(load_config())
    ib.RequestTimeout = 30
    try:
        return run(datetime.now(ET), ib, Ledger())
    finally:
        ib.disconnect()


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    try:
        raise SystemExit(main())
    except Exception as err:  # noqa: BLE001 - fail loudly with a clear line, non-zero exit
        print(f"[FAIL] {type(err).__name__}: {err}", file=sys.stderr)
        raise SystemExit(1)
