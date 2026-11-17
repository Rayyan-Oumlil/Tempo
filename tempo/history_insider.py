"""History of the two insider sources (Workstream F): the live rules, replayed on the SEC Insider Transactions Data Sets.

Nothing is re-implemented: purchases are rebuilt from the quarterly zips in the same shape `tempo.insider.parse_form4` returns, and
the live `clusters` and `opportunistic_signals` pick the signals. A signal as of trading day P is entered at the open of the next
session (the live morning job records it before the 09:40 entry). One signal per issuer per 30 days, as live.

Purchases filed more than 365 days after the trade are excluded (late filings nobody could act on).
Limits, stated in every report: Form sets before April 2023 have no 10b5-1 flag (those purchases cannot be excluded); issuers that
IBKR no longer lists have no bars and drop out (survivorship flatters the result); entries stop on 2025-12-23 so no 2026 price is used.
"""
from __future__ import annotations

import csv
import io
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Callable, Iterator

from tempo import insider as cluster_rule
from tempo import insider_opp as opp_rule
from tempo.history_core import Series, Trade, trade_excess

LAST_ENTRY = "2025-12-23"      # a 5-session exit then lands on or before 2025-12-31: the 2026 holdout is never read
HORIZON = 5
MAX_LAG_DAYS = 365   # a purchase filed more than a year after the trade is a late, non-actionable filing (decided 2026-11-16, before any result);
                     # the live opportunistic rule would also raise HistoryMissing on one whose trade year the routine index does not cover
WINDOW_DAYS = max(cluster_rule.WINDOW_DAYS, opp_rule.WINDOW_DAYS)
SOURCES = {"insider_cluster_v1": cluster_rule.ROUND_TRIP_COST, "insider_opportunistic_v1": opp_rule.ROUND_TRIP_COST}


def _rows(z: zipfile.ZipFile, name: str) -> Iterator[dict]:
    with z.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, "utf-8", errors="replace"), delimiter="\t", quoting=csv.QUOTE_NONE)


def _iso(raw: str) -> str:
    return datetime.strptime(raw.strip(), "%d-%b-%Y").date().isoformat()


def buys_from_zip(raw: bytes) -> list[dict]:
    """Counted purchases of one quarterly set, shaped like `parse_form4` output: Form 4 (not an amendment), not 10b5-1, a plain
    letters-only symbol, transaction code P, acquired, shares and price above zero."""
    z = zipfile.ZipFile(io.BytesIO(raw))
    filings = {}
    for r in _rows(z, "SUBMISSION.tsv"):
        symbol = r["ISSUERTRADINGSYMBOL"].strip().upper()
        if (r["DOCUMENT_TYPE"] == "4" and r.get("AFF10B5ONE", "").strip().lower() not in ("1", "true")
                and cluster_rule.SYMBOL.match(symbol) and symbol not in cluster_rule.PLACEHOLDER_SYMBOLS):
            try:
                filings[r["ACCESSION_NUMBER"]] = {"filing_date": _iso(r["FILING_DATE"]), "issuer_cik": r["ISSUERCIK"].strip(), "symbol": symbol}
            except ValueError:
                continue
    owners: dict[str, list[str]] = defaultdict(list)
    officer_director: dict[str, list[str]] = defaultdict(list)
    for r in _rows(z, "REPORTINGOWNER.tsv"):
        acc = r["ACCESSION_NUMBER"]
        if acc in filings:
            owners[acc].append(r["RPTOWNERCIK"].strip())
            if "Officer" in r["RPTOWNER_RELATIONSHIP"] or "Director" in r["RPTOWNER_RELATIONSHIP"]:
                officer_director[acc].append(r["RPTOWNERCIK"].strip())
    buys = []
    for r in _rows(z, "NONDERIV_TRANS.tsv"):
        acc = r["ACCESSION_NUMBER"]
        if acc not in filings or r["TRANS_CODE"] != "P" or r["TRANS_ACQUIRED_DISP_CD"] != "A":
            continue
        try:
            shares, price = float(r["TRANS_SHARES"] or 0), float(r["TRANS_PRICEPERSHARE"] or 0)
            trade_date = _iso(r["TRANS_DATE"])
        except ValueError:
            continue
        if shares > 0 and price > 0:
            f = filings[acc]
            buys.append({"accession": acc, "filing_date": f["filing_date"], "trade_date": trade_date, "issuer_cik": f["issuer_cik"],
                         "symbol": f["symbol"], "owners": owners[acc], "officer_director": officer_director[acc],
                         "shares": shares, "price": price, "value": shares * price})
    return buys


def signals(buys: list[dict], index: dict, calendar: list[str], first: str, last: str = LAST_ENTRY) -> dict[str, list[tuple[str, str]]]:
    """source -> [(entry day, symbol)] for every signal whose entry session lies in [first, last]."""
    by_date: dict[str, list[dict]] = defaultdict(list)
    for b in buys:
        if (date.fromisoformat(b["filing_date"]) - date.fromisoformat(b["trade_date"])).days <= MAX_LAG_DAYS:
            by_date[b["filing_date"]].append(b)
    out: dict[str, list[tuple[str, str]]] = {s: [] for s in SOURCES}
    last_signal: dict[str, dict[str, date]] = {s: {} for s in SOURCES}
    for k in range(len(calendar) - 1):
        asof, entry = calendar[k], calendar[k + 1]
        if entry < first or entry > last:
            continue
        p = date.fromisoformat(asof)
        window = [b for n in range(WINDOW_DAYS) for b in by_date.get((p - timedelta(days=n)).isoformat(), ())]
        if not window:
            continue
        found = {"insider_cluster_v1": cluster_rule.clusters(window, p),
                 "insider_opportunistic_v1": opp_rule.opportunistic_signals(window, p, index)}
        for source, hits in found.items():
            for c in hits:
                seen = last_signal[source].get(c["symbol"])
                if seen is not None and (date.fromisoformat(entry) - seen).days < cluster_rule.RESIGNAL_DAYS:
                    continue
                last_signal[source][c["symbol"]] = date.fromisoformat(entry)
                out[source].append((entry, c["symbol"]))
    return out


def to_trades(sigs: list[tuple[str, str]], spy: Series, bars: Callable[[str], Series | None], horizon: int = HORIZON) -> tuple[list[Trade], Counter]:
    counts: Counter = Counter()
    trades = []
    for entry, symbol in sigs:
        stock = bars(symbol)
        if stock is None:
            counts["no_bars"] += 1
            continue
        gross = trade_excess(stock, spy, entry, 1, horizon)
        if gross is None:
            counts["unscored"] += 1
            continue
        counts["scored"] += 1
        trades.append(Trade(entry, symbol, gross))
    return trades, counts
