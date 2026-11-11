"""Which insiders are "routine" buyers (evidence/insider_opportunistic_forward.json), from the SEC Insider Transactions
Data Sets: one quarterly zip of every Form 3/4/5, free.

Usage: python -m tempo.insider_history build [YEAR ...]      default: the three calendar years before this one.
Writes data/insider_routine.json: for each officer/director (CIK without leading zeros), the months (YYYY-MM) in
which they made a counted open-market purchase. About 10 MB is downloaded per quarter; zips are kept in
data/insider_sets/ so a rebuild does not download again.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Iterator

DATA = Path(__file__).resolve().parents[1] / "data"
INDEX_FILE = DATA / "insider_routine.json"
SETS_DIR = DATA / "insider_sets"
SETS_URL = "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{quarter}_form345.zip"
LETTERS = re.compile(r"^[A-Z]{1,5}$")
YEARS_BACK = 3


class HistoryMissing(RuntimeError):
    """The routine index does not cover the years a decision needs. Never guess: build it first."""


def _cik(raw: str) -> str:
    return raw.strip().lstrip("0")


def _rows(z: zipfile.ZipFile, name: str) -> Iterator[dict]:
    with z.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, "utf-8", errors="replace"), delimiter="\t", quoting=csv.QUOTE_NONE)


def purchase_months_from_zip(raw: bytes) -> dict[str, set[str]]:
    """Owner CIK -> months with a counted purchase: Form 4 (not an amendment), not 10b5-1, plain letters-only symbol,
    owner an officer or director, transaction code P, acquired, shares and price above zero."""
    z = zipfile.ZipFile(io.BytesIO(raw))
    counted = {r["ACCESSION_NUMBER"] for r in _rows(z, "SUBMISSION.tsv")
               if r["DOCUMENT_TYPE"] == "4" and r["AFF10B5ONE"].strip().lower() not in ("1", "true")
               and LETTERS.match(r["ISSUERTRADINGSYMBOL"].strip().upper() or "-")}
    owners: dict[str, list[str]] = {}
    for r in _rows(z, "REPORTINGOWNER.tsv"):
        roles = r["RPTOWNER_RELATIONSHIP"]
        if r["ACCESSION_NUMBER"] in counted and ("Officer" in roles or "Director" in roles):
            owners.setdefault(r["ACCESSION_NUMBER"], []).append(_cik(r["RPTOWNERCIK"]))
    out: dict[str, set[str]] = {}
    for r in _rows(z, "NONDERIV_TRANS.tsv"):
        acc = r["ACCESSION_NUMBER"]
        if acc not in owners or r["TRANS_CODE"] != "P" or r["TRANS_ACQUIRED_DISP_CD"] != "A":
            continue
        try:
            if float(r["TRANS_SHARES"] or 0) <= 0 or float(r["TRANS_PRICEPERSHARE"] or 0) <= 0:
                continue
            month = datetime.strptime(r["TRANS_DATE"].strip(), "%d-%b-%Y").strftime("%Y-%m")
        except ValueError:
            continue
        for owner in owners[acc]:
            out.setdefault(owner, set()).add(month)
    return out


def build_index(years: list[int], fetch_quarter: Callable[[str], bytes]) -> dict:
    merged: dict[str, set[str]] = {}
    for year in sorted(years):
        for q in (1, 2, 3, 4):
            for owner, months in purchase_months_from_zip(fetch_quarter(f"{year}q{q}")).items():
                merged.setdefault(owner, set()).update(months)
    return {"years": sorted(years), "owners": {k: sorted(v) for k, v in sorted(merged.items())}}


def is_routine(owner_cik: str, year: int, month: int, index: dict) -> bool:
    """Routine = a counted purchase in this calendar month in each of the three previous years (no history: not routine)."""
    needed = [year - k for k in range(1, YEARS_BACK + 1)]
    missing = sorted(set(needed) - set(index.get("years", [])))
    if missing:
        raise HistoryMissing(f"routine history lacks {missing}; run: python -m tempo.insider_history build {' '.join(map(str, sorted(needed)))}")
    months = set(index["owners"].get(_cik(owner_cik), ()))
    return all(f"{y}-{month:02d}" in months for y in needed)


def load_index(path: Path = INDEX_FILE) -> dict:
    if not Path(path).exists():
        raise HistoryMissing(f"{path} not found; run: python -m tempo.insider_history build")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _fetch_quarter(quarter: str) -> bytes:  # pragma: no cover - network
    from tempo.edgar import fetch_bytes
    cached = SETS_DIR / f"{quarter}_form345.zip"
    if not cached.exists():
        SETS_DIR.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(fetch_bytes(SETS_URL.format(quarter=quarter), timeout=300))
    return cached.read_bytes()


def main(argv: list[str]) -> int:  # pragma: no cover - network
    if not argv or argv[0] != "build":
        raise SystemExit("usage: python -m tempo.insider_history build [YEAR ...]")
    years = [int(y) for y in argv[1:]] or [date.today().year - k for k in range(YEARS_BACK, 0, -1)]
    index = build_index(years, lambda q: (print(f"  {q}...", flush=True), _fetch_quarter(q))[1])
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index), encoding="utf-8")
    print(f"routine index: years {index['years']}, {len(index['owners'])} officers/directors with purchases -> {INDEX_FILE}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
