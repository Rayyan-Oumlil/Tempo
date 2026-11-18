"""Workstream N4a: the registered B4 news legs replayed on the FNSPID headline archive (protocol frozen 2026-11-17 in docs/plan-quant-v2.md).

  python -m tempo.history_news extract   stream data/news_history/All_external.csv into data/news_history/headlines.tsv.gz (no network)
  python -m tempo.history_news report    join headlines to >=5% moves, score exec_v2 excess, rule-7 verdicts, placebo, Benjamini-Hochberg

Pure functions first (tested); the two commands at the bottom only read and write local files. Nothing is fitted.
"""
from __future__ import annotations

import csv
import gzip
import json
import random
import sys
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from tempo.autopsy import bh_threshold, p_value
from tempo.daybars import liquid
from tempo.history_core import Series, Trade, Verdict, judge, load_series, trade_excess
from tempo.news_labels import clean, label, roundup_texts

DATA = Path(__file__).resolve().parents[1] / "data"
SRC = DATA / "news_history" / "All_external.csv"
TSV = DATA / "news_history" / "headlines.tsv.gz"
REPORT = DATA / "history" / "news_history_report.json"
NY = ZoneInfo("America/New_York")

MOVE = 0.05
COST = 0.002
HORIZON = 5
DEDUP_DAYS = 30
MIN_SYMBOL_YEAR = 50
FIRST_YEAR, LAST_YEAR = 2016, 2023
TEST_YEARS = ("2019", "2020")  # AMENDMENT 2: the archive has no headlines after 2020
NOT_COUNTED = ("roundup", "auto_move")
TRIALS = ("news_any", "news_substantive", "news_analyst", "news_press_release", "news_filing", "no_news_fade")
PLACEBO_SHIFT_DAYS = 30
PLACEBO_SEED = 20261117


def parse_utc(stamp: str) -> datetime | None:
    """'2020-06-05 06:30:54 UTC' -> aware UTC datetime; None when malformed. A stamp of exactly 00:00:00 means 'date only' (AMENDMENT 1)."""
    try:
        return datetime.fromisoformat(stamp[:19]).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def is_date_only(utc: datetime) -> bool:
    return (utc.hour, utc.minute, utc.second) == (0, 0, 0)


def session_of(utc: datetime, calendar: list[str]) -> str | None:
    """The trading session whose window (previous 16:00 ET to this 16:00 ET) contains the headline; None past the end of the calendar."""
    if is_date_only(utc):  # AMENDMENT 1: first session on or after the stated date (no time zone shift: the date is the whole information)
        i = bisect_left(calendar, utc.date().isoformat())
        return calendar[i] if i < len(calendar) else None
    et = utc.astimezone(NY)
    day = et.date().isoformat()
    after_close = (et.hour, et.minute, et.second) > (16, 0, 0)
    i = bisect_right(calendar, day) if after_close else bisect_left(calendar, day)
    return calendar[i] if i < len(calendar) else None


def moves(stock: Series, spy: Series, threshold: float = MOVE) -> list[tuple[str, float]]:
    """(day, stock return minus SPY return) for every liquid session whose close-to-close excess is at least `threshold` in size."""
    out = []
    for i in range(1, len(stock.dates)):
        d, prev = stock.dates[i], stock.dates[i - 1]
        k = spy.pos.get(d)
        if k is None or k == 0 or spy.dates[k - 1] != prev:
            continue
        if min(stock.close[max(0, i - 21):i + 1]) <= 0:  # a zero or negative price in the window is a data error, never a move (the report counts such symbols)
            continue
        excess = (stock.close[i] / stock.close[i - 1] - 1) - (spy.close[k] / spy.close[k - 1] - 1)
        if abs(excess) >= threshold and liquid(stock, d)["status"] == "ok":  # type: ignore[arg-type]  # duck-typed: dates, close, volume
            out.append((d, excess))
    return out


def trial_membership(labels: frozenset[str], symbol_year_headlines: int) -> tuple[str, ...]:
    """Which trials an event with these counted-headline labels belongs to. no_news_fade needs a covered symbol-year (rule 3)."""
    counted = labels - set(NOT_COUNTED)
    member = []
    if counted:
        member.append("news_any")
        member.extend(f"news_{lab}" for lab in ("substantive", "analyst", "press_release", "filing") if lab in counted)
    elif symbol_year_headlines >= MIN_SYMBOL_YEAR:
        member.append("no_news_fade")
    return tuple(member)


def dedupe(events: list[tuple[str, str]], days: int = DEDUP_DAYS) -> list[tuple[str, str]]:
    """Keep the first event per symbol, then skip further events of that symbol within `days` calendar days. Input (symbol, day) in any order."""
    last: dict[str, date] = {}
    kept = []
    for symbol, day in sorted(events, key=lambda e: (e[1], e[0])):
        d = date.fromisoformat(day)
        if symbol in last and (d - last[symbol]).days < days:
            continue
        last[symbol] = d
        kept.append((symbol, day))
    return kept


def earnings_days(filings: dict, sessions: list[str]) -> tuple[set[str], str | None]:
    """Sessions treated as earnings days (an 8-K item 2.02 filed that session or the one before) and the first date the filing list covers."""
    recent = filings.get("filings", {}).get("recent", {})
    dates = recent.get("filingDate", [])
    first = min(dates) if dates else None
    out: set[str] = set()
    for form, items, filed in zip(recent.get("form", []), recent.get("items", []), dates):
        if form != "8-K" or "2.02" not in str(items).split(","):
            continue
        i = bisect_left(sessions, filed)
        if i < len(sessions):
            out.add(sessions[i])
            if i + 1 < len(sessions):
                out.add(sessions[i + 1])
    return out, first


def to_trade(stock: Series, spy: Series, day: str, excess: float, trial: str) -> Trade | None:
    """exec_v2 trade for a signal at the close of `day`: entry next session open, exit HORIZON sessions after the entry. Fade is the opposite direction."""
    k = spy.pos.get(day)
    if k is None or k + 1 >= len(spy.dates):
        return None
    entry = spy.dates[k + 1]
    direction = (1 if excess > 0 else -1) * (-1 if trial == "no_news_fade" else 1)
    gross = trade_excess(stock, spy, entry, direction, HORIZON)
    return None if gross is None else Trade(entry, "", gross)


def two_sided_p(v: Verdict) -> float:
    return 1.0 if v.t is None else p_value(v.t)


def bh_flags(verdicts: dict[str, Verdict]) -> dict[str, bool]:
    """Benjamini-Hochberg at 10% across the trials: True where a trial's p is within the passing threshold."""
    thr = bh_threshold([two_sided_p(v) for v in verdicts.values()])
    return {k: thr is not None and two_sided_p(v) <= thr for k, v in verdicts.items()}


# --- local-file commands --------------------------------------------------------------------------------------------------

def bar_files() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for d in (DATA / "history" / "fast" / "bars", DATA / "history" / "shortvol" / "bars"):
        for p in d.glob("*.csv"):
            found.setdefault(p.stem, p)
    return found


def extract() -> int:  # pragma: no cover - reads the 5 GB archive
    csv.field_size_limit(2**31 - 1)
    symbols = set(bar_files())
    kept: Counter[str] = Counter()
    TSV.parent.mkdir(parents=True, exist_ok=True)
    tmp = TSV.with_suffix(".tmp")
    with SRC.open(encoding="utf-8", errors="replace", newline="") as f, gzip.open(tmp, "wt", encoding="utf-8", newline="") as out:
        r = csv.reader(f)
        header = next(r)
        di, ti, si, pi = (header.index(c) for c in ("Date", "Article_title", "Stock_symbol", "Publisher"))
        for n, row in enumerate(r, 1):
            if n % 1_000_000 == 0:
                print(f"  {n:,} rows read, {kept['kept']:,} kept", flush=True)
            if len(row) <= max(di, ti, si, pi):
                kept["short_row"] += 1
                continue
            sym = row[si].strip()
            if sym not in symbols:
                kept["other_symbol"] += 1
                continue
            utc = parse_utc(row[di])
            if utc is None:
                kept["bad_date"] += 1
                continue
            if not FIRST_YEAR <= utc.year <= LAST_YEAR:
                kept["outside_years"] += 1
                continue
            title = " ".join(row[ti].split())
            kept["date_only" if is_date_only(utc) else "timed"] += 1
            out.write(f"{utc:%Y-%m-%dT%H:%M:%S}\t{sym}\t{row[pi].strip().replace(chr(9), ' ')}\t{title.replace(chr(9), ' ')}\n")
            kept["kept"] += 1
    tmp.replace(TSV)
    print(dict(kept))
    return 0


def load_headlines() -> list[tuple[datetime, str, str, str]]:  # pragma: no cover
    rows = []
    with gzip.open(TSV, "rt", encoding="utf-8") as f:
        for line in f:
            ts, sym, pub, title = line.rstrip("\n").split("\t", 3)
            rows.append((datetime.fromisoformat(ts).replace(tzinfo=timezone.utc), sym, pub, title))
    return rows


def label_headlines(rows, calendar: list[str], shift_days: int = 0, rng: random.Random | None = None):  # pragma: no cover
    """(symbol, session) -> set of labels, and symbol -> year -> headline count. A placebo moves every headline by a random +-shift_days."""
    by_day: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for utc, sym, _pub, title in rows:
        by_day[utc.date().isoformat()].append((sym, clean(title)))
    roundups = {d: roundup_texts(v) for d, v in by_day.items()}
    labels: dict[tuple[str, str], set[str]] = defaultdict(set)
    year_counts: dict[str, Counter] = defaultdict(Counter)
    for utc, sym, _pub, title in rows:
        at = utc + timedelta(days=rng.randint(-shift_days, shift_days)) if shift_days and rng else utc
        sess = session_of(at, calendar)
        if sess is None:
            continue
        labels[(sym, sess)].add(label(title, roundups[utc.date().isoformat()]))
        year_counts[sym][sess[:4]] += 1
    return labels, year_counts


def build_trades(universe: dict[str, Series], spy: Series, labels, year_counts, earn) -> tuple[dict[str, list[Trade]], Counter]:  # pragma: no cover
    counts: Counter = Counter()
    events: dict[str, list[tuple[str, str]]] = defaultdict(list)
    sizes: dict[tuple[str, str], float] = {}
    for sym, stock in universe.items():
        if any(c <= 0 for c in stock.close):
            counts["symbols_with_nonpositive_close"] += 1
        ed, first = earn.get(sym, (set(), None))
        for day, excess in moves(stock, spy):
            if day in ed:
                counts["earnings_day_excluded"] += 1
                continue
            if first is None or day < first:
                counts["earnings_unknown_kept"] += 1
            if not "2017" <= day[:4] <= str(LAST_YEAR):
                continue
            for trial in trial_membership(frozenset(labels.get((sym, day), ())), year_counts[sym][day[:4]]):
                events[trial].append((sym, day))
                sizes[(trial + sym, day)] = excess
    trades: dict[str, list[Trade]] = {}
    for trial, evs in events.items():
        out = []
        for sym, day in dedupe(evs):
            t = to_trade(universe[sym], spy, day, sizes[(trial + sym, day)], trial)
            counts[f"{trial}:{'scored' if t else 'unscored'}"] += 1
            if t:
                out.append(Trade(t.day, sym, t.gross))
        trades[trial] = out
    return trades, counts


def render(rows: dict[str, dict]) -> str:  # pragma: no cover
    lines = ["N4a NEWS HISTORY VERDICTS (FNSPID headlines; entries 2019-2020; 5-session horizon; net of 0.20%; protocol frozen 2026-11-17)", ""]
    for name, r in rows.items():
        v: Verdict = r["verdict"]
        if v.mean_net is None or v.ci is None or v.mean_net_stress is None:
            lines.append(f"{name:20s} events {v.events:5d}  {v.decision}: {'; '.join(v.reasons)}")
            continue
        t = f"{v.t:.2f}" if v.t is not None else "n/a"
        lines.append(f"{name:20s} events {v.events:5d}  net {v.mean_net:+.2%} [{v.ci[0]:+.2%}, {v.ci[1]:+.2%}]  t {t}  1.5x {v.mean_net_stress:+.2%}  "
                     f"BH {'pass' if r['bh'] else 'no'}  => {v.decision}" + (f" ({'; '.join(v.reasons)})" if v.reasons else ""))
        lines.append("                     by year: " + "  ".join(f"{y} {m:+.2%} ({n})" for y, (n, m) in v.years.items()) + f"   placebo: {r['placebo']}")
    return "\n".join(lines)


def report() -> int:  # pragma: no cover
    from tempo.history_report import load_spy
    spy = load_spy()
    files = bar_files()
    universe = {s: b for s, p in files.items() if (b := load_series(p)) is not None and s != "SPY"}
    rows = load_headlines()
    print(f"{len(rows):,} headlines, {len(universe)} symbols with bars", flush=True)
    earn = {}
    for p in (DATA / "history" / "earnings" / "submissions").glob("*.json"):
        filings = json.loads(p.read_text(encoding="utf-8"))
        days = earnings_days(filings, spy.dates)
        for tk in filings.get("tickers", []):
            earn[tk] = days
    labels, year_counts = label_headlines(rows, spy.dates)
    trades, counts = build_trades(universe, spy, labels, year_counts, earn)
    result: dict[str, dict] = {}
    verdicts = {t: judge(trades.get(t, []), COST, HORIZON, TEST_YEARS) for t in TRIALS}
    flags = bh_flags(verdicts)
    placebo_labels, placebo_years = label_headlines(rows, spy.dates, PLACEBO_SHIFT_DAYS, random.Random(PLACEBO_SEED))
    placebo_trades, _ = build_trades(universe, spy, placebo_labels, placebo_years, earn)
    for t in TRIALS:
        pv = judge(placebo_trades.get(t, []), COST, HORIZON, TEST_YEARS)
        result[t] = {"verdict": verdicts[t], "bh": flags[t], "placebo": f"{pv.decision} (net {pv.mean_net:+.2%}, t {pv.t:.2f})" if pv.t is not None and pv.mean_net is not None else pv.decision}
    print(render(result))
    print("\ncounts:", dict(counts))
    print("Limits: current-constituent bars (survivorship flatters long legs); archive coverage thins for small names; headline time is the provider's;")
    print("earnings days are excluded only where the 8-K list reaches back that far (earnings_unknown_kept). FORWARD means 'worth a forward test', never real money.")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({t: {"decision": r["verdict"].decision, "events": r["verdict"].events, "mean_net": r["verdict"].mean_net, "ci": r["verdict"].ci,
                                      "t": r["verdict"].t, "years": r["verdict"].years, "bh": r["bh"], "placebo": r["placebo"], "reasons": list(r["verdict"].reasons)}
                                  for t, r in result.items()} | {"counts": dict(counts)}, indent=1), encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:  # pragma: no cover
    if argv[:1] == ["extract"]:
        return extract()
    if argv[:1] == ["report"]:
        return report()
    print(__doc__)
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main(sys.argv[1:]))
