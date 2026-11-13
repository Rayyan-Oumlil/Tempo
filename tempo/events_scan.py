"""Read-only count of structural-event filings on SEC EDGAR (issuer tender offers, closed-end-fund repurchase notices,
merger proxies, spin-off registrations). It places no orders and changes no rule: it turns guesses about how many such
events exist per year into measured counts, with accession numbers, so a later pre-registration can set real sample sizes.

Source: EDGAR's quarterly form index (https://www.sec.gov/Archives/edgar/full-index/YYYY/QTRn/form.gz), which lists every
filing by form type. (The full-text-search host efts.sec.gov answers 403 to this client, so it is not used.) A completed
quarter is cached under data/events/index/ and never fetched twice; the running quarter is re-fetched every time.
The company-name hint (`fund_like`) is a crude regex, not a classification; a SIC lookup is a later step.

`enrich` adds each filer's current SIC code, tickers and exchanges from data.sec.gov/submissions (cached in
data/events/cik_meta.json). Those fields describe the filer TODAY: a target acquired since its merger proxy, or a
liquidated SPAC, shows no exchange, so the "listed" counts are a lower bound for mergers and SPAC-like events.

Usage: python -m tempo.events_scan [FIRST_YEAR]    (default 2019) -> data/events/events.csv and a per-year table.
       python -m tempo.events_scan enrich          fill data/events/cik_meta.json for the CIKs in events.csv (resumable).
"""
from __future__ import annotations

import csv
import gzip
import json
import re
import sys
import zlib
from collections import Counter
from collections.abc import Callable, Iterable
from datetime import date, timedelta
from pathlib import Path

from tempo import edgar

INDEX_URL = "https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{q}/form.gz"
CACHE = Path("data/events/index")
OUT = Path("data/events/events.csv")
FIRST_YEAR = 2019
SETTLE_DAYS = 5
# Original filings only: amendments (form type ending "/A") are the same event again and are never counted.
WATCH = ("SC TO-I", "10-12B", "DEFM14A", "SC 13E3", "N-23C3A", "N-23C3B", "N-23C-3")
FUND_HINT = re.compile(r"\b(fund|trust|portfolio|strategies|partners|opportunit\w*|income)\b", re.IGNORECASE)
ROW = re.compile(r"^(?P<form>\S.*?)\s{2,}(?P<name>.+?)\s+(?P<cik>\d{1,10})\s+(?P<filed>\d{4}-\d{2}-\d{2})\s+(?P<path>\S+)\s*$")
META = Path("data/events/cik_meta.json")
LISTED = frozenset({"NYSE", "Nasdaq", "NYSE American", "NYSE Arca", "Cboe BZX", "CBOE"})
ENRICH_FORMS = ("SC TO-I", "DEFM14A", "10-12B", "SC 13E3")
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
FIELDS = ("form", "filed", "cik", "company", "accession", "fund_like")


class FormIndexError(RuntimeError):
    pass


def parse_form_index(text: str, watch: Iterable[str] = WATCH) -> list[dict]:
    """Rows of the watched form types from one quarterly index. Refuses a file with no header or too few parsable rows."""
    wanted = set(watch)
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("-----")), None)
    if start is None or len(lines) - start < 100:
        raise FormIndexError("not an EDGAR form index (no header rule, or far too short)")
    events, seen = [], 0
    for ln in lines[start + 1:]:
        m = ROW.match(ln)
        if not m:
            continue
        seen += 1
        if m["form"] not in wanted:
            continue
        accession = m["path"].rsplit("/", 1)[-1].removesuffix(".txt")
        events.append({"form": m["form"], "filed": m["filed"], "cik": str(int(m["cik"])), "company": m["name"].strip(),
                       "accession": accession, "fund_like": bool(FUND_HINT.search(m["name"]))})
    if seen < 1000:
        raise FormIndexError(f"only {seen} parsable rows: the index format has changed")
    return events


def quarters(first_year: int, today: date) -> list[tuple[int, int]]:
    return [(y, q) for y in range(first_year, today.year + 1) for q in range(1, 5) if date(y, 3 * q - 2, 1) <= today]


def quarter_complete(year: int, q: int, today: date) -> bool:
    """Complete only a few days after the quarter ends: the index is built nightly, so the first days still miss late filings."""
    end_month = 3 * q
    nxt = date(year + (end_month == 12), end_month % 12 + 1, 1)
    return nxt + timedelta(days=SETTLE_DAYS) <= today


def load_quarter(year: int, q: int, today: date, fetch: Callable[[str], bytes] = edgar.fetch_bytes, cache: Path = CACHE) -> list[dict]:
    path = cache / f"{year}Q{q}.form.gz"
    done = quarter_complete(year, q, today)
    if path.exists() and done:
        raw = path.read_bytes()
    else:
        raw = fetch(INDEX_URL.format(year=year, q=q))
    try:
        text = gzip.decompress(raw).decode("latin-1")
    except (OSError, EOFError, zlib.error) as exc:
        raise FormIndexError(f"{year} Q{q}: not a readable gzip file ({exc!r})") from exc
    events = parse_form_index(text)          # validated BEFORE it can be cached
    if done and not path.exists():
        cache.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return events


def scan(first_year: int, today: date, fetch: Callable[[str], bytes] = edgar.fetch_bytes, cache: Path = CACHE,
         skipped: list[str] | None = None) -> list[dict]:
    """All watched filings. The running quarter may not be published or usable yet: that one quarter is skipped and named in `skipped`;
    a failure in any completed quarter still raises."""
    out: dict[str, dict] = {}
    for year, q in quarters(first_year, today):
        try:
            found = load_quarter(year, q, today, fetch, cache)
        except (edgar.EdgarError, FormIndexError) as exc:
            if quarter_complete(year, q, today):
                raise
            if skipped is not None:
                skipped.append(f"{year} Q{q}: {exc}")
            continue
        for ev in found:
            out[ev["accession"]] = ev
    return sorted(out.values(), key=lambda e: (e["filed"], e["accession"]))


def per_year(events: list[dict]) -> dict[str, Counter]:
    table: dict[str, Counter] = {}
    for e in events:
        table.setdefault(e["form"], Counter())[e["filed"][:4]] += 1
    return table


def write_csv(events: list[dict], path: Path = OUT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(events)


def fetch_meta(cik: str, fetch: Callable[[str], str] = edgar.fetch) -> dict:
    try:
        j = json.loads(fetch(SUBMISSIONS.format(cik=int(cik))))
    except (edgar.EdgarError, ValueError) as exc:        # ValueError: a throttle or error page that is not JSON
        return {"error": str(exc)}
    return {"sic": j.get("sic"), "sic_desc": j.get("sicDescription"), "tickers": j.get("tickers") or [],
            "exchanges": [x for x in (j.get("exchanges") or []) if x], "entity": j.get("entityType")}


def is_listed(meta: dict) -> bool:
    return bool(LISTED & set(meta.get("exchanges") or []))


def enrich(ciks: Iterable[str], fetch: Callable[[str], str] = edgar.fetch, path: Path = META, save_every: int = 100) -> dict[str, dict]:
    """Fill the metadata cache for every CIK not yet fetched OK (earlier errors are retried). Resumable: saves as it goes."""
    meta: dict[str, dict] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    todo = [c for c in sorted(set(ciks), key=int) if "sic" not in meta.get(c, {})]
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        for n, cik in enumerate(todo, 1):
            meta[cik] = fetch_meta(cik, fetch)
            if n % save_every == 0:
                path.write_text(json.dumps(meta), encoding="utf-8")
    finally:
        path.write_text(json.dumps(meta), encoding="utf-8")       # whatever was fetched is never lost
    return meta


def listed_per_year(events: list[dict], meta: dict[str, dict]) -> dict[str, Counter]:
    table: dict[str, Counter] = {}
    for e in events:
        if is_listed(meta.get(e["cik"], {})):
            table.setdefault(e["form"], Counter())[e["filed"][:4]] += 1
    return table


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "enrich":
        return main_enrich()
    first = int(args[0]) if args else FIRST_YEAR
    skipped: list[str] = []
    events = scan(first, date.today(), skipped=skipped)
    for note in skipped:
        print(f"skipped running quarter, not usable yet: {note}")
    write_csv(events)
    table = per_year(events)
    years = sorted({y for c in table.values() for y in c})
    print(f"{'form':10} " + " ".join(f"{y:>6}" for y in years))
    for form in WATCH:
        print(f"{form:10} " + " ".join(f"{table.get(form, Counter())[y]:>6}" for y in years))
    fund = Counter(e["filed"][:4] for e in events if e["form"] == "SC TO-I" and e["fund_like"])
    print(f"{'TO-I fund?':10} " + " ".join(f"{fund[y]:>6}" for y in years) + "   (name hint only)")
    print(f"{len(events)} events -> {OUT}")
    return 0


def main_enrich() -> int:
    events = list(csv.DictReader(OUT.open(encoding="utf-8")))
    ciks = {e["cik"] for e in events if e["form"] in ENRICH_FORMS}
    meta = enrich(ciks)
    bad = [c for c in ciks if "sic" not in meta[c]]
    for e in events:
        e["fund_like"] = e["fund_like"] == "True"
    table = listed_per_year([e for e in events if e["form"] in ENRICH_FORMS], meta)
    years = sorted({y for c in table.values() for y in c})
    print("filer listed on a US exchange TODAY (lower bound for mergers):")
    print(f"{'form':10} " + " ".join(f"{y:>6}" for y in years))
    for form in ENRICH_FORMS:
        print(f"{form:10} " + " ".join(f"{table.get(form, Counter())[y]:>6}" for y in years))
    print(f"{len(ciks)} filers, {len(bad)} without metadata (rerun to retry)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
