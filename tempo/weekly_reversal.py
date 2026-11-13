"""Weekly short-term reversal on the S&P 500 (evidence/weekly_reversal_forward.json), recorded as forward signals.

Usage: python -m tempo.weekly_reversal      after 16:20 ET (the evening job runs it daily; it acts only on the last
trading day of the week); needs Gateway.

Each week: the 10 stocks with the lowest 5-session return minus SPY's get long signals, the 10 with the highest get
short signals, among liquid universe stocks. Entry is the next session's open; primary horizon 5 sessions.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from tempo.daybars import DayBars, day_bars, liquid, load_universe
from tempo.hours import is_trading_day
from tempo.ledger import Ledger, SignalRefused
from tempo.snapshots import Borrow, context_features, load_shortstock

SOURCE = "weekly_reversal_v1"
UNIVERSE = "evidence/universe_sp500_20261111.txt"
N_EACH = 10
MIN_SCORABLE = 40
LOOKBACK = 5
ROUND_TRIP_COST = 0.002
ET = ZoneInfo("America/New_York")


def is_week_end(day: date) -> bool:
    if not is_trading_day(day):
        return False
    d = day + timedelta(days=1)
    while d.isocalendar()[1] == day.isocalendar()[1]:
        if is_trading_day(d):
            return False
        d += timedelta(days=1)
    return True


def r5(stock: DayBars, spy: DayBars, day: str) -> float | None:
    if day not in stock.dates or day not in spy.dates:
        return None
    i = stock.dates.index(day)
    if i < LOOKBACK:
        return None
    then = stock.dates[i - LOOKBACK]
    if then not in spy.dates:
        return None
    j, k = spy.dates.index(day), spy.dates.index(then)
    return (stock.close[i] / stock.close[i - LOOKBACK] - 1) - (spy.close[j] / spy.close[k] - 1)


def pick(moves: dict[str, float], n: int = N_EACH) -> tuple[list[str], list[str]]:
    if len(moves) < MIN_SCORABLE:
        return [], []
    ranked = sorted(moves, key=lambda s: (moves[s], s))
    longs = ranked[:n]
    shorts = sorted(moves, key=lambda s: (-moves[s], s))[:n]
    return longs, shorts


def record_signals(longs: list[str], shorts: list[str], info: dict[str, dict], day: date, ledger: Ledger,
                   borrow: dict[str, Borrow] | None = None) -> list[dict]:
    recorded = []
    for symbol, direction in [(s, 1) for s in longs] + [(s, -1) for s in shorts]:
        try:
            recorded.append(ledger.record_signal(
                source=SOURCE, symbol=symbol, direction=direction, event_id=day.strftime("%Y%m%d"), price=info[symbol]["close"],
                features={"round_trip_cost": ROUND_TRIP_COST, "r5": round(info[symbol]["r5"], 5),
                          **context_features(info[symbol], borrow, symbol)}))
        except SignalRefused:
            continue
    return recorded


def run(now: datetime, ib, ledger: Ledger, say=print) -> int:  # pragma: no cover - glue, exercised live
    from tempo.earnings_reaction import ready_to_record
    day = now.astimezone(ET).date()
    if not is_week_end(day):
        say(f"weekly reversal: {day} is not the last trading day of its week; nothing to do")
        return 0
    if not ready_to_record(now, day):
        say("not recording: weekly reversal signals are only recorded on the week's last trading day after 16:20 ET")
        return 0
    spy = day_bars(ib, "SPY", "2 M")
    if spy is None:
        raise RuntimeError("no SPY bars from IBKR")
    counts = {"symbols": 0, "no_bar": 0, "short_history": 0, "filtered": 0, "scorable": 0}
    info: dict[str, dict] = {}
    for symbol in load_universe(UNIVERSE):
        counts["symbols"] += 1
        bars = day_bars(ib, symbol, "2 M")
        m = liquid(bars, day.isoformat()) if bars else {"status": "no_bar"}
        move = r5(bars, spy, day.isoformat()) if bars and m["status"] == "ok" else None
        if m["status"] != "ok":
            counts[m["status"]] += 1
            continue
        if move is None:
            counts["short_history"] += 1
            continue
        counts["scorable"] += 1
        info[symbol] = {"close": m["close"], "r5": move, "vol20": m["vol20"]}
    longs, shorts = pick({s: v["r5"] for s, v in info.items()})
    recorded = record_signals(longs, shorts, info, day, ledger, load_shortstock(day))
    say(f"weekly reversal {day}: {counts}; new signals recorded: {len(recorded)}")
    for r in recorded:
        say(f"  {r['symbol']:<6} {'LONG ' if r['direction'] == 1 else 'SHORT'} r5 {r['features']['r5']:+.1%}")
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
