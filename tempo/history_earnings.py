"""C2 kill filter: does a large post-earnings price reaction drift further over 5 days, 2010 to 2025, net of nothing, gross?

It can only KILL a band. The sample is today's listed tickers, so delisted and bankrupt names are missing: that flatters the long
leg and understates the short leg, the bias has no known sign for the spread, and a band that passes proves nothing (it still goes to
the forward test). A band whose gross drift is below its registered cost is dropped (plan C2: 20 bps large, 60 bps small).

Same event and same reaction measure as the live sources (their frozen `measure` is reused, not copied). The one difference is the
trading calendar: history uses the SPY bar dates, because tempo.hours only knows 2026 and later.
  event      8-K item 2.02, accepted outside 09:30-16:00 ET (intraday filings are skipped, as live)
  signal day first SPY bar date on or after the event whose close has the reaction (live: the day the signal is recorded)
  drift      signed excess over SPY from the signal-day close to the close 5 SPY sessions later (gross, no cost, no beta hedge)
Standard error: day cohorts, Newey-West with lag horizon - 1, as in tempo.sequential.

Usage (needs Gateway for the bars, SEC_USER_AGENT for EDGAR; resumable, everything is cached under data/history/earnings):
  python -m tempo.history_earnings fetch [N_TICKERS]     default 1500, a fixed-seed sample of today's tickers
  python -m tempo.history_earnings report
"""
from __future__ import annotations

import csv
import json
import math
import random
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from statistics import fmean
from typing import Callable
from zoneinfo import ZoneInfo

from tempo import earnings_reaction as large
from tempo import earnings_reaction_small as small
from tempo.earnings_reaction import DayBars, measure
from tempo.sequential import hac_variance_of_mean

ET = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[1]
HIST = ROOT / "data" / "history" / "earnings"
FIRST, LAST = date(2010, 1, 1), date(2025, 12, 31)
HORIZON = 5
SEED = 20261113
SAMPLE = 1500
COSTS = {"large": large.ROUND_TRIP_COST, "small": small.ROUND_TRIP_COST}
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
OLDER = "https://data.sec.gov/submissions/{name}"
TICKERS = "https://www.sec.gov/files/company_tickers.json"
MIN_DAYS = 30


# ---- EDGAR: 8-K item 2.02 with acceptance time -------------------------------------------------------------------------------

def block_filings(block: dict) -> list[tuple[str, datetime]]:
    """(accession, acceptance time in ET) of every 8-K with item 2.02 in one submissions block. Refuses ragged arrays."""
    keys = ("form", "items", "accessionNumber", "acceptanceDateTime")
    cols = [block[k] for k in keys]
    if len({len(c) for c in cols}) != 1:
        raise ValueError(f"submissions block has columns of different lengths: {[len(c) for c in cols]}")
    out = []
    for form, items, acc, when in zip(*cols):
        if form == "8-K" and "2.02" in str(items).split(","):
            out.append((acc, datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(ET)))
    return out


def earnings_filings(sub: dict, older: Callable[[str], dict], first: date = FIRST, last: date = LAST) -> list[tuple[str, datetime]]:
    """All item 2.02 8-Ks accepted between `first` and `last`, following the older-filings files only when they overlap the range."""
    found = block_filings(sub["filings"]["recent"])
    for f in sub["filings"].get("files", []):
        if date.fromisoformat(f["filingTo"]) >= first and date.fromisoformat(f["filingFrom"]) <= last:
            found += block_filings(older(f["name"]))
    return sorted({a: t for a, t in found if first <= t.date() <= last}.items(), key=lambda x: x[1])


# ---- the event and its outcome -----------------------------------------------------------------------------------------------

def signal_day(accepted: datetime, calendar: list[str]) -> str | None:
    """The bar date that carries the reaction, or None for a filing accepted during the session. `calendar` is sorted SPY dates."""
    local = accepted.astimezone(ET)
    day, t = local.date().isoformat(), local.time()
    if day in calendar:
        if t < large.OPEN:
            return day
        if t < large.CLOSE:
            return None
    later = [d for d in calendar if d > day]
    return later[0] if later else None


def forward_excess(stock: DayBars, spy: DayBars, day: str, direction: int, horizon: int = HORIZON) -> float | None:
    """Signed excess return over SPY from the close of `day` to the close `horizon` SPY sessions later. None if a bar is missing."""
    if day not in spy.dates:
        return None
    j = spy.dates.index(day)
    if j + horizon >= len(spy.dates):
        return None
    end = spy.dates[j + horizon]
    if day not in stock.dates or end not in stock.dates:
        return None
    s0, s1 = stock.close[stock.dates.index(day)], stock.close[stock.dates.index(end)]
    b0, b1 = spy.close[j], spy.close[j + horizon]
    return direction * ((s1 / s0 - 1) - (b1 / b0 - 1))


def band_and_direction(m: dict) -> tuple[str, int] | None:
    for band, mod in (("large", large), ("small", small)):
        direction = mod.decide(m)
        if direction is not None:
            return band, direction
    return None


def events_for_symbol(symbol: str, filings: list[tuple[str, datetime]], stock: DayBars, spy: DayBars) -> list[dict]:
    rows = []
    for acc, accepted in filings:
        day = signal_day(accepted, spy.dates)
        if day is None:
            continue
        m = measure(stock, spy, day)
        picked = band_and_direction(m) if m.get("status") == "ok" else None
        if picked is None:
            continue
        band, direction = picked
        rows.append({"symbol": symbol, "accession": acc, "day": day, "band": band, "direction": direction, "reaction": m["reaction"],
                     "adv20": m["adv20"], "drift": forward_excess(stock, spy, day, direction)})
    return rows


# ---- the verdict -------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class BandResult:
    band: str
    events: int
    days: int
    mean: float | None
    ci: tuple[float, float] | None
    cost: float
    verdict: str


def evaluate(rows: list[dict], band: str, direction: int | None = None) -> BandResult:
    """Mean over day cohorts of the signed drift, with a Newey-West interval, against the band's registered cost."""
    cost = COSTS[band]
    by_day: dict[str, list[float]] = defaultdict(list)
    n = 0
    for r in rows:
        if r["band"] == band and r["drift"] is not None and (direction is None or r["direction"] == direction):
            by_day[r["day"]].append(r["drift"])
            n += 1
    cohort = [fmean(v) for _, v in sorted(by_day.items())]
    if len(cohort) < MIN_DAYS:
        return BandResult(band, n, len(cohort), None, None, cost, f"too few days ({len(cohort)} < {MIN_DAYS}): no verdict")
    mean = fmean(cohort)
    se = math.sqrt(hac_variance_of_mean(cohort, HORIZON - 1))
    ci = (mean - 1.96 * se, mean + 1.96 * se)
    if mean < cost:
        verdict = "KILL: mean gross drift is below the registered cost" + (" (and the interval agrees)" if ci[1] < cost else "")
    else:
        verdict = "not killed (a pass proves nothing: survivorship, no cost or hedge applied)"
    return BandResult(band, n, len(cohort), mean, ci, cost, verdict)


def by_year(rows: list[dict], band: str) -> dict[str, tuple[int, float]]:
    out: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r["band"] == band and r["drift"] is not None:
            out[r["day"][:4]].append(r["drift"])
    return {y: (len(v), fmean(v)) for y, v in sorted(out.items())}


def render(rows: list[dict]) -> str:
    lines = [f"events measured: {sum(r['drift'] is not None for r in rows)} of {len(rows)} (the rest have no 5-day forward bar)"]
    for band in COSTS:
        for label, d in (("both", None), ("long", 1), ("short", -1)):
            res = evaluate(rows, band, d)
            if res.mean is None or res.ci is None:
                lines.append(f"{band:6} {label:5} n={res.events:>5} days={res.days:>4}  {res.verdict}")
            else:
                lines.append(f"{band:6} {label:5} n={res.events:>5} days={res.days:>4} mean {res.mean:+.2%} "
                             f"[{res.ci[0]:+.2%},{res.ci[1]:+.2%}] cost {res.cost:.2%}  {res.verdict}")
        years = by_year(rows, band)
        lines.append("       by year: " + "  ".join(f"{y} {m:+.1%}({n})" for y, (n, m) in years.items()))
    return "\n".join(lines)


# ---- cache and glue ----------------------------------------------------------------------------------------------------------

def save_bars(path: Path, bars: DayBars) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(("date", "close", "volume"))
        w.writerows(zip(bars.dates, bars.close, bars.volume))


def load_bars(path: Path) -> DayBars | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return DayBars([r["date"] for r in rows], [float(r["close"]) for r in rows], [float(r["volume"]) for r in rows])


def load_sample(path: Path = HIST / "sample.json") -> list[list]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def pick_sample(mapping: dict, n: int, seed: int = SEED) -> list[list]:
    """[[cik, ticker]] for n tickers drawn with a fixed seed from the SEC ticker file (letters only, one ticker per CIK)."""
    pairs = sorted((int(c), t) for c, t in large._ticker_for_cik(mapping).items())
    return [[c, t] for c, t in random.Random(seed).sample(pairs, min(n, len(pairs)))]


def collect_rows(sample: list[list], hist: Path = HIST) -> list[dict]:  # pragma: no cover - reads the cache
    spy = load_bars(hist / "bars" / "SPY.csv")
    if spy is None:
        raise RuntimeError("no cached SPY bars: run fetch first")
    rows: list[dict] = []
    for cik, symbol in sample:
        stock = load_bars(hist / "bars" / f"{symbol}.csv")
        sub_path = hist / "submissions" / f"{int(cik):010d}.json"
        if stock is None or not sub_path.exists():
            continue
        sub = json.loads(sub_path.read_text(encoding="utf-8"))
        older = lambda name: json.loads((hist / "submissions" / name).read_text(encoding="utf-8"))  # noqa: E731
        rows += events_for_symbol(symbol, earnings_filings(sub, older), stock, spy)
    return rows


def fetch_all(n: int) -> int:  # pragma: no cover - network and Gateway
    import dataclasses
    import time

    from dotenv import load_dotenv

    from tempo import edgar
    from tempo.config import load_config
    from tempo.ibkr import connect
    from ib_async import Stock
    load_dotenv()
    sample_path = HIST / "sample.json"
    if not sample_path.exists():
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        sample_path.write_text(json.dumps(pick_sample(json.loads(edgar.fetch(TICKERS)), n)), encoding="utf-8")
    sample = load_sample()
    ib = connect(dataclasses.replace(load_config(), client_id=97))      # a client id of its own: never collides with the cron jobs
    ib.RequestTimeout = 60
    done = skipped = 0
    try:
        for cik, symbol in [[0, "SPY"], *sample]:
            bars_path = HIST / "bars" / f"{symbol}.csv"
            if symbol != "SPY":
                sub_path = HIST / "submissions" / f"{int(cik):010d}.json"
                if not sub_path.exists():
                    sub_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        sub_path.write_text(edgar.fetch(SUBMISSIONS.format(cik=int(cik))), encoding="utf-8")
                    except edgar.EdgarError as exc:
                        print(f"{symbol}: no submissions ({exc})")
                        continue
                sub = json.loads(sub_path.read_text(encoding="utf-8"))
                for f in sub["filings"].get("files", []):
                    p = HIST / "submissions" / f["name"]
                    if not p.exists() and date.fromisoformat(f["filingTo"]) >= FIRST:
                        p.write_text(edgar.fetch(OLDER.format(name=f["name"])), encoding="utf-8")
                if not earnings_filings(sub, lambda name: json.loads((HIST / "submissions" / name).read_text(encoding="utf-8"))):
                    skipped += 1
                    continue
            if bars_path.exists() or (HIST / "bars" / f"{symbol}.none").exists():
                continue
            contract = Stock(symbol, "SMART", "USD")
            if not ib.qualifyContracts(contract):
                (HIST / "bars").mkdir(parents=True, exist_ok=True)
                (HIST / "bars" / f"{symbol}.none").write_text("not qualified", encoding="utf-8")
                continue
            raw = ib.reqHistoricalData(contract, "", "16 Y", "1 day", "TRADES", useRTH=True, formatDate=1)
            if not raw:
                (HIST / "bars" / f"{symbol}.none").write_text("no bars", encoding="utf-8")
                continue
            save_bars(bars_path, DayBars([str(b.date) for b in raw], [float(b.close) for b in raw], [float(b.volume) for b in raw]))
            done += 1
            if done % 50 == 0:
                print(f"{done} bar files fetched")
            time.sleep(0.3)
    finally:
        ib.disconnect()
    print(f"fetched {done} bar files; {skipped} tickers have no item 2.02 filing in range")
    return 0


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - entry point
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "fetch":
        return fetch_all(int(args[1]) if len(args) > 1 else SAMPLE)
    if args and args[0] == "report":
        sample = load_sample()
        if not sample:
            raise SystemExit("no sample.json: run fetch first")
        print(render(collect_rows(sample)))
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
