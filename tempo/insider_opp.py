"""Opportunistic insider purchases (evidence/insider_opportunistic_forward.json), recorded as forward signals.

Runs inside `python -m tempo.insider` after the cluster source, on the same Form 4 cache. A purchase counts when one of
its officers or directors is not a routine buyer (tempo/insider_history.py). Per issuer, over the trailing 3 calendar
days of filings: at least 50,000 USD of such purchases at a volume-weighted price of at least 5 USD gives one long
signal, not repeated within 30 days.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from tempo.insider_history import is_routine
from tempo.ledger import Ledger, SignalRefused

SOURCE = "insider_opportunistic_v1"
WINDOW_DAYS = 3
MIN_VALUE = 50_000.0
MIN_PRICE = 5.0
RESIGNAL_DAYS = 30
ROUND_TRIP_COST = 0.005
NEW_YORK = ZoneInfo("America/New_York")


def _opportunistic_owners(b: dict, index: dict) -> list[str]:
    trade = date.fromisoformat((b.get("trade_date") or b["filing_date"])[:10])
    return [o for o in b.get("officer_director", []) if not is_routine(o, trade.year, trade.month, index)]


def opportunistic_signals(buys: list[dict], asof: date, index: dict) -> list[dict]:
    start = (asof - timedelta(days=WINDOW_DAYS)).isoformat()
    by_issuer: dict[tuple[str, str], list[tuple[dict, list[str]]]] = {}
    for b in buys:
        if not (start < b["filing_date"] <= asof.isoformat()) or not b.get("officer_director"):
            continue
        owners = _opportunistic_owners(b, index)
        if owners:
            by_issuer.setdefault((b["symbol"], b["issuer_cik"]), []).append((b, owners))
    found = []
    for (symbol, cik), rows in sorted(by_issuer.items()):
        value, shares = sum(b["value"] for b, _ in rows), sum(b["shares"] for b, _ in rows)
        vwap = value / shares
        if value >= MIN_VALUE and vwap >= MIN_PRICE:
            found.append({"symbol": symbol, "issuer_cik": cik, "value": value, "vwap": vwap,
                          "owners": sorted({o for _, os in rows for o in os}),
                          "last_filing_date": max(b["filing_date"] for b, _ in rows),
                          "accessions": sorted({b["accession"] for b, _ in rows})})
    return found


def record_signals(found: list[dict], ledger: Ledger) -> list[dict]:
    today = datetime.fromtimestamp(ledger.journal.now(), NEW_YORK).date()
    recent = {s["symbol"] for s in ledger.signals(SOURCE, include_backfill=True)
              if (today - date.fromisoformat(s["date_et"])).days < RESIGNAL_DAYS}
    recorded = []
    for c in found:
        if c["symbol"] in recent:
            continue
        try:
            recorded.append(ledger.record_signal(
                source=SOURCE, symbol=c["symbol"], direction=1, event_id=c["last_filing_date"].replace("-", ""), price=c["vwap"],
                features={"round_trip_cost": ROUND_TRIP_COST, "n_opportunistic": len(c["owners"]), "value": round(c["value"]),
                          "vwap": round(c["vwap"], 4), "accessions": c["accessions"]}))
        except SignalRefused:
            continue
    return recorded
