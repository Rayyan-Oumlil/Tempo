"""Free daily data, saved as point-in-time files under data/snapshots/ (the VPS builds a history nobody can sell us).

Usage: python -m tempo.snapshots        (the "late" job runs it on trading days after 19:00 ET; safe to run any number of times)

  finra_short_volume/YYYYMMDD.txt.gz   FINRA Reg SHO consolidated daily short volume, one file per trading day (free, no key)
  fred/VIXCLS.csv, fred/VXVCLS.csv     VIX and its 3-month cousin from FRED (the term structure), rewritten each run
  sec_ftd/cnsfailsYYYYMM{a,b}.zip      SEC fails-to-deliver, twice a month, published about two weeks late

Every fetch is validated before it is kept; a source that is not published yet is reported, a malformed one fails loudly.
"""
from __future__ import annotations

import gzip
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

from tempo.hours import is_trading_day

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"
FINRA_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{day}.txt"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
FTD_URL = "https://www.sec.gov/files/data/fails-deliver-data/cnsfails{ym}{half}.zip"
FINRA_HEADER = "Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market"
FINRA_MIN_ROWS = 4000
BACKFILL_DAYS = 45          # trading days of FINRA history kept on hand; the short-volume signal needs 20 plus margin
FRED_SERIES = ("VIXCLS", "VXVCLS")
FRED_MIN_ROWS = 500


class SnapshotError(RuntimeError):
    pass


class NotPublished(SnapshotError):
    """The source answered 'not there (yet)': normal for today's file before the evening, a problem for an old one."""


Fetch = Callable[[str], bytes]


def http_get(url: str) -> bytes:  # pragma: no cover - network
    req = urllib.request.Request(url, headers={"User-Agent": "TempoResearch/1.0", "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 404):
            raise NotPublished(f"{url}: HTTP {exc.code}") from exc
        raise SnapshotError(f"{url}: HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SnapshotError(f"{url}: {exc!r}") from exc


def parse_short_volume(text: str) -> dict[str, tuple[float, float]]:
    """symbol -> (short volume, total volume). Fails loudly on a changed layout or a truncated file."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines or lines[0].strip() != FINRA_HEADER:
        raise SnapshotError(f"unexpected FINRA header: {lines[0][:80] if lines else 'empty file'}")
    out: dict[str, tuple[float, float]] = {}
    for ln in lines[1:]:
        parts = ln.split("|")
        if len(parts) < 5:   # FINRA may append a trailer line with a row count
            continue
        try:
            short, total = float(parts[2]), float(parts[4])
        except ValueError as exc:
            raise SnapshotError(f"bad FINRA row: {ln[:80]}") from exc
        out[parts[1]] = (short, total)
    if len(out) < FINRA_MIN_ROWS:
        raise SnapshotError(f"FINRA file has only {len(out)} symbols; expected at least {FINRA_MIN_ROWS} (truncated?)")
    return out


def trading_days_back(today: date, n: int) -> list[date]:
    out, d = [], today
    while len(out) < n:
        if is_trading_day(d):
            out.append(d)
        d -= timedelta(days=1)
    return out[::-1]


def collect_finra(today: date, fetch: Fetch = http_get, snap: Path = SNAP, backfill: int = BACKFILL_DAYS) -> dict[str, list[str]]:
    folder = snap / "finra_short_volume"
    folder.mkdir(parents=True, exist_ok=True)
    result: dict[str, list[str]] = {"saved": [], "have": [], "not_published": []}
    for day in trading_days_back(today, backfill):
        target = folder / f"{day:%Y%m%d}.txt.gz"
        if target.exists():
            result["have"].append(day.isoformat())
            continue
        try:
            raw = fetch(FINRA_URL.format(day=f"{day:%Y%m%d}"))
        except NotPublished:
            result["not_published"].append(day.isoformat())
            continue
        parse_short_volume(raw.decode("utf-8", "replace"))      # validate before keeping
        partial = target.with_suffix(".partial")
        partial.write_bytes(gzip.compress(raw))
        partial.replace(target)
        result["saved"].append(day.isoformat())
    return result


def load_short_volume(day: date, snap: Path = SNAP) -> dict[str, tuple[float, float]] | None:
    path = snap / "finra_short_volume" / f"{day:%Y%m%d}.txt.gz"
    if not path.exists():
        return None
    return parse_short_volume(gzip.decompress(path.read_bytes()).decode("utf-8", "replace"))


def collect_fred(fetch: Fetch = http_get, snap: Path = SNAP) -> list[str]:
    folder = snap / "fred"
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for series in FRED_SERIES:
        raw = fetch(FRED_URL.format(series=series))
        rows = [ln for ln in raw.decode("utf-8", "replace").splitlines() if ln.strip()]
        header = rows[0].lower() if rows else ""
        if len(rows) < FRED_MIN_ROWS or not header.startswith(("observation_date,", "date,")):
            raise SnapshotError(f"FRED {series}: unexpected content ({len(rows)} rows, header {header[:40]!r})")
        partial = folder / f"{series}.partial"
        partial.write_bytes(raw)
        partial.replace(folder / f"{series}.csv")
        saved.append(series)
    return saved


def ftd_periods(today: date, n: int = 4) -> list[tuple[str, str]]:
    """The last n half-month periods that could already be published (a period is published about 2 weeks after it ends)."""
    y, m = today.year, today.month
    half = "a"
    if today.day <= 15:          # the previous month's second half is the newest one that can be out
        m -= 1
        half = "b"
        if m == 0:
            y, m = y - 1, 12
    out: list[tuple[str, str]] = []
    while len(out) < n:
        out.append((f"{y}{m:02d}", half))
        if half == "b":
            half = "a"
        else:
            half = "b"
            m -= 1
            if m == 0:
                y, m = y - 1, 12
    return out


def collect_ftd(today: date, fetch: Fetch, snap: Path = SNAP) -> dict[str, list[str]]:
    folder = snap / "sec_ftd"
    folder.mkdir(parents=True, exist_ok=True)
    result: dict[str, list[str]] = {"saved": [], "have": [], "not_published": []}
    for ym, half in ftd_periods(today):
        name = f"cnsfails{ym}{half}.zip"
        if (folder / name).exists():
            result["have"].append(name)
            continue
        try:
            raw = fetch(FTD_URL.format(ym=ym, half=half))
        except NotPublished:
            result["not_published"].append(name)
            continue
        if raw[:2] != b"PK":
            raise SnapshotError(f"{name}: not a zip file")
        (folder / name).write_bytes(raw)
        result["saved"].append(name)
    return result


def main() -> int:  # pragma: no cover - entry point
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from tempo.edgar import EdgarError, fetch_bytes
    today = datetime.now(ZoneInfo("America/New_York")).date()
    problems = []
    finra = collect_finra(today)
    print(f"finra short volume: {len(finra['saved'])} saved, {len(finra['have'])} already had, not yet published: {finra['not_published']}")
    old = [d for d in finra["not_published"] if date.fromisoformat(d) < today - timedelta(days=3)]
    if old:
        problems.append(f"FINRA files missing for older days: {old}")

    def sec_fetch(url: str) -> bytes:
        try:
            return fetch_bytes(url)
        except EdgarError as exc:
            if "HTTP 404" in str(exc) or "HTTP 403" in str(exc):
                raise NotPublished(str(exc)) from exc
            raise SnapshotError(str(exc)) from exc
    ftd = collect_ftd(today, sec_fetch)
    print(f"sec fails-to-deliver: {len(ftd['saved'])} saved, {len(ftd['have'])} already had, not yet published: {ftd['not_published']}")
    print(f"fred: {', '.join(collect_fred())} refreshed")
    if problems:
        print("[FAIL] " + "; ".join(problems), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    try:
        raise SystemExit(main())
    except Exception as err:  # noqa: BLE001 - fail loudly with a clear line, non-zero exit
        print(f"[FAIL] {type(err).__name__}: {err}", file=sys.stderr)
        raise SystemExit(1)
