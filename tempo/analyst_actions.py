"""Analyst upgrades and downgrades (evidence/analyst_actions_forward.json), recorded as forward signals.

Usage: python -m tempo.analyst_actions      after 16:20 ET on a trading day (the evening job runs it); needs Gateway.

For every symbol of the frozen S&P 500 universe, read IBKR's free Briefing.com Analyst Actions headlines (BRFUPDN),
keep upgrades and downgrades timed between the previous close and today's close, and record a long (upgrade) or
short (downgrade) signal for liquid stocks. Entry is the next session's open, so the announcement day is not traded.
"""
from __future__ import annotations

import re
import sys
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from tempo.daybars import day_bars, liquid, load_universe
from tempo.hours import is_trading_day
from tempo.ledger import Ledger, SignalRefused

SOURCE = "analyst_actions_v1"
UNIVERSE = "evidence/universe_sp500_20261111.txt"
PROVIDER = "BRFUPDN"
PER_SYMBOL = 50
ROUND_TRIP_COST = 0.002
MAX_NEWS_FAILED_SHARE = 0.02   # more than this share of unanswered symbols means the run is incomplete: fail, do not pretend
ET = ZoneInfo("America/New_York")
CLOSE = time(16, 0)
HEADLINE = re.compile(r"^(?:\{[^}]*\})?!?(?P<firm>.+?) (?P<action>upgraded|downgraded) (?P<company>.+?) "
                      r"\((?P<symbol>[A-Z]{1,5})\) to (?P<rating>.+?)(?: with target \$(?P<target>[\d.,]+))?$")


def parse_headline(text: str) -> dict | None:
    m = HEADLINE.match(text.strip())
    if not m:
        return None
    return {"symbol": m.group("symbol"), "direction": 1 if m.group("action") == "upgraded" else -1,
            "firm": m.group("firm").strip(), "rating": m.group("rating").strip(),
            "target": float(m.group("target").replace(",", "")) if m.group("target") else None}


def _previous_trading_day(day: date) -> date:
    d = day - timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def window(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(_previous_trading_day(day), CLOSE, tzinfo=ET).astimezone(timezone.utc)
    end = datetime.combine(day, CLOSE, tzinfo=ET).astimezone(timezone.utc)
    return start, end


def _as_utc(stamp) -> datetime:
    if isinstance(stamp, str):
        stamp = datetime.strptime(stamp[:19], "%Y-%m-%d %H:%M:%S")
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def actions_in_window(symbol: str, headlines: list[tuple], day: date) -> list[dict]:
    """Every parsed upgrade/downgrade of `symbol` timed inside the signal window, in the order given."""
    start, end = window(day)
    out = []
    for stamp, text in headlines:
        p = parse_headline(text)
        if p and p["symbol"] == symbol and start < _as_utc(stamp) <= end:
            out.append(p)
    return out


def direction_for(symbol: str, headlines: list[tuple], day: date) -> int | None:
    found = {a["direction"] for a in actions_in_window(symbol, headlines, day)}
    return found.pop() if len(found) == 1 else None


def action_features(actions: list[dict], close: float) -> dict:
    """What the headlines said, kept so later analysis (tempo.autopsy, a registered challenger) can condition on it
    without a new data source: who, what rating, what target, how many firms, and the target relative to the price."""
    ups = [a["target"] / close - 1 for a in actions if a["target"]]
    return {"n_actions": len(actions), "firms": [a["firm"] for a in actions], "ratings": [a["rating"] for a in actions],
            "targets": [a["target"] for a in actions], "target_vs_price": sum(ups) / len(ups) if ups else None}


def fetch_news(ib, con_id: int) -> list | None:
    """Headlines for one stock, or None when the request failed. ib_async returns None on its hard 4 s timeout
    instead of raising, and [] for a real empty answer, so the two must not be merged with `or []`."""
    try:
        return ib.reqHistoricalNews(con_id, PROVIDER, "", "", PER_SYMBOL)
    except Exception:  # noqa: BLE001 - counted by the caller, never hidden
        return None


def record_signals(hits: list[dict], ledger: Ledger) -> list[dict]:
    recorded = []
    for h in hits:
        try:
            recorded.append(ledger.record_signal(
                source=SOURCE, symbol=h["symbol"], direction=h["direction"], event_id=h["day"].replace("-", ""),
                price=h["close"], features={"round_trip_cost": ROUND_TRIP_COST, "adv20": round(h["adv20"]),
                                            **action_features(h.get("actions", []), h["close"])}))
        except SignalRefused:
            continue
    return recorded


def run(now: datetime, ib, ledger: Ledger, say=print) -> int:  # pragma: no cover - glue, exercised live
    from ib_async import Stock

    from tempo.earnings_reaction import ready_to_record
    day = now.astimezone(ET).date()
    if not ready_to_record(now, day):
        say("not recording: analyst actions are only recorded on the signal day after 16:20 ET")
        return 0
    counts = {"symbols": 0, "not_qualified": 0, "news_failed": 0, "actions": 0, "no_bar": 0, "short_history": 0,
              "filtered": 0, "signal": 0}
    hits: list[dict] = []
    failed: list[str] = []
    for symbol in load_universe(UNIVERSE):
        counts["symbols"] += 1
        contract = Stock(symbol, "SMART", "USD")
        if not ib.qualifyContracts(contract):
            counts["not_qualified"] += 1
            continue
        news = fetch_news(ib, contract.conId)
        if news is None:   # one retry: a 4 s timeout is usually a busy moment, not a missing answer
            news = fetch_news(ib, contract.conId)
        if news is None:
            counts["news_failed"] += 1
            failed.append(symbol)
            continue
        headlines = [(n.time, n.headline) for n in news]
        direction = direction_for(symbol, headlines, day)
        if direction is None:
            continue
        counts["actions"] += 1
        bars = day_bars(ib, symbol)
        m = liquid(bars, day.isoformat()) if bars else {"status": "no_bar"}
        if m["status"] != "ok":
            counts[m["status"]] += 1
            continue
        counts["signal"] += 1
        hits.append({"symbol": symbol, "direction": direction, "day": day.isoformat(), "close": m["close"], "adv20": m["adv20"],
                     "actions": actions_in_window(symbol, headlines, day)})
    recorded = record_signals(hits, ledger)
    say(f"analyst actions {day}: {counts}; new signals recorded: {len(recorded)}")
    for r in recorded:
        say(f"  {r['symbol']:<6} {'LONG ' if r['direction'] == 1 else 'SHORT'}")
    if counts["symbols"] and len(failed) / counts["symbols"] > MAX_NEWS_FAILED_SHARE:
        say(f"[FAIL] {len(failed)} of {counts['symbols']} symbols got no news answer even after a retry: {failed[:20]}")
        return 1
    if failed:
        say(f"no news answer for {len(failed)} symbols (under the {MAX_NEWS_FAILED_SHARE:.0%} limit): {failed}")
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
