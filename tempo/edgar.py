"""A small, polite client for SEC EDGAR, used to read earnings releases (8-K item 2.02) and, later, insider purchases.

The SEC's fair-access rules require a User-Agent that identifies the requester (SEC_USER_AGENT in .env, never in the
repo) and at most 10 requests a second; this client stays far below that (one request per 0.25 s) and fails loudly on
any HTTP error instead of retrying in a loop.

Usage: python -m tempo.edgar TICKER [YYYY-MM-DD] [MAX_CHARS | brief]
       prints the text of the company's earnings press release filed that day (default today, New York date).
"""
from __future__ import annotations

import functools
import html
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

MIN_INTERVAL = 0.25
TIMEOUT = 30
EXHIBIT = re.compile(r"ex[-_]?99|dex99", re.IGNORECASE)


class EdgarError(RuntimeError):
    def __init__(self, url: str, why: str):
        super().__init__(f"{url}: {why}")


class Throttle:
    """Keep at least `min_interval` seconds between requests."""

    def __init__(self, min_interval: float = MIN_INTERVAL, clock=time.monotonic, sleep=time.sleep):
        self._min, self._clock, self._sleep, self._last = min_interval, clock, sleep, None

    def wait(self) -> None:
        now = self._clock()
        if self._last is not None and now - self._last < self._min:
            self._sleep(self._min - (now - self._last))
        self._last = self._clock()


_THROTTLE = Throttle()


def fetch(url: str) -> str:
    return fetch_bytes(url).decode("utf-8", "replace")


def fetch_bytes(url: str, timeout: float = TIMEOUT) -> bytes:
    load_dotenv()
    agent = os.environ.get("SEC_USER_AGENT")
    if not agent:
        raise EdgarError(url, "SEC_USER_AGENT is not set in .env (the SEC requires a contact string in the User-Agent)")
    _THROTTLE.wait()
    req = urllib.request.Request(url, headers={"User-Agent": agent, "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as exc:
        raise EdgarError(url, f"HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as exc:
        raise EdgarError(url, repr(exc)) from exc


def cik_for(ticker: str, mapping: dict) -> str | None:
    """Ten-digit CIK for a ticker from the SEC's company_tickers.json, or None."""
    for entry in mapping.values():
        if entry["ticker"].upper() == ticker.upper():
            return f"{int(entry['cik_str']):010d}"
    return None


def select_earnings_filing(submissions: dict, date: str) -> dict | None:
    """The 8-K with item 2.02 (results of operations) that the company filed on `date`, or None."""
    r = submissions["filings"]["recent"]
    for i, form in enumerate(r["form"]):
        if form == "8-K" and r["filingDate"][i] == date and "2.02" in r["items"][i].split(","):
            return {"accession": r["accessionNumber"][i], "filing_date": date, "accepted": r["acceptanceDateTime"][i],
                    "primary": r["primaryDocument"][i]}
    return None


def pick_exhibit(index_html: str, fallback: str) -> str:
    """URL of the press release exhibit (type EX-99.x) in a filing's HTML index page, else `fallback`.

    The index lists every document with its official type; file names are not predictable (Amgen's release is
    'amgn-20260930earningsrelea.htm'), so the type column is the only reliable key.
    """
    for row in re.findall(r"(?is)<tr\b.*?</tr>", index_html):
        cells = [re.sub(r"(?s)<[^>]+>", "", c).replace("&nbsp;", " ").strip() for c in re.findall(r"(?is)<td\b.*?</td>", row)]
        link = re.search(r'href="([^"]+)"', row)
        if len(cells) >= 4 and cells[3].upper().startswith("EX-99") and link:
            path = link.group(1).replace("/ix?doc=", "")
            return path if path.startswith("http") else "https://www.sec.gov" + path
    return fallback


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)</(p|div|tr|h[1-6]|li|br)\s*>|<br\s*/?>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw)).replace("\xa0", " ")
    lines = (re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


GUIDANCE = re.compile(r"(?i)\b(guidance|outlook|expects?|raises?|raised|lowers?|lowered|reaffirm\w*|forecast)\b")


def brief_text(text: str, head: int = 2200, max_lines: int = 6) -> str:
    """The start of a release plus the lines that talk about guidance or outlook (kept short to limit reading effort)."""
    hits = [line[:300] for line in text.split("\n") if GUIDANCE.search(line)]
    return text[:head] + "\n--- guidance lines ---\n" + "\n".join(hits[:max_lines])


@functools.lru_cache(maxsize=1)
def _ticker_map() -> dict:
    return json.loads(fetch("https://www.sec.gov/files/company_tickers.json"))


def earnings_release(ticker: str, date: str) -> dict | None:
    """Text and metadata of `ticker`'s earnings press release filed on `date`, or None if there is none (yet)."""
    cik = cik_for(ticker, _ticker_map())
    if cik is None:
        raise EdgarError(ticker, "ticker not found in the SEC's company_tickers.json")
    filing = select_earnings_filing(json.loads(fetch(f"https://data.sec.gov/submissions/CIK{cik}.json")), date)
    if filing is None:
        return None
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{filing['accession'].replace('-', '')}"
    url = pick_exhibit(fetch(f"{base}/{filing['accession']}-index.htm"), fallback=f"{base}/{filing['primary']}")
    return {**filing, "url": url, "text": html_to_text(fetch(url))}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # filings contain characters a Windows console cannot show
    try:
        ticker = sys.argv[1]
        date = sys.argv[2] if len(sys.argv) > 2 else datetime.now(ZoneInfo("America/New_York")).date().isoformat()
        mode = sys.argv[3] if len(sys.argv) > 3 else "4000"
        rel = earnings_release(ticker, date)
        if rel is None:
            print(f"NO EARNINGS 8-K FOR {ticker} ON {date} (not filed yet, or no item 2.02)")
        else:
            body = brief_text(rel["text"]) if mode == "brief" else rel["text"][:int(mode)]
            print(f"{ticker} filed {rel['accepted']}  {rel['url']}\n---\n{body}")
    except (IndexError, EdgarError, ValueError) as err:
        print(f"[FAIL] {err}", file=sys.stderr)
        raise SystemExit(1)
