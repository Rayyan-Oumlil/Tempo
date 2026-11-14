"""B4: big one-day moves split by news (evidence/news_drift_forward.json and evidence/no_news_fade_forward.json), recorded as forward signals.

Usage: python -m tempo.news_split      after 16:20 ET on a trading day (the evening job runs it); needs Gateway and SEC_USER_AGENT.

Each evening, for every liquid universe stock whose close-to-close move today minus SPY's is at least 5% up or down:
  * an 8-K item 2.02 accepted in the window (previous close to today's close)  -> skipped, earnings_reaction_v1 owns it;
  * at least one headline in the window from DJ-RTG, DJ-N or BRFG               -> news_drift_v1: follow the move;
  * no headline, and the move minus the stock's sector ETF has the same sign and is at least 4% -> no_news_fade_v1: oppose the move;
  * no headline but the sector explains it (sympathy move)                     -> skipped.
A stock whose news could not be fetched is skipped and counted: an unknown is never treated as "no news". A missed evening is lost,
never recorded late.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, cast
from zoneinfo import ZoneInfo

from tempo.daybars import DayBars
from tempo.earnings_reaction import Filing, decide, measure, ready_to_record
from tempo.hours import is_trading_day
from tempo.ledger import Ledger, SignalRefused
from tempo.snapshots import SNAP, Borrow, context_features, load_shortstock

DRIFT = "news_drift_v1"
FADE = "no_news_fade_v1"
UNIVERSE = "evidence/universe_sp500_20261111.txt"
ROOT = Path(__file__).resolve().parents[1]
SECTOR_MAP = ROOT / "evidence" / "sector_map_20261113.csv"
PROVIDERS = ("DJ-RTG", "DJ-N", "BRFG")
PER_FEED = 30
RESIDUAL = 0.04
RESIGNAL_DAYS = 30
ROUND_TRIP_COST = 0.002
MAX_FAILED_SHARE = 0.2
CLOSE = time(16, 0)
ET = ZoneInfo("America/New_York")
Headline = tuple[datetime, str, str]


def load_sector_map(path: Path = SECTOR_MAP) -> dict[str, str]:
    """Symbol to its SPDR sector ETF, from the frozen file. A missing file is an error, never an empty map."""
    with path.open(encoding="utf-8", newline="") as f:
        return {row["symbol"]: row["sector_etf"] for row in csv.DictReader(f)}


def previous_trading_day(day: date) -> date:
    d = day - timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def window(day: date) -> tuple[datetime, datetime]:
    """From the previous session's close to today's close, New York time."""
    return (datetime.combine(previous_trading_day(day), CLOSE, tzinfo=ET), datetime.combine(day, CLOSE, tzinfo=ET))


def headlines_in_window(items: list[Headline], day: date) -> list[Headline]:
    lo, hi = window(day)
    return [h for h in items if lo <= h[0] <= hi]


def earnings_symbols(filings: list[Filing], tickers: dict[str, str], day: date) -> set[str]:
    """Tickers with an 8-K item 2.02 accepted inside the window, whatever the hour: earnings are the event of another source."""
    lo, hi = window(day)
    return {tickers[f.cik] for f in filings if "2.02" in f.items and lo <= f.accepted <= hi and f.cik in tickers}


def raw_return(bars: DayBars, day: str) -> float | None:
    if day not in bars.dates:
        return None
    i = bars.dates.index(day)
    return None if i < 1 else bars.close[i] / bars.close[i - 1] - 1


def sector_residual(stock: DayBars, etf: DayBars, day: str) -> float | None:
    """The stock's close-to-close move minus its sector ETF's, None if either bar is missing."""
    s, e = raw_return(stock, day), raw_return(etf, day)
    return None if s is None or e is None else s - e


def classify(direction: int, residual: float | None, has_earnings: bool, n_headlines: int) -> tuple[str, int] | str:
    """(source, signal direction) for a mover, or the reason it is skipped. `direction` is the move's sign."""
    if has_earnings:
        return "earnings"
    if n_headlines > 0:
        return DRIFT, direction
    if residual is None:
        return "no_sector_bars"
    if residual * direction >= RESIDUAL:
        return FADE, -direction
    return "sympathy"


def vix_asof(day: date, path: Path = SNAP / "fred" / "VIXCLS.csv") -> float | None:
    """Last VIX close strictly before `day` (a logged condition, never a filter); None when the file or the value is missing."""
    if not path.exists():
        return None
    last: float | None = None
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        d, _, v = line.partition(",")
        try:
            if date.fromisoformat(d) < day:
                last = float(v)
        except ValueError:
            continue
    return last


def record_signals(hits: list[dict], source: str, ledger: Ledger, borrow: dict[str, Borrow] | None, vix: float | None) -> list[dict]:
    today = datetime.fromtimestamp(ledger.journal.now(), ET).date()
    recent = {s["symbol"] for s in ledger.signals(source, include_backfill=True)
              if (today - date.fromisoformat(s["date_et"])).days < RESIGNAL_DAYS}
    recorded = []
    for h in hits:
        if h["symbol"] in recent:
            continue
        features: dict[str, Any] = {"round_trip_cost": ROUND_TRIP_COST, "reaction": round(h["reaction"], 5), "adv20": round(h["adv20"]),
                                    "headlines": h["headlines"], "providers": h["providers"], "vix": vix,
                                    **context_features(h, borrow, h["symbol"])}
        if source == FADE:
            features.update({"sector_etf": h["sector_etf"], "residual": round(h["residual"], 5)})
        try:
            recorded.append(ledger.record_signal(source=source, symbol=h["symbol"], direction=h["direction"], event_id=h["day"].replace("-", ""),
                                                 price=h["close"], features=features))
            recent.add(h["symbol"])
        except SignalRefused:
            continue
    return recorded


def too_many_failed(failed: int, movers: int) -> bool:
    return movers > 0 and failed / movers > MAX_FAILED_SHARE


COUNTS = ("movers", "earnings", "news_unavailable", "no_sector_bars", "sympathy", "drift", "fade")


# --- the parts that talk to the SEC and to IBKR -------------------------------------------------------------------

def ib_news(ib, symbol: str) -> list[Headline] | None:  # pragma: no cover - IBKR
    """Headlines from the three feeds for this company's contract (the provider attaches them to the contract), or None on any failure."""
    from ib_async import Stock
    contract = Stock(symbol, "SMART", "USD")
    if not ib.qualifyContracts(contract):
        return None
    out: list[Headline] = []
    for provider in PROVIDERS:
        try:
            got = ib.reqHistoricalNews(contract.conId, provider, "", "", PER_FEED)
        except Exception:  # noqa: BLE001 - the caller counts it as unavailable
            return None
        if got is None:
            return None
        for n in cast(list, got):
            t = n.time if isinstance(n.time, datetime) else datetime.strptime(str(n.time)[:19], "%Y-%m-%d %H:%M:%S")
            out.append((t if t.tzinfo else t.replace(tzinfo=timezone.utc), provider, n.headline))
    return out


def run(now: datetime, ib, ledger: Ledger, fetcher: Callable[[str], str], say=print) -> int:  # pragma: no cover - glue, exercised live
    from tempo.daybars import day_bars, load_universe
    from tempo.earnings_reaction import _filings_since, _ticker_for_cik
    day = now.astimezone(ET).date()
    if not ready_to_record(now, day):
        say("not recording: B4 signals are only recorded on the signal day after 16:20 ET")
        return 0
    iso = day.isoformat()
    lo, _ = window(day)
    earn = earnings_symbols(_filings_since(lo - timedelta(hours=1), fetcher),
                            _ticker_for_cik(json.loads(fetcher("https://www.sec.gov/files/company_tickers.json"))), day)
    sectors = load_sector_map()
    spy = day_bars(ib, "SPY")
    if spy is None:
        raise RuntimeError("no SPY bars from IBKR")
    etf_bars: dict[str, DayBars | None] = {}
    counts = dict.fromkeys(COUNTS, 0)
    hits: dict[str, list[dict]] = {DRIFT: [], FADE: []}
    for symbol in load_universe(UNIVERSE):
        bars = day_bars(ib, symbol)
        m: dict[str, Any] = measure(bars, spy, iso) if bars else {"status": "no_bar"}
        direction = decide(m)
        if direction is None or bars is None:
            continue
        counts["movers"] += 1
        if symbol in earn:
            counts["earnings"] += 1
            continue
        news = ib_news(ib, symbol)
        if news is None:
            counts["news_unavailable"] += 1
            continue
        items = headlines_in_window(news, day)
        residual = None
        etf = sectors.get(symbol)
        if not items and etf is not None:
            if etf not in etf_bars:
                etf_bars[etf] = day_bars(ib, etf)
            eb = etf_bars[etf]
            residual = sector_residual(bars, eb, iso) if eb else None
        verdict = classify(direction, residual, False, len(items))
        if isinstance(verdict, str):
            counts[verdict] += 1
            continue
        source, signal_direction = verdict
        counts["drift" if source == DRIFT else "fade"] += 1
        hits[source].append({"symbol": symbol, "direction": signal_direction, "day": iso, "reaction": m["reaction"], "close": m["close"],
                             "adv20": m["adv20"], "vol20": m["vol20"], "headlines": len(items), "providers": sorted({h[1] for h in items}),
                             "sector_etf": etf, "residual": residual})
    borrow, vix = load_shortstock(day), vix_asof(day)
    recorded = {s: record_signals(h, s, ledger, borrow, vix) for s, h in hits.items()}
    say(f"B4 news split {day}: {counts}; new signals: drift {len(recorded[DRIFT])}, fade {len(recorded[FADE])}")
    for s, rows in recorded.items():
        for r in rows:
            say(f"  {s:<16} {r['symbol']:<6} {'LONG ' if r['direction'] == 1 else 'SHORT'} reaction {r['features']['reaction']:+.1%}")
    return 1 if too_many_failed(counts["news_unavailable"], counts["movers"]) else 0


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
