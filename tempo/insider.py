"""Insider-purchase clusters from SEC Form 4 filings, recorded as forward signals (evidence/insider_forward.json).

Usage: python -m tempo.insider DATE [DATE ...]      process those trading days' filings in order, then emit signals
       as of the LAST date. The SEC generates a day's index overnight, so the newest date available is yesterday.

A cluster is: in the trailing 7 calendar days of filings, at least 2 distinct insiders made open-market purchases
(transaction code P, acquired, not a pre-planned 10b5-1 trade) of at least 200,000 USD in total at a volume-weighted
price of at least 5 USD. One long signal per issuer per 30 days, recorded in the ledger with the clock's timestamp
and a 50 bps round-trip cost assumption.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from tempo.edgar import EdgarError, fetch
from tempo.ledger import Ledger, SignalRefused

SOURCE = "insider_cluster_v1"
CACHE = Path(__file__).resolve().parents[1] / "data" / "insider_cache.jsonl"
WINDOW_DAYS = 7
MIN_OWNERS = 2
MIN_VALUE = 200_000.0
MIN_PRICE = 5.0
RESIGNAL_DAYS = 30
ROUND_TRIP_COST = 0.005
MAX_DOCUMENT_CHARS = 500_000
NEW_YORK = ZoneInfo("America/New_York")
INDEX_ROW = re.compile(r"^4\s+(.+?)\s+(\d+)\s+(\d{8})\s+(edgar/\S+)\s*$")
SYMBOL = re.compile(r"^[A-Z]{1,5}$")
DOC = re.compile(r"<ownershipDocument>.*?</ownershipDocument>", re.DOTALL)


def parse_index(text: str) -> list[dict]:
    """Form 4 filings listed in an EDGAR daily form index, once each (the owner and the issuer both get a line)."""
    seen, out = set(), []
    for line in text.split("\n"):
        m = INDEX_ROW.match(line)
        if not m:
            continue
        path = m.group(4)
        accession = path.rsplit("/", 1)[-1].removesuffix(".txt")
        if accession in seen:
            continue
        seen.add(accession)
        d = m.group(3)
        out.append({"accession": accession, "path": path, "filing_date": f"{d[:4]}-{d[4:6]}-{d[6:]}"})
    return out


def _text(node, path: str) -> str:
    found = node.find(path)
    return (found.text or "").strip() if found is not None and found.text else ""


def parse_form4(submission: str, filing_date: str, accession: str) -> list[dict]:
    """Counted purchases in one Form 4 submission (see the module docstring for what counts)."""
    m = DOC.search(submission)
    if not m:
        return []
    document = m.group(0)
    # The XML is filer-supplied, so it is untrusted. A Form 4 never needs a DTD or entity definitions; refusing them
    # (and absurd sizes) closes the entity-expansion ("billion laughs") hole of the standard-library parser.
    if len(document) > MAX_DOCUMENT_CHARS or "<!DOCTYPE" in document.upper() or "<!ENTITY" in document.upper():
        return []
    try:
        root = ET.fromstring(document)
    except ET.ParseError:
        return []
    symbol = _text(root, "issuer/issuerTradingSymbol").upper()
    if not SYMBOL.match(symbol) or _text(root, "aff10b5One").lower() in ("1", "true"):  # both spellings occur
        return []
    owners = [(o.text or "").strip() for o in root.findall("reportingOwner/reportingOwnerId/rptOwnerCik")]
    officer_director = [_text(o, "reportingOwnerId/rptOwnerCik") for o in root.findall("reportingOwner")
                        if any(_text(o, f"reportingOwnerRelationship/{flag}").lower() in ("1", "true") for flag in ("isDirector", "isOfficer"))]
    buys = []
    for tx in root.findall("nonDerivativeTable/nonDerivativeTransaction"):
        if _text(tx, "transactionCoding/transactionCode") != "P" or _text(tx, "transactionAmounts/transactionAcquiredDisposedCode/value") != "A":
            continue
        try:
            shares = float(_text(tx, "transactionAmounts/transactionShares/value"))
            price = float(_text(tx, "transactionAmounts/transactionPricePerShare/value"))
        except ValueError:
            continue
        if shares > 0 and price > 0:
            buys.append({"accession": accession, "filing_date": filing_date, "trade_date": _text(tx, "transactionDate/value"),
                         "issuer_cik": _text(root, "issuer/issuerCik"), "symbol": symbol, "owners": owners,
                         "officer_director": officer_director, "shares": shares,
                         "price": price, "value": shares * price})
    return buys


def clusters(buys: list[dict], asof: date, window_days: int = WINDOW_DAYS, min_owners: int = MIN_OWNERS,
             min_value: float = MIN_VALUE, min_price: float = MIN_PRICE) -> list[dict]:
    """Issuers whose counted purchases filed in the last `window_days` calendar days (through `asof`) form a cluster."""
    start = (asof - timedelta(days=window_days)).isoformat()
    by_issuer: dict[tuple[str, str], list[dict]] = {}
    for b in buys:
        if start < b["filing_date"] <= asof.isoformat():
            by_issuer.setdefault((b["symbol"], b["issuer_cik"]), []).append(b)
    found = []
    for (symbol, cik), rows in sorted(by_issuer.items()):
        owners = sorted({o for r in rows for o in r["owners"]})
        value, shares = sum(r["value"] for r in rows), sum(r["shares"] for r in rows)
        vwap = value / shares
        if len(owners) >= min_owners and value >= min_value and vwap >= min_price:
            found.append({"symbol": symbol, "issuer_cik": cik, "owners": owners, "value": value, "vwap": vwap,
                          "last_filing_date": max(r["filing_date"] for r in rows), "accessions": sorted({r["accession"] for r in rows})})
    return found


def new_signals(found: list[dict], ledger: Ledger) -> list[dict]:
    """Record a long signal for each cluster not already signalled in the last RESIGNAL_DAYS days. Returns the records."""
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
                features={"round_trip_cost": ROUND_TRIP_COST, "n_insiders": len(c["owners"]), "value": round(c["value"]),
                          "vwap": round(c["vwap"], 4), "accessions": c["accessions"]}))
        except SignalRefused:
            continue
    return recorded


def load_cache(path: Path = CACHE) -> tuple[set[str], list[dict]]:
    seen, buys = set(), []
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            (seen.add(rec["acc"]) if rec["k"] == "filing" else buys.append(rec["buy"]))
    return seen, buys


def _append(path: Path, records: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in records)


def process_day(day: date, fetcher=fetch, cache: Path = CACHE, say=print) -> dict:
    """Download and parse every Form 4 filed on `day` that is not already cached. A filing that fails is NOT marked
    as seen, so the next run retries it."""
    quarter = (day.month - 1) // 3 + 1
    index = fetcher(f"https://www.sec.gov/Archives/edgar/daily-index/{day.year}/QTR{quarter}/form.{day:%Y%m%d}.idx")
    rows = parse_index(index)
    seen, _ = load_cache(cache)
    todo = [r for r in rows if r["accession"] not in seen]
    stats = {"filings": len(rows), "new": len(todo), "purchases": 0, "failed": 0}
    batch: list[dict] = []
    for i, row in enumerate(todo, 1):
        try:
            buys = parse_form4(fetcher(f"https://www.sec.gov/Archives/{row['path']}"), row["filing_date"], row["accession"])
        except EdgarError as err:
            stats["failed"] += 1
            say(f"  failed {row['accession']}: {err}")
            continue
        batch += [{"k": "buy", "buy": b} for b in buys] + [{"k": "filing", "acc": row["accession"]}]
        stats["purchases"] += len(buys)
        if i % 50 == 0 or i == len(todo):
            _append(cache, batch)
            batch = []
            say(f"  {day}: {i}/{len(todo)} filings, {stats['purchases']} purchases so far")
    _append(cache, batch)
    return stats


def main(dates: list[str]) -> int:
    days = [date.fromisoformat(d) for d in dates]
    for d in days:
        print(f"{d}: {process_day(d)}")
    _, buys = load_cache()
    found = clusters(buys, days[-1])
    recorded = new_signals(found, Ledger())
    print(f"clusters as of {days[-1]}: {len(found)}; new signals recorded: {len(recorded)}")
    for s in recorded:
        print(f"  {s['symbol']:<6} {s['features']['n_insiders']} insiders, {s['features']['value']:,} USD at {s['features']['vwap']}")
    from tempo.insider_history import load_index
    from tempo.insider_opp import opportunistic_signals, record_signals
    found_opp = opportunistic_signals(buys, days[-1], load_index())
    recorded_opp = record_signals(found_opp, Ledger())
    print(f"opportunistic as of {days[-1]}: {len(found_opp)}; new signals recorded: {len(recorded_opp)}")
    for s in recorded_opp:
        print(f"  {s['symbol']:<6} {s['features']['n_opportunistic']} opportunistic, {s['features']['value']:,} USD at {s['features']['vwap']}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        if len(sys.argv) < 2:
            raise ValueError("usage: python -m tempo.insider DATE [DATE ...]")
        raise SystemExit(main(sys.argv[1:]))
    except (EdgarError, ValueError, RuntimeError) as err:  # RuntimeError covers HistoryMissing
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
