"""Drift after a large reaction to an earnings 8-K (evidence/earnings_reaction_forward.json), recorded as forward signals.

Usage: python -m tempo.earnings_reaction      after 16:20 ET on a trading day (the evening job runs it); needs Gateway.

Each evening: read the SEC's feed of current 8-K filings back to the previous session's close, keep item 2.02 filings
accepted outside regular hours whose reaction day is today, measure each stock's close-to-close move today minus SPY's,
and record a long (+5% or more) or short (-5% or less) signal for liquid stocks (close >= 5 USD, 20-day average dollar
volume >= 5M USD). Signals can only be recorded on the reaction day itself, after the close; a missed evening is lost
(reported, never recorded late), as the registration requires.
"""
from __future__ import annotations

import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from tempo.hours import add_trading_days, is_trading_day
from tempo.ledger import Ledger, SignalRefused

SOURCE = "earnings_reaction_v1"
THRESHOLD = 0.05
MIN_PRICE = 5.0
MIN_ADV = 5_000_000.0
ADV_DAYS = 20
RESIGNAL_DAYS = 30
ROUND_TRIP_COST = 0.002
RECORD_AFTER = time(16, 20)       # delayed bars: give the close 20 minutes to settle
OPEN, CLOSE = time(9, 30), time(16, 0)
FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&dateb=&owner=include&start={start}&count=100&output=atom"
MAX_PAGES = 60
ET = ZoneInfo("America/New_York")
ENTRY = re.compile(r"<entry>(.*?)</entry>", re.DOTALL)
TITLE = re.compile(r"<title>([^<]*?) - .*\((\d{10})\) \((\w+)\)</title>")
ACC = re.compile(r"AccNo:\s*(?:&lt;/b&gt;|</b>)?\s*([0-9A-Za-z-]+)")
ITEM = re.compile(r"Item (\d\.\d\d)")
UPDATED = re.compile(r"<updated>([^<]+)</updated>")


@dataclass(frozen=True)
class Filing:
    cik: str
    accession: str
    items: tuple[str, ...]
    accepted: datetime


@dataclass(frozen=True)
class DayBars:
    dates: list[str]
    close: list[float]
    volume: list[float]


def parse_feed(atom: str) -> list[Filing]:
    out: dict[str, Filing] = {}
    for body in ENTRY.findall(atom):
        t, a, u = TITLE.search(body), ACC.search(body), UPDATED.search(body)
        if not (t and a and u) or t.group(1).strip() != "8-K" or t.group(3) != "Filer":
            continue
        items = tuple(ITEM.findall(html.unescape(body)))
        accepted = datetime.fromisoformat(u.group(1).strip()).astimezone(ET)
        out.setdefault(a.group(1), Filing(t.group(2).lstrip("0"), a.group(1), items, accepted))
    return list(out.values())


def reaction_day(accepted: datetime) -> date | None:
    local = accepted.astimezone(ET)
    d, t = local.date(), local.time()
    if is_trading_day(d) and OPEN <= t < CLOSE:
        return None
    if is_trading_day(d) and t < OPEN:
        return d
    return add_trading_days(d, 1)


def events_for(filings: list[Filing], day: date) -> list[Filing]:
    return [f for f in filings if "2.02" in f.items and reaction_day(f.accepted) == day]


def measure(stock: DayBars, spy: DayBars, day: str) -> dict[str, Any]:
    if day not in stock.dates or day not in spy.dates:
        return {"status": "no_bar"}
    i = stock.dates.index(day)
    if i < ADV_DAYS:
        return {"status": "short_history"}
    prev = stock.dates[i - 1]
    if prev not in spy.dates:
        return {"status": "no_bar"}
    j, k = spy.dates.index(day), spy.dates.index(prev)
    raw = stock.close[i] / stock.close[i - 1] - 1
    bench = spy.close[j] / spy.close[k] - 1
    adv = sum(stock.close[n] * stock.volume[n] for n in range(i - ADV_DAYS, i)) / ADV_DAYS
    return {"status": "ok", "reaction": raw - bench, "close": stock.close[i], "adv20": adv}


def decide(m: dict) -> int | None:
    if m.get("status") != "ok" or m["close"] < MIN_PRICE or m["adv20"] < MIN_ADV:
        return None
    if m["reaction"] >= THRESHOLD:
        return 1
    if m["reaction"] <= -THRESHOLD:
        return -1
    return None


def ready_to_record(now: datetime, day: date) -> bool:
    local = now.astimezone(ET)
    return is_trading_day(day) and local.date() == day and local.time() >= RECORD_AFTER


def record_signals(hits: list[dict], ledger: Ledger) -> list[dict]:
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
                          "accession": h["accession"]}))
            recent.add(h["symbol"])
        except SignalRefused:
            continue
    return recorded


# --- the parts that talk to the SEC and to IBKR -------------------------------------------------------------------

def _filings_since(cutoff: datetime, fetcher) -> list[Filing]:  # pragma: no cover - network
    seen: dict[str, Filing] = {}
    for page in range(MAX_PAGES):
        rows = parse_feed(fetcher(FEED.format(start=page * 100)))
        if not rows:
            break
        for f in rows:
            seen.setdefault(f.accession, f)
        if min(f.accepted for f in rows) < cutoff:
            return list(seen.values())
    raise RuntimeError(f"the SEC 8-K feed did not reach back to {cutoff:%Y-%m-%d %H:%M} ET in {MAX_PAGES} pages")


def _ticker_for_cik(mapping: dict) -> dict[str, str]:  # pragma: no cover - network data
    out: dict[str, str] = {}
    for row in mapping.values():
        ticker = str(row["ticker"]).upper()
        if re.fullmatch(r"[A-Z]{1,5}", ticker):
            out.setdefault(str(row["cik_str"]), ticker)
    return out


def _day_bars(ib, symbol: str) -> DayBars | None:  # pragma: no cover - IBKR
    from ib_async import Stock
    contract = Stock(symbol, "SMART", "USD")
    if not ib.qualifyContracts(contract):
        return None
    raw = ib.reqHistoricalData(contract, "", "3 M", "1 day", "TRADES", useRTH=True, formatDate=1)
    if not raw:
        return None
    return DayBars([str(b.date) for b in raw], [float(b.close) for b in raw], [float(b.volume) for b in raw])


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
    counts = {"events": len(events), "no_ticker": 0, "no_bar": 0, "short_history": 0, "filtered": 0, "below_threshold": 0, "signal": 0}
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
        direction = decide(m)
        if direction is None:
            counts["filtered" if (m["close"] < MIN_PRICE or m["adv20"] < MIN_ADV) else "below_threshold"] += 1
            continue
        counts["signal"] += 1
        hits.append({"symbol": symbol, "direction": direction, "day": day.isoformat(), "reaction": m["reaction"],
                     "close": m["close"], "adv20": m["adv20"], "accession": f.accession})
    recorded = record_signals(hits, ledger)
    say(f"earnings reactions {day}: {counts}; new signals recorded: {len(recorded)}")
    for r in recorded:
        say(f"  {r['symbol']:<6} {'LONG ' if r['direction'] == 1 else 'SHORT'} reaction {r['features']['reaction']:+.1%}")
    return 0


def _previous_trading_day(day: date) -> date:
    d = day - timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


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
