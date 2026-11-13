"""Drift after a large earnings reaction in LESS liquid stocks (evidence/earnings_reaction_small_forward.json).

Usage: python -m tempo.earnings_reaction_small      after 16:20 ET on a trading day (the late job runs it); needs Gateway.

Same events and same reaction measure as earnings_reaction_v1, whose frozen code it reuses without change. Only the
liquidity band (20-day dollar volume from 500k up to, not including, 5M USD; price at least 3 USD) and the cost (60 bps)
differ, so the two sources never both take the same stock on the same day.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from typing import Any

from tempo.earnings_reaction import (CLOSE, ET, MIN_ADV as LARGE_MIN_ADV, RECORD_AFTER, RESIGNAL_DAYS, THRESHOLD, _day_bars,
                                     _filings_since, _previous_trading_day, _ticker_for_cik, events_for, measure, ready_to_record)
from tempo.ledger import Ledger, SignalRefused
from tempo.snapshots import Borrow, load_shortstock

SOURCE = "earnings_reaction_small_v1"
MIN_PRICE = 3.0
MIN_ADV = 500_000.0
MAX_ADV = LARGE_MIN_ADV          # exclusive: the large-cap source takes everything at or above this
ROUND_TRIP_COST = 0.006


def in_band(m: dict) -> bool:
    return m.get("status") == "ok" and m["close"] >= MIN_PRICE and MIN_ADV <= m["adv20"] < MAX_ADV


def decide(m: dict) -> int | None:
    if not in_band(m):
        return None
    if m["reaction"] >= THRESHOLD:
        return 1
    if m["reaction"] <= -THRESHOLD:
        return -1
    return None


def borrow_features(symbol: str, table: dict[str, Borrow] | None) -> dict:
    """Stock-loan facts logged beside a signal (never used to filter it: the fee veto is a later, pre-registered test).
    A missing file or symbol is recorded as such, not as a zero fee."""
    b = table.get(symbol) if table else None
    if b is None:
        return {"borrow_known": False}
    return {"borrow_known": True, "borrow_fee": b.fee, "borrow_rebate": b.rebate, "borrow_available": b.available,
            "borrow_capped": b.capped}


def record_signals(hits: list[dict], ledger: Ledger, borrow: dict[str, Borrow] | None = None) -> list[dict]:
    today = datetime.fromtimestamp(ledger.journal.now(), ET).date()
    recent = {s["symbol"] for s in ledger.signals(SOURCE, include_backfill=True)
              if (today - date.fromisoformat(s["date_et"])).days < RESIGNAL_DAYS}
    recorded = []
    for h in hits:
        if h["symbol"] in recent:
            continue
        try:
            recorded.append(ledger.record_signal(
                source=SOURCE, symbol=h["symbol"], direction=h["direction"], event_id=h["day"].replace("-", ""), price=h["close"],
                features={"round_trip_cost": ROUND_TRIP_COST, "reaction": round(h["reaction"], 5), "adv20": round(h["adv20"]),
                          "accession": h["accession"], **borrow_features(h["symbol"], borrow)}))
            recent.add(h["symbol"])
        except SignalRefused:
            continue
    return recorded


def run(now: datetime, ib, ledger: Ledger, fetcher, say=print) -> int:  # pragma: no cover - glue, exercised live
    day = now.astimezone(ET).date()
    if not ready_to_record(now, day):
        say(f"not recording: signals for a reaction day are only recorded on that day after {RECORD_AFTER:%H:%M} ET")
        return 0
    prev_close = datetime.combine(_previous_trading_day(day), CLOSE, tzinfo=ET)
    events = events_for(_filings_since(prev_close - timedelta(hours=1), fetcher), day)
    tickers = _ticker_for_cik(json.loads(fetcher("https://www.sec.gov/files/company_tickers.json")))
    spy = _day_bars(ib, "SPY")
    if spy is None:
        raise RuntimeError("no SPY bars from IBKR")
    counts = {"events": len(events), "no_ticker": 0, "no_bar": 0, "short_history": 0, "out_of_band": 0, "below_threshold": 0, "signal": 0}
    hits = []
    for f in events:
        symbol = tickers.get(f.cik)
        if symbol is None:
            counts["no_ticker"] += 1
            continue
        bars = _day_bars(ib, symbol)
        m: dict[str, Any] = measure(bars, spy, day.isoformat()) if bars else {"status": "no_bar"}
        if m["status"] != "ok":
            counts[m["status"]] += 1
            continue
        if not in_band(m):
            counts["out_of_band"] += 1
            continue
        direction = decide(m)
        if direction is None:
            counts["below_threshold"] += 1
            continue
        counts["signal"] += 1
        hits.append({"symbol": symbol, "direction": direction, "day": day.isoformat(), "reaction": m["reaction"],
                     "close": m["close"], "adv20": m["adv20"], "accession": f.accession})
    recorded = record_signals(hits, ledger, load_shortstock(day))
    say(f"small-cap earnings reactions {day}: {counts}; new signals recorded: {len(recorded)}")
    for r in recorded:
        say(f"  {r['symbol']:<6} {'LONG ' if r['direction'] == 1 else 'SHORT'} reaction {r['features']['reaction']:+.1%}")
    return 0


def main() -> int:  # pragma: no cover - entry point
    from dotenv import load_dotenv

    from tempo.config import load_config
    from tempo.edgar import fetch
    from tempo.ibkr import connect

    load_dotenv()
    ib = connect(load_config())
    ib.RequestTimeout = 60
    try:
        return run(datetime.now(ET), ib, Ledger(), fetch)
    finally:
        ib.disconnect()


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    try:
        raise SystemExit(main())
    except Exception as err:  # noqa: BLE001 - fail loudly with a clear line, non-zero exit
        print(f"[FAIL] {type(err).__name__}: {err}", file=sys.stderr)
        raise SystemExit(1)
