"""Read-only count of structural-event filings on SEC EDGAR (issuer tender offers, closed-end-fund repurchase notices,
merger proxies, spin-off registrations). It places no orders and changes no rule: it turns guesses about how many such
events exist per year into measured counts, with accession numbers, so a later pre-registration can set real sample sizes.

Source: EDGAR's quarterly form index (https://www.sec.gov/Archives/edgar/full-index/YYYY/QTRn/form.gz), which lists every
filing by form type. (The full-text-search host efts.sec.gov answers 403 to this client, so it is not used.) A completed
quarter is cached under data/events/index/ and never fetched twice; the running quarter is re-fetched every time.
The company-name hint (`fund_like`) is a crude regex, not a classification; a SIC lookup is a later step.

Usage: python -m tempo.events_scan [FIRST_YEAR]   (default 2019) -> data/events/events.csv and a per-year table.
"""
from __future__ import annotations

import csv
import gzip
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterable
from datetime import date
from pathlib import Path

from tempo import edgar

INDEX_URL = "https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{q}/form.gz"
CACHE = Path("data/events/index")
OUT = Path("data/events/events.csv")
FIRST_YEAR = 2019
# Original filings only: amendments (form type ending "/A") are the same event again and are never counted.
WATCH = ("SC TO-I", "10-12B", "DEFM14A", "SC 13E3", "N-23C3A", "N-23C3B", "N-23C-3")
FUND_HINT = re.compile(r"\b(fund|trust|portfolio|strategies|partners|opportunit\w*|income)\b", re.IGNORECASE)
ROW = re.compile(r"^(?P<form>\S.*?)\s{2,}(?P<name>.+?)\s+(?P<cik>\d{1,10})\s+(?P<filed>\d{4}-\d{2}-\d{2})\s+(?P<path>\S+)\s*$")
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
    end_month = 3 * q
    nxt = date(year + (end_month == 12), end_month % 12 + 1, 1)
    return nxt <= today


def load_quarter(year: int, q: int, today: date, fetch: Callable[[str], bytes] = edgar.fetch_bytes, cache: Path = CACHE) -> list[dict]:
    path = cache / f"{year}Q{q}.form.gz"
    done = quarter_complete(year, q, today)
    if path.exists() and done:
        raw = path.read_bytes()
    else:
        raw = fetch(INDEX_URL.format(year=year, q=q))
        try:
            gzip.decompress(raw)
        except OSError as exc:
            raise FormIndexError(f"{year} Q{q}: not a gzip file ({exc})") from exc
        if done:
            cache.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    return parse_form_index(gzip.decompress(raw).decode("latin-1"))


def scan(first_year: int, today: date, fetch: Callable[[str], bytes] = edgar.fetch_bytes, cache: Path = CACHE) -> list[dict]:
    out: dict[str, dict] = {}
    for year, q in quarters(first_year, today):
        for ev in load_quarter(year, q, today, fetch, cache):
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


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    first = int(args[0]) if args else FIRST_YEAR
    events = scan(first, date.today())
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


if __name__ == "__main__":
    raise SystemExit(main())
